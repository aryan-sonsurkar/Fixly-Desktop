import { useState } from "react";
import { Badge } from "@fixly/ui";

export interface Citation {
  type: "document" | "web";
  title: string;
  url?: string;
  page?: number;
  chunk?: string;
}

interface SourceCitationsProps {
  citations: Citation[];
}

export function SourceCitations({ citations }: SourceCitationsProps) {
  const [expanded, setExpanded] = useState(false);

  if (!citations || citations.length === 0) return null;

  const docCitations = citations.filter((c) => c.type === "document");
  const webCitations = citations.filter((c) => c.type === "web");

  return (
    <div className="mt-2 border-t pt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
      >
        <svg
          className="w-3 h-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
          />
        </svg>
        {citations.length} source{citations.length !== 1 ? "s" : ""}
        <svg
          className={`w-3 h-3 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {expanded && (
        <div className="mt-2 space-y-1">
          {docCitations.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                Documents
              </p>
              {docCitations.map((c, i) => (
                <div
                  key={`doc-${i}`}
                  className="flex items-center gap-1.5 text-xs text-muted-foreground"
                >
                  <Badge variant="secondary" className="text-[10px] px-1 py-0">
                    PDF
                  </Badge>
                  <span className="truncate">{c.title}</span>
                  {c.page && <span className="shrink-0">p.{c.page}</span>}
                </div>
              ))}
            </div>
          )}
          {webCitations.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                Web
              </p>
              {webCitations.map((c, i) => (
                <div
                  key={`web-${i}`}
                  className="flex items-center gap-1.5 text-xs text-muted-foreground"
                >
                  <Badge variant="outline" className="text-[10px] px-1 py-0">
                    Web
                  </Badge>
                  {c.url ? (
                    <a
                      href={c.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="truncate hover:underline text-primary"
                    >
                      {c.title}
                    </a>
                  ) : (
                    <span className="truncate">{c.title}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
