from pathlib import Path
import os,sys,tempfile,socket,inspect,json,sqlite3
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
_arguments = sys.argv[1:] or ["full-offline", "."]
root = Path(__file__).resolve().parents[2]
sys.argv = [__file__, str(root), *_arguments]
artifacts = Path(tempfile.mkdtemp(prefix="cybershield-isolated-results-"))
scratch=Path(tempfile.mkdtemp(prefix="cybershield-batch2-pytest-"))/"run"
outbound=[]
original_connect=socket.socket.connect
def guarded_connect(sock,address):
    if (isinstance(address,tuple) and address[0] in {"127.0.0.1","::1"} and
        any(frame.function in {"socketpair","_fallback_socketpair"} and
            Path(frame.filename).resolve()==Path(socket.__file__).resolve()
            for frame in inspect.stack(context=0))):
        return original_connect(sock,address)
    outbound.append("socket")
    raise AssertionError("Outbound connections forbidden in isolated tests")
socket.socket.connect=guarded_connect
socket.socket.connect_ex=guarded_connect
def deny_dns(*args,**kwargs):
    outbound.append("dns")
    raise AssertionError("DNS/network resolution forbidden in isolated tests")
socket.getaddrinfo=deny_dns
import psycopg2
def deny_postgres(*args,**kwargs):
    outbound.append("postgres")
    raise AssertionError("PostgreSQL connections forbidden in isolated tests")
psycopg2.connect=deny_postgres
original_sqlite=sqlite3.connect
def isolated_sqlite(database,*args,**kwargs):
    allowed=Path(os.environ["VECTOR_DB_DIR"]).resolve().parent
    assert allowed.is_dir() and not allowed.is_relative_to(root)
    assert str(database)==":memory:" or Path(database).resolve().is_relative_to(allowed)
    return original_sqlite(database,*args,**kwargs)
sqlite3.connect=isolated_sqlite
sqlite3.dbapi2.connect=isolated_sqlite
import pytest
class Guard:
    @pytest.fixture(autouse=True)
    def record_synthetic_http(self, request, monkeypatch):
        if sys.argv[2] != "integration-recorded" or request.node.path.name != "test_grounded_chat_integration.py":
            return
        from fastapi.testclient import TestClient
        import time
        original = TestClient.post
        def capture(client, *args, **kwargs):
            start = time.perf_counter()
            response = original(client, *args, **kwargs)
            elapsed = time.perf_counter()-start
            if response.status_code != 200:
                return response
            body = response.json()
            ground = body.get("grounding")
            if not ground or ground["status"] != "supported_quotes":
                return response
            evidence = {item["citation_id"]:item for item in ground["evidence"]}
            links = [(claim["text"],cid) for claim in ground["claims"] for cid in claim["citation_ids"]]
            assert all(cid in evidence and text==evidence[cid]["excerpt"] for text,cid in links)
            report_path = artifacts/"integration-citations.json"
            report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {"supported_http_responses":0,"citation_links":0,"exact_supported_links":0,"wall_seconds":[]}
            report["supported_http_responses"] += 1
            report["citation_links"] += len(links)
            report["exact_supported_links"] += len(links)
            report["wall_seconds"].append(elapsed)
            report_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
            if request.node.name == "test_enabled_end_to_end_exact_citations_and_existing_fields":
                # Headers/tokens are deliberately never captured.
                (artifacts/"synthetic-http-example.json").write_text(json.dumps({
                    "request":{"method":"POST","path":"/api/copilot/ask","body":kwargs["json"]},
                    "response":body},indent=2),encoding="utf-8")
            return response
        monkeypatch.setattr(TestClient,"post",capture)
    @pytest.fixture(autouse=True)
    def offline_provider(self,request):
        is_gate=sys.argv[2]=="part-a-gate-offline"
        legacy_unit=sys.argv[2]=="full-offline" and request.node.path.name in {
            "test_orchestrator.py","test_rag_service.py","test_agent_upgrades.py"}
        if is_gate or (legacy_unit and "failing_llm" not in request.fixturenames):
            request.getfixturevalue("stub_llm")
    def pytest_sessionstart(self,session):
        from app.core.config import settings
        from sqlalchemy.engine import make_url
        url=make_url(settings.DATABASE_URL)
        assert settings.ENVIRONMENT=="test" and url.get_backend_name()=="sqlite"
        assert Path(url.database).resolve().parent==Path(os.environ["VECTOR_DB_DIR"]).resolve().parent
        assert not Path(url.database).resolve().is_relative_to(root)
        assert os.environ["EMBEDDING_BACKEND"]=="hash"
    def pytest_sessionfinish(self,session,exitstatus):
        if outbound:
            session.exitstatus=pytest.ExitCode.TESTS_FAILED
        print("ISOLATION_RESULT "+json.dumps({"outbound_attempts_blocked":len(outbound),
           "postgres_attempts_blocked":outbound.count("postgres"),"test_storage_outside_repository":True}))
mode=sys.argv[2]
paths=[str(root/"backend/tests"/name) for name in sys.argv[3:]]
args=["-p","no:cacheprovider",*paths,"--basetemp",str(scratch),"--junitxml",str(artifacts/(mode+".xml")),
      "-q","--tb=short","-ra","--disable-warnings"]
raise SystemExit(pytest.main(args,plugins=[Guard()]))

