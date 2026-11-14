import { useId, useRef, useState } from "react";
import { displayDate, groundingStatuses, safeCitationUrl, sourceOrganization } from "../../lib/grounding";
import type { GroundingView } from "../../lib/grounding";
import "./grounding.css";

export default function GroundedAnswer({ view }: { view: Exclude<GroundingView, { kind: "legacy" }> }) {
  const prefix = useId();
  const sources = useRef(new Map<string, HTMLDetailsElement>());
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  if (view.kind === "invalid") {
    return <section className="grounded-answer grounded-warning" aria-label="Evidence metadata unavailable">
      <h4>Evidence metadata unavailable</h4>
      <p>This response cannot be displayed as a supported quotation. Reload history or ask again; no verification is claimed.</p>
    </section>;
  }
  const result = view.value;
  const [heading, explanation] = groundingStatuses[result.status];
  const openSource = (id: string) => {
    const detail = sources.current.get(id);
    if (detail) {
      detail.open = true;
      detail.querySelector("summary")?.focus();
      detail.scrollIntoView({ block: "nearest" });
    }
  };
  return <section className={"grounded-answer " + (result.abstained ? "grounded-warning" : "")} aria-labelledby={prefix + "-heading"}>
    <header><h4 id={prefix + "-heading"}>{heading}</h4><p>{explanation}</p></header>
    {!result.abstained && <>
      <h5>Quoted source passages</h5>
      <ol className="grounded-claims">
        {result.claims.map((claim, index) => <li key={claim.claim_id}>
          <blockquote><p>{claim.text}</p></blockquote>
          <div className="grounded-references" aria-label={"Sources for quotation " + (index + 1)}>
            {claim.citation_ids.map(id => {
              const number = result.evidence.findIndex(item => item.citation_id === id) + 1;
              return <button key={id} type="button" onClick={() => openSource(id)}
                aria-controls={prefix + "-" + id} aria-expanded={expanded[id] ?? false}>Source {number}</button>;
            })}
          </div>
        </li>)}
      </ol>
      <section aria-label="Source evidence and provenance">
        <h5>Evidence and provenance</h5>
        {result.evidence.map((source, index) => {
          const link = safeCitationUrl(source.canonical_url);
          const published = displayDate(source.published_at);
          const modified = displayDate(source.modified_at);
          const retrieved = displayDate(source.retrieved_at);
          return <details key={source.citation_id} id={prefix + "-" + source.citation_id}
            ref={node => { if (node) sources.current.set(source.citation_id, node); else sources.current.delete(source.citation_id); }}
            onToggle={event => {
              const open = event.currentTarget.open;
              setExpanded(prev => ({ ...prev, [source.citation_id]: open }));
            }}>
            <summary>Source {index + 1}: {source.title}</summary>
            <div className="grounded-source">
              <p>{sourceOrganization(source.source_id) ?? "Organization not provided"}</p>
              <p className="grounded-source-kind">{source.trust === "synthetic_fixture" ? "Synthetic fixture — not official guidance"
                : source.scope === "private" ? "Private source" : "Public source snapshot"}</p>
              {link ? <a href={link} target="_blank" rel="noopener noreferrer">Open canonical source <span>(new tab)</span></a>
                : <p>No safe canonical link available.</p>}
              <dl>
                <dt>Section</dt><dd>{source.section}</dd>
                <dt>Published</dt><dd>{published ? <time dateTime={source.published_at!}>{published} (UTC)</time> : "Not provided"}</dd>
                <dt>Modified</dt><dd>{modified ? <time dateTime={source.modified_at!}>{modified} (UTC)</time> : "Not provided"}</dd>
                <dt>Retrieved</dt><dd>{retrieved ? <time dateTime={source.retrieved_at}>{retrieved} (UTC)</time> : "Not provided"}</dd>
                <dt>Source version</dt><dd>{source.source_version}</dd>
                <dt>Evidence reference</dt><dd>{source.citation_id}</dd>
              </dl>
              <p className="grounded-quote-label">Retrieved passage (quoted verbatim)</p>
              <blockquote><p>{source.excerpt}</p></blockquote>
            </div>
          </details>;
        })}
      </section>
    </>}
  </section>;
}
