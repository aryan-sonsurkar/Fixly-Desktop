import { cn } from "@fixly/shared-utils";

/**
 * Filename presentation helpers (display only).
 *
 * The stored/database filename is NEVER modified here — these helpers only
 * decide how a name looks in the UI. The full original name is always kept
 * in the `title` tooltip for accuracy.
 */

export interface SplitName {
  stem: string;
  ext: string;
}

/** Split "DBMS.Unit.3.Final.pdf" into stem "DBMS.Unit.3.Final" + ext ".pdf". */
export function splitExtension(name: string): SplitName {
  let rest = name;
  // Collapse a duplicated trailing extension ("report.pdf.pdf" → "report.pdf").
  // The stored identity is never touched — this is display normalization only.
  const dup = rest.match(/(\.[A-Za-z0-9]{1,12})\1$/i);
  if (dup) {
    rest = rest.slice(0, -dup[1].length);
  }
  const idx = rest.lastIndexOf(".");
  // No dot, leading dotfile (".env"), or trailing dot → treat whole as stem.
  if (idx <= 0 || idx === rest.length - 1) {
    return { stem: rest, ext: "" };
  }
  const stem = rest.slice(0, idx);
  const ext = rest.slice(idx).toLowerCase();
  // Absurdly long "extensions" are really part of the name.
  if (ext.length > 12) {
    return { stem: rest, ext: "" };
  }
  return { stem, ext };
}

/** "Aryan_Sonsurkar__Resume" → "Aryan Sonsurkar Resume". Extension untouched. */
export function prettifyStem(stem: string): string {
  return stem.replace(/_+/g, " ").replace(/\s+/g, " ").trim() || stem;
}

/** Full display string (used in tests and non-truncating contexts). */
export function formatDisplayName(name: string): string {
  const { stem, ext } = splitExtension(name);
  return `${prettifyStem(stem)}${ext}`;
}

interface DocumentFilenameProps {
  /** Exact original filename (storage identity). Shown in full via tooltip. */
  name: string;
  className?: string;
}

/**
 * Single-line filename with graceful ellipsis that ALWAYS keeps the
 * extension visible: `Very Long Assignment Name....pdf`. No wrapping,
 * no layout expansion, full original in `title`.
 */
export function DocumentFilename({ name, className }: DocumentFilenameProps) {
  const { stem, ext } = splitExtension(name);
  const display = prettifyStem(stem);
  return (
    <span title={name} className={cn("flex min-w-0 items-baseline", className)}>
      <span className="truncate text-sm font-medium">{display}</span>
      {ext && <span className="shrink-0 text-sm font-medium">{ext}</span>}
    </span>
  );
}
