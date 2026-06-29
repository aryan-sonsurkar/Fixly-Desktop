import { useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useSearchStore } from "@/stores/search-store";
import { searchAll } from "@/lib/search-service";
import { Button, Input } from "@fixly/ui";

const categoryIcons: Record<string, string> = {
  assignment: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
  subject: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
  email: "M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75",
  document: "M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z",
  conversation: "M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z",
  note: "M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125",
};

const categoryColors: Record<string, string> = {
  assignment: "text-blue-500",
  subject: "text-purple-500",
  email: "text-green-500",
  document: "text-orange-500",
  conversation: "text-primary",
  note: "text-yellow-500",
};

const categories = [
  { value: null, label: "All" },
  { value: "assignment", label: "Assignments" },
  { value: "subject", label: "Subjects" },
  { value: "email", label: "Emails" },
  { value: "document", label: "Documents" },
  { value: "conversation", label: "Conversations" },
  { value: "note", label: "Notes" },
];

export function CommandPalette() {
  const navigate = useNavigate();
  const {
    open, query, results, selectedIndex, loading, categoryFilter, recentSearches,
    setOpen, setQuery, setResults, setSelectedIndex, setLoading,
    setCategoryFilter, addRecentSearch, clearRecentSearches, reset,
  } = useSearchStore();

  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen(!open);
      }
      if (e.key === "Escape" && open) {
        reset();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, setOpen, reset]);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const data = await searchAll(q, 10);
      setResults(data.results);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [setResults, setLoading]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(query), 200);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, doSearch]);

  const filteredResults = categoryFilter
    ? results.filter((r) => r.type === categoryFilter)
    : results;

  const handleSelect = (result: (typeof results)[0]) => {
    if (query.trim()) addRecentSearch(query.trim());
    if (result.url) navigate(result.url);
    reset();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex(Math.min(selectedIndex + 1, filteredResults.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex(Math.max(selectedIndex - 1, 0));
    } else if (e.key === "Enter" && filteredResults[selectedIndex]) {
      handleSelect(filteredResults[selectedIndex]);
    }
  };

  const showRecent = !query.trim() && recentSearches.length > 0 && !categoryFilter;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-[15vh]"
          onClick={(e) => { if (e.target === e.currentTarget) reset(); }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.15 }}
            className="w-full max-w-xl overflow-hidden rounded-xl border bg-card shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center border-b px-4">
              <svg className="h-5 w-5 shrink-0 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              <Input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search assignments, subjects, emails, documents..."
                className="border-0 bg-transparent shadow-none focus-visible:ring-0"
              />
              <kbd className="hidden shrink-0 rounded border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground sm:inline-block">
                ESC
              </kbd>
            </div>

            <div className="flex gap-1 border-b px-3 py-2">
              {categories.map((cat) => (
                <button
                  key={cat.label}
                  type="button"
                  onClick={() => setCategoryFilter(cat.value)}
                  className={`rounded-full px-2.5 py-1 text-xs transition-colors ${
                    categoryFilter === cat.value
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-accent"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            <div className="max-h-80 overflow-y-auto p-2">
              {loading && (
                <div className="flex items-center justify-center py-8">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50" style={{ animationDelay: "0ms" }} />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50" style={{ animationDelay: "150ms" }} />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              )}

              {!loading && showRecent && (
                <div>
                  <div className="flex items-center justify-between px-3 py-1.5">
                    <span className="text-xs font-medium text-muted-foreground">Recent Searches</span>
                    <Button variant="ghost" size="sm" className="h-auto text-[10px]" onClick={clearRecentSearches}>
                      Clear
                    </Button>
                  </div>
                  {recentSearches.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setQuery(s)}
                      className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {s}
                    </button>
                  ))}
                </div>
              )}

              {!loading && query.trim() && filteredResults.length === 0 && (
                <div className="flex flex-col items-center gap-2 py-8 text-center">
                  <svg className="h-10 w-10 text-muted-foreground/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                  </svg>
                  <p className="text-sm text-muted-foreground">No results found</p>
                </div>
              )}

              {!loading && filteredResults.length > 0 && (
                <div>
                  {filteredResults.map((result, index) => (
                    <motion.button
                      key={`${result.type}-${result.id}`}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: index * 0.02 }}
                      type="button"
                      onClick={() => handleSelect(result)}
                      onMouseEnter={() => setSelectedIndex(index)}
                      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                        index === selectedIndex ? "bg-accent" : "hover:bg-accent/50"
                      }`}
                    >
                      <svg className={`h-5 w-5 shrink-0 ${categoryColors[result.type] || "text-muted-foreground"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d={categoryIcons[result.type] || "M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"} />
                      </svg>
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">{result.title}</p>
                        {result.subtitle && (
                          <p className="truncate text-xs text-muted-foreground">{result.subtitle}</p>
                        )}
                      </div>
                      <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground capitalize">
                        {result.type}
                      </span>
                    </motion.button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-4 border-t px-4 py-2 text-[10px] text-muted-foreground">
              <span className="flex items-center gap-1">
                <kbd className="rounded border bg-muted px-1">↑↓</kbd> Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="rounded border bg-muted px-1">↵</kbd> Open
              </span>
              <span className="flex items-center gap-1">
                <kbd className="rounded border bg-muted px-1">Esc</kbd> Close
              </span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
