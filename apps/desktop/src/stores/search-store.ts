import { create } from "zustand";
import type { SearchResult } from "@/lib/search-service";

export interface SearchState {
  open: boolean;
  query: string;
  results: SearchResult[];
  selectedIndex: number;
  loading: boolean;
  categoryFilter: string | null;
  recentSearches: string[];
  setOpen: (open: boolean) => void;
  setQuery: (query: string) => void;
  setResults: (results: SearchResult[]) => void;
  setSelectedIndex: (index: number) => void;
  setLoading: (loading: boolean) => void;
  setCategoryFilter: (filter: string | null) => void;
  addRecentSearch: (query: string) => void;
  clearRecentSearches: () => void;
  reset: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  open: false,
  query: "",
  results: [],
  selectedIndex: 0,
  loading: false,
  categoryFilter: null,
  recentSearches: [],

  setOpen: (open) => set({ open, query: "", results: [], selectedIndex: 0, categoryFilter: null }),
  setQuery: (query) => set({ query, selectedIndex: 0 }),
  setResults: (results) => set({ results }),
  setSelectedIndex: (index) => set({ selectedIndex: index }),
  setLoading: (loading) => set({ loading }),
  setCategoryFilter: (filter) => set({ categoryFilter: filter, selectedIndex: 0 }),
  addRecentSearch: (query) =>
    set((state) => {
      const filtered = state.recentSearches.filter((s) => s !== query);
      return { recentSearches: [query, ...filtered].slice(0, 10) };
    }),
  clearRecentSearches: () => set({ recentSearches: [] }),
  reset: () =>
    set({
      open: false,
      query: "",
      results: [],
      selectedIndex: 0,
      loading: false,
      categoryFilter: null,
    }),
}));
