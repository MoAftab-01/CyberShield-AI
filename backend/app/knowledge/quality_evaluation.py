"""Batch 2 dedicated offline worker: python -B -m app.knowledge.quality_evaluation.

--local-models enables ONLY complete cached safetensors snapshots. No fetching.
No serving process imports or production indexes are reused.
"""
import argparse
from contextlib import redirect_stdout, redirect_stderr
from hashlib import sha256
import importlib.metadata
import io
import json
import os
from pathlib import Path
import random
import socket
import sys
import tempfile
import time

from .quality_dataset import (QUALITY_ROOT, SEED, corpus_catalog, load_judgments,
                              query_view, retrieval_request, source_aware_order, validate_dataset)
from .quality_metrics import audit_answer, passage_key, passage_metrics

RRF_GRID = (60, 10, 100)
MMR_GRID = (0.85, 0.65, 1.0)
SEMANTIC_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CROSS_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def local_snapshot(name):
    """Read a standard external cache; never search the original repository."""
    folder = Path.home()/".cache/huggingface/hub"/("models--"+name.replace("/", "--"))/"snapshots"
    if not folder.is_dir():
        return None
    candidates = [p for p in folder.iterdir()
                  if p.is_dir() and all((p/n).is_file() for n in ("config.json", "model.safetensors", "tokenizer.json"))]
    return sorted(candidates, key=lambda p:p.name)[-1] if candidates else None


def _stamp(path, name):
    selected = ("config.json", "model.safetensors", "tokenizer.json", "modules.json", "1_Pooling/config.json")
    checksums, size = {}, 0
    for filename in selected:
        file = path/filename
        if file.is_file():
            hasher = sha256()
            with file.open("rb") as source:
                while block := source.read(1024*1024):
                    hasher.update(block)
            checksums[filename] = hasher.hexdigest()
            size += file.stat().st_size
    return {"name":name, "revision":path.name, "files_sha256":checksums, "selected_bytes":size}


def load_local_models(enabled, scratch):
    models, metadata = {}, {}
    if not enabled:
        return models, {"status":"disabled; pass --local-models for cached weights"}
    start = time.perf_counter()
    try:
        import torch
        torch.manual_seed(SEED)
        torch.set_num_threads(2)
        torch.use_deterministic_algorithms(True)
        from sentence_transformers import SentenceTransformer, CrossEncoder
        from transformers.utils import logging
        logging.disable_progress_bar()
    except (ImportError, RuntimeError, OSError) as error:
        return models, {"status":"unavailable", "error_type":type(error).__name__}
    for key, name, constructor in (("semantic",SEMANTIC_MODEL,SentenceTransformer),("cross",CROSS_MODEL,CrossEncoder)):
        path = local_snapshot(name)
        if path is None:
            metadata[key] = {"name":name,"status":"complete local safetensors snapshot absent"}
            continue
        before = time.perf_counter()
        try:
            model = constructor(str(path), device="cpu", local_files_only=True,
                                trust_remote_code=False, token=False)
        except Exception as error:
            metadata[key] = {"name":name,"status":"load failed; no fallback or download",
                             "error_type":type(error).__name__}
            continue
        models[key] = model
        metadata[key] = {**_stamp(path,name), "status":"loaded offline",
                         "load_seconds":time.perf_counter()-before}
    metadata["import_and_load_seconds"] = time.perf_counter()-start
    return models, metadata


class Engine:
    """One embedding space at a time, with identical authorized corpus snapshots."""
    def __init__(self, catalog, semantic=None):
        self.catalog, self.semantic = catalog, semantic
        self.contexts, self.vectors = {}, {}
        self.encoding_seconds = self.index_seconds = 0.0
        self.cross_pairs = 0

    def embed(self, texts):
        import numpy as np
        from app.rag.embeddings import EmbeddingService
        values = list(texts)
        missing = list(dict.fromkeys(text for text in values if text not in self.vectors))
        if missing:
            start = time.perf_counter()
            generated = (self.semantic.encode(missing, normalize_embeddings=True, show_progress_bar=False,
                                              batch_size=32, convert_to_numpy=True)
                         if self.semantic else EmbeddingService.hash_vectors(missing))
            generated = np.asarray(generated,dtype="float32")
            if generated.ndim != 2 or generated.shape[0] != len(missing) or not np.isfinite(generated).all():
                raise ValueError("Invalid model vectors; lexical fallback is prohibited.")
            norms = np.linalg.norm(generated,axis=1,keepdims=True)
            generated = generated/np.maximum(norms,1e-12)
            self.vectors.update(zip(missing,generated))
            self.encoding_seconds += time.perf_counter()-start
        return np.asarray([self.vectors[text] for text in values],dtype="float32")

    def activate(self, question):
        from app.rag.bm25_store import BM25Store
        from app.rag.faiss_store import FAISSStore
        key = question["user_id"], question["source_as_of"]
        if key not in self.contexts:
            view = query_view(self.catalog,question)
            docs = sorted(view.documents(question["user_id"]),key=lambda d:d.metadata["chunk_id"])
            if not docs:
                raise ValueError("The reviewed benchmark requires a nonempty visible corpus.")
            vectors = self.embed([d.page_content for d in docs])
            start = time.perf_counter()
            FAISSStore.build_index(vectors,docs)
            BM25Store.build_index(docs)
            self.index_seconds += time.perf_counter()-start
            self.contexts[key] = view,docs,FAISSStore._index,BM25Store._bm25
        view,docs,index,bm25 = self.contexts[key]
        FAISSStore._index,FAISSStore._documents = index,docs
        BM25Store._bm25,BM25Store._documents = bm25,docs
        return view,docs,index,bm25

    def rank(self, question, mode, *, rrf=60, mmr=0.85, cross=None):
        from app.rag.retriever import HybridRetriever
        from app.rag.query_expander import prepare_retrieval_query
        from .evidence import collect_evidence, rerank_documents
        if set(question)!={"question","user_id","source_as_of"}:
            raise ValueError("Only query text, actor and source cutoff may enter retrieval.")
        view,docs,index,bm25 = self.activate(question)
        text, actor = question["question"],question["user_id"]
        # Equal warm-vector timing; cold encoding cost is recorded separately.
        self.embed([text,prepare_retrieval_query(text)])
        before = time.perf_counter()
        if mode == "bm25":
            from app.rag.bm25_store import BM25Store
            scores = bm25.get_scores(BM25Store.tokenize(text))
            order = sorted(range(len(docs)),key=lambda i:(-float(scores[i]),docs[i].metadata["chunk_id"]))
            found = tuple(docs[i] for i in order[:5])
        elif mode == "faiss":
            distances,indices = index.search(self.embed([text]),len(docs))
            order = sorted(zip(distances[0],indices[0]),key=lambda x:(float(x[0]),docs[int(x[1])].metadata["chunk_id"]))
            found = tuple(docs[int(i)] for _,i in order[:5])
        else:
            os.environ["RAG_FUSION"] = "on"
            os.environ["RAG_RRF_K"] = str(rrf)
            os.environ["RAG_MMR_LAMBDA"] = str(mmr)
            found,_ = HybridRetriever.search_with_metrics(text,top_k=20 if cross or mode=="source_aware" else 5,
                                                         user_id=actor,include_uploads=True)
            found = tuple(found)
            if mode == "source_aware":
                found = source_aware_order(text,found,view,actor)[:5]
            if cross and found:
                def rerank(evidence):
                    pairs = [(text,item.excerpt) for item in evidence]
                    self.cross_pairs += len(pairs)
                    scores = cross.predict(pairs,show_progress_bar=False,batch_size=16)
                    if len(scores)!=len(evidence):
                        raise ValueError("Invalid cross-encoder score count.")
                    import numpy as np
                    if not np.isfinite(scores).all():
                        raise ValueError("Nonfinite cross-encoder scores.")
                    order = sorted(range(len(evidence)),key=lambda i:(-float(scores[i]),evidence[i].chunk_id))
                    return tuple(evidence[i] for i in order[:5])
                found = rerank_documents(view,found,actor,rerank)
        elapsed = time.perf_counter()-before
        evidence = collect_evidence(view,found,actor)
        return view,found,evidence,elapsed


def _mean(metrics):
    if not metrics:
        return {}
    return {name:sum(row[name] for row in metrics)/len(metrics) for name in metrics[0]}


def select_configuration(dev_questions, dev_judgments, rank):
    """Selection accepts development data ONLY; held-out data is never evaluated."""
    if not dev_questions or any(q["split"]!="dev" for q in dev_questions):
        raise ValueError("Configuration selection accepts the development split only.")
    if set(dev_judgments)!={q["id"] for q in dev_questions}:
        raise ValueError("Configuration selection received nondevelopment labels.")
    grid = []
    for rrf in RRF_GRID:
        for mmr in MMR_GRID:
            measured = []
            for question in dev_questions:
                labels = dev_judgments[question["id"]]["relevant"]
                _,_,evidence,_ = rank(retrieval_request(question),"hybrid",rrf=rrf,mmr=mmr)
                if labels:
                    measured.append(passage_metrics([passage_key(e) for e in evidence],labels))
            grid.append({"rrf":rrf,"mmr":mmr,"dev":_mean(measured)})
    # Stable ties prefer the existing RRF/MMR defaults, listed first.
    best = max(grid,key=lambda item:(item["dev"]["ndcg_at_5"],item["dev"]["recall_at_5"],item["dev"]["mrr"]))
    no_mmr = max((row for row in grid if row["mmr"]==1.0),
                 key=lambda item:(item["dev"]["ndcg_at_5"],item["dev"]["recall_at_5"],item["dev"]["mrr"]))
    return {"hybrid":no_mmr,"hybrid_mmr":best,"selection":"development nDCG@5, then Recall@5, then MRR; stable default-first ties",
            "grid":grid,"dev_query_ids":[q["id"] for q in dev_questions]}


def score_mode(engine, questions, judgments, mode, config, cross=None):
    from .evidence import grounded_answer
    from .evaluation import _extractive_stub
    metrics, cases, latencies = [],[],[]
    totals = dict(citation_references=0,valid_references=0,claims=0,unsupported_excerpts=0,
                  incorrect_attributions=0,unjudged_claims=0,covered_passages=0,relevant_passages=0)
    must_abstain = correct_abstain = false_abstain = answerable = accepted = 0
    answerable_covered = answerable_gold = 0
    for question in questions:
        view,found,evidence,elapsed = engine.rank(retrieval_request(question),mode,cross=cross,**config)
        labels = judgments[question["id"]]["relevant"]
        metric = passage_metrics([passage_key(e) for e in evidence],labels) if labels else None
        if metric:
            metrics.append(metric)
        answer = grounded_answer(question["question"],found,view,question["user_id"],generator=_extractive_stub)
        audit = audit_answer(evidence,answer,labels)
        for name,value in audit.items():
            totals[name] += value
        expected = question["expected_abstain"]
        if not expected:
            answerable_covered += audit["covered_passages"]
            answerable_gold += audit["relevant_passages"]
        must_abstain += expected
        correct_abstain += expected and answer.abstained
        answerable += not expected
        false_abstain += not expected and answer.abstained
        accepted += not answer.abstained
        latencies.append(elapsed*1000)
        cases.append({"id":question["id"],"ranked":[list(passage_key(e)) for e in evidence],
                      "versions":[e.source_version for e in evidence],"ranking":metric,
                      "abstained":answer.abstained,"reason":answer.reason,"audit":audit})
    import numpy as np
    return {
        "retrieval":_mean(metrics),
        "abstention":{"expected":must_abstain,"correct":correct_abstain,"answerable":answerable,
                      "false_abstentions":false_abstain,"accepted":accepted,
                      "precision":correct_abstain/(correct_abstain+false_abstain) if correct_abstain+false_abstain else None,
                      "recall":correct_abstain/must_abstain if must_abstain else None,
                      "false_abstention_rate":false_abstain/answerable if answerable else None},
        "evidence":{**totals,
            "citation_validity":totals["valid_references"]/totals["citation_references"] if totals["citation_references"] else None,
            "evidence_coverage":totals["covered_passages"]/totals["relevant_passages"] if totals["relevant_passages"] else None,
            "unsupported_excerpt_rate":totals["unsupported_excerpts"]/totals["claims"] if totals["claims"] else None,
            "answerable_covered_passages":answerable_covered,"answerable_relevant_passages":answerable_gold,
            "answerable_evidence_coverage":answerable_covered/answerable_gold if answerable_gold else None,
            "semantic_unsupported_claim_rate":None},
        "timing":{"mean_warm_ranking_ms":float(np.mean(latencies)),"p95_warm_ranking_ms":float(np.percentile(latencies,95))},
        "cases":cases,
    }


def _evaluate(local_models, scratch):
    import numpy as np
    from unittest.mock import patch
    from app.rag.embeddings import EmbeddingService
    from app.rag.faiss_store import FAISSStore
    from app.rag.bm25_store import BM25Store
    random.seed(SEED)
    np.random.seed(SEED)
    assert FAISSStore.INDEX_PATH.resolve().is_relative_to(scratch)
    assert BM25Store.INDEX_PATH.resolve().is_relative_to(scratch)
    catalog = corpus_catalog()
    questions,judgments = load_judgments()
    stats = validate_dataset(catalog,questions,judgments)
    models,metadata = load_local_models(local_models,scratch)
    manifest_bytes = (QUALITY_ROOT/"manifest.json").read_bytes()
    report = {"seed":SEED,"dataset":stats,"manifest_sha256":sha256(manifest_bytes).hexdigest(),
              "models":metadata,"packages":{name:importlib.metadata.version(name) for name in
                    ("numpy","faiss-cpu","rank-bm25","pydantic")},
              "protocol":{"unit":"authorized source + record + section at explicit source snapshot",
                  "nDCG":"graded 2**relevance-1; binary Recall/Precision/MRR",
                  "k":5,"precision_denominator":5,"empty_gold":"excluded from ranking mean; scored in abstention",
                  "generator":"unchanged Batch 1 first-excerpt stub; labels never supplied",
                  "authority":"no trust/recency boost; explicit historical views only",
                  "candidate_pool_cross_encoder":20,"runtime_settings_changed":False},
              "tuning":{},"modes":{},"costs":{}}
    splits = {split:[q for q in questions if q["split"]==split] for split in ("dev","heldout")}
    for backend,model in (("hash",None),("semantic",models.get("semantic"))):
        if backend=="semantic" and model is None:
            continue
        engine = Engine(catalog,model)
        with patch.object(EmbeddingService,"embed_documents",classmethod(lambda cls,texts:engine.embed(texts))), \
             patch.object(EmbeddingService,"embed_query",classmethod(lambda cls,text:engine.embed([text]))), \
             patch.object(EmbeddingService,"backend_name",classmethod(lambda cls:backend)):
            dev_judgments = {q["id"]:judgments[q["id"]] for q in splits["dev"]}
            selected = select_configuration(splits["dev"],dev_judgments,engine.rank)
            report["tuning"][backend] = selected
            modes = {"faiss":("faiss",{},None),"hybrid":("hybrid",{"rrf":60,"mmr":1.0},None),
                     "hybrid_mmr":("hybrid",{"rrf":60,"mmr":0.85},None),
                     "tuned_hybrid":("hybrid",{k:selected["hybrid"][k] for k in ("rrf","mmr")},None),
                     "tuned_hybrid_mmr":("hybrid",{k:selected["hybrid_mmr"][k] for k in ("rrf","mmr")},None),
                     "source_aware":("source_aware",{k:selected["hybrid_mmr"][k] for k in ("rrf","mmr")},None)}
            if backend=="hash":
                modes = {"bm25":("bm25",{},None),**modes}
            if backend=="semantic" and "cross" in models:
                modes["cross_encoder"] = ("hybrid",{k:selected["hybrid_mmr"][k] for k in ("rrf","mmr")},models["cross"])
            for name,(mode,configuration,cross) in modes.items():
                report["modes"][backend+"_"+name] = {
                    "configuration":configuration,
                    **{split:score_mode(engine,items,judgments,mode,configuration,cross) for split,items in splits.items()}}
        report["costs"][backend] = {"unique_encoded_texts":len(engine.vectors),"encoding_seconds":engine.encoding_seconds,
                                   "index_build_seconds":engine.index_seconds,"contexts":len(engine.contexts),
                                   "cross_encoder_pairs":engine.cross_pairs}
    report["costs"]["temporary_index_bytes"] = sum(p.stat().st_size for p in scratch.rglob("*") if p.is_file())
    try:
        import psutil
        memory = psutil.Process().memory_info()
        report["costs"]["process_peak_rss_bytes"] = getattr(memory,"peak_wset",memory.rss)
    except ImportError:
        report["costs"]["process_peak_rss_bytes"] = None
    return report


def run_worker(*, local_models=False):
    if any(name in sys.modules for name in ("app.rag.faiss_store","app.rag.bm25_store","app.rag.embeddings")):
        raise RuntimeError("Use a fresh dedicated benchmark process.")
    sys.dont_write_bytecode = True
    previous = dict(os.environ)
    previous_tempdir = tempfile.tempdir
    guards = {"network_attempts_blocked":0,"forbidden_file_operations_blocked":0}
    state = {"active":False}
    original = QUALITY_ROOT.parents[2].parent/"CyberShield-AI"
    def audit(event,args):
        if not state["active"]:
            return
        if event in {"socket.connect","socket.getaddrinfo","socket.sendto"}:
            guards["network_attempts_blocked"] += 1
            raise RuntimeError("Offline benchmark prohibits network access.")
        if event in {"os.mkdir","os.remove","os.rmdir","os.rename"}:
            paths = args[:2] if event=="os.rename" else args[:1]
            if any(not Path(os.fsdecode(path)).resolve().is_relative_to(state["scratch"]) for path in paths):
                guards["forbidden_file_operations_blocked"] += 1
                raise RuntimeError("Benchmark filesystem mutations must remain disposable.")
        if event=="open" and isinstance(args[0],(str,bytes,os.PathLike)):
            if os.fsdecode(args[0]).casefold() == os.devnull.casefold():
                return
            path = Path(os.fsdecode(args[0])).resolve()
            writing = isinstance(args[1],str) and any(c in args[1] for c in "wax+")
            writing = writing or bool(args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
            if path.is_relative_to(original) or (writing and not path.is_relative_to(state["scratch"])):
                guards["forbidden_file_operations_blocked"] += 1
                raise RuntimeError("Benchmark storage is confined to its disposable directory.")
    sys.addaudithook(audit)
    start_wall,start_cpu = time.perf_counter(),time.process_time()
    try:
        with tempfile.TemporaryDirectory(prefix="cybershield-quality-eval-") as temporary:
            scratch = Path(temporary).resolve()
            state.update(active=True,scratch=scratch)
            tempfile.tempdir = str(scratch)
            for name in tuple(os.environ):
                if name.startswith("RAG_") or name.startswith("EMBEDDING_"):
                    os.environ.pop(name)
            os.environ.update(VECTOR_DB_DIR=str(scratch/"indexes"),EMBEDDING_BACKEND="hash",
                HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",HF_HUB_DISABLE_TELEMETRY="1",
                HF_HUB_DISABLE_PROGRESS_BARS="1",TOKENIZERS_PARALLELISM="false",
                HF_HOME=str(scratch/"hf"),HF_HUB_CACHE=str(scratch/"hf/hub"),TRANSFORMERS_CACHE=str(scratch/"transformers"),TORCH_HOME=str(scratch/"torch"),
                SENTENCE_TRANSFORMERS_HOME=str(scratch/"sentence-transformers"),
                TORCHINDUCTOR_CACHE_DIR=str(scratch/"inductor"))
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                report = _evaluate(local_models,scratch)
            state["active"] = False
    finally:
        state["active"] = False
        tempfile.tempdir = previous_tempdir
        os.environ.clear()
        os.environ.update(previous)
    report["isolation"] = guards
    report["costs"].update(wall_seconds=time.perf_counter()-start_wall,cpu_seconds=time.process_time()-start_cpu,
                           torch_cpu_threads=2 if local_models else None,
                           faiss_threads="installed library default; no OpenMP override")
    return report


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-models",action="store_true")
    options = parser.parse_args()
    print(json.dumps(run_worker(local_models=options.local_models),indent=2,sort_keys=True))
