import { CodeBlock } from "@/components/ai/code-block";

interface MarkdownRendererProps {
  content: string;
}

function parseInline(text: string): (string | { bold?: string; code?: string; italic?: string })[] {
  const parts: (string | { bold?: string; code?: string; italic?: string })[] = [];
  const regex = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    if (match[1]) {
      parts.push({ code: match[1].slice(1, -1) });
    } else if (match[2]) {
      parts.push({ bold: match[2].slice(2, -2) });
    } else if (match[3]) {
      parts.push({ italic: match[3].slice(1, -1) });
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

function renderInline(parts: (string | { bold?: string; code?: string; italic?: string })[]) {
  return parts.map((part, i) => {
    if (typeof part === "string") return part;
    if ("bold" in part) return <strong key={i}>{part.bold}</strong>;
    if ("italic" in part) return <em key={i}>{part.italic}</em>;
    if ("code" in part)
      return (
        <code key={i} className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono">
          {part.code}
        </code>
      );
    return null;
  });
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const blocks = parseBlocks(content);

  return <div className="space-y-3 leading-relaxed">{blocks.map(renderBlock)}</div>;
}

interface Block {
  type: "code" | "heading" | "list" | "ordered_list" | "paragraph" | "divider" | "table";
  language?: string;
  code?: string;
  level?: number;
  text?: string;
  items?: string[];
  headers?: string[];
  rows?: string[][];
}

function parseBlocks(content: string): Block[] {
  const lines = content.split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("```")) {
      const language = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      blocks.push({ type: "code", language: language || undefined, code: codeLines.join("\n") });
      i++;
      continue;
    }

    if (line.startsWith("#")) {
      const level = line.match(/^#+/)?.[0].length || 1;
      blocks.push({ type: "heading", level, text: line.replace(/^#+\s*/, "") });
      i++;
      continue;
    }

    if (line.trim() === "---") {
      blocks.push({ type: "divider" });
      i++;
      continue;
    }

    if (line.trim().startsWith("|") && line.includes("|")) {
      const headerMatch = lines[i + 1]?.trim().match(/^[\s|:-]+$/);
      if (headerMatch) {
        const headers = line.split("|").filter(Boolean).map((h) => h.trim());
        const rows: string[][] = [];
        i += 2;
        while (i < lines.length && lines[i].trim().startsWith("|")) {
          const cells = lines[i].split("|").filter(Boolean).map((c) => c.trim());
          if (cells.length > 0) {
            rows.push(cells);
          }
          i++;
        }
        blocks.push({ type: "table", headers, rows });
        continue;
      }
    }

    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      const items: string[] = [];
      while (i < lines.length && (lines[i].trim().startsWith("- ") || lines[i].trim().startsWith("* "))) {
        items.push(lines[i].trim().replace(/^[-*]\s/, ""));
        i++;
      }
      blocks.push({ type: "list", items });
      continue;
    }

    if (line.trim().match(/^\d+\.\s/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].trim().match(/^\d+\.\s/)) {
        items.push(lines[i].trim().replace(/^\d+\.\s/, ""));
        i++;
      }
      blocks.push({ type: "ordered_list", items });
      continue;
    }

    if (line.trim() === "") {
      i++;
      continue;
    }

    const paraLines: string[] = [];
    while (i < lines.length && lines[i].trim() !== "" && !lines[i].startsWith("#")
      && !lines[i].startsWith("```") && !lines[i].startsWith("---")) {
      paraLines.push(lines[i]);
      i++;
    }
    blocks.push({ type: "paragraph", text: paraLines.join(" ") });
  }

  return blocks;
}

function renderBlock(block: Block, idx: number) {
  switch (block.type) {
    case "code":
      return <CodeBlock key={idx} code={block.code || ""} language={block.language} />;

    case "heading": {
      const level = block.level || 2;
      const sizes: Record<number, string> = {
        1: "text-xl font-bold",
        2: "text-lg font-semibold",
        3: "text-base font-semibold",
        4: "text-sm font-semibold",
      };
      const className = `${sizes[level]} mt-4 mb-2`;
      const content = renderInline(parseInline(block.text || ""));
      if (level === 1) return <h1 key={idx} className={className}>{content}</h1>;
      if (level === 2) return <h2 key={idx} className={className}>{content}</h2>;
      if (level === 3) return <h3 key={idx} className={className}>{content}</h3>;
      return <h4 key={idx} className={className}>{content}</h4>;
    }

    case "list":
      return (
        <ul key={idx} className="list-disc space-y-1 pl-6">
          {block.items?.map((item, j) => (
            <li key={j}>{renderInline(parseInline(item))}</li>
          ))}
        </ul>
      );

    case "ordered_list":
      return (
        <ol key={idx} className="list-decimal space-y-1 pl-6">
          {block.items?.map((item, j) => (
            <li key={j}>{renderInline(parseInline(item))}</li>
          ))}
        </ol>
      );

    case "table": {
      const colCount = block.headers?.length || block.rows?.[0]?.length || 0;
      return (
        <div key={idx} className="my-3 overflow-x-auto rounded-lg border">
          <table className="w-full text-left text-sm">
            {block.headers && block.headers.length > 0 && (
              <thead>
                <tr className="border-b bg-muted/50">
                  {block.headers.map((h, j) => (
                    <th key={j} className="px-4 py-2 font-medium text-muted-foreground" style={{ minWidth: colCount > 3 ? 120 : undefined }}>
                      {renderInline(parseInline(h))}
                    </th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody>
              {block.rows?.map((row, j) => (
                <tr key={j} className={j < (block.rows?.length || 0) - 1 ? "border-b" : ""}>
                  {row.map((cell, k) => (
                    <td key={k} className="px-4 py-2">{renderInline(parseInline(cell))}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    case "divider":
      return <hr key={idx} className="my-4 border-muted" />;

    case "paragraph":
    default:
      return (
        <p key={idx} className="text-sm leading-relaxed">
          {renderInline(parseInline(block.text || ""))}
        </p>
      );
  }
}
