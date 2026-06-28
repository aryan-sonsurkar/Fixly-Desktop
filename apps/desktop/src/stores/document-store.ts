import { create } from "zustand";
import type { Document, DocumentDetail } from "@/lib/document-service";

export interface DocumentState {
  documents: Document[];
  total: number;
  page: number;
  selectedDocument: DocumentDetail | null;
  isLoading: boolean;
  searchQuery: string;
  filterStatus: string | null;
  filterType: string | null;

  setDocuments: (docs: Document[], total: number, page: number) => void;
  setSelectedDocument: (doc: DocumentDetail | null) => void;
  setIsLoading: (loading: boolean) => void;
  setSearchQuery: (query: string) => void;
  setFilterStatus: (status: string | null) => void;
  setFilterType: (type: string | null) => void;
  reset: () => void;
}

const initialState = {
  documents: [],
  total: 0,
  page: 1,
  selectedDocument: null,
  isLoading: false,
  searchQuery: "",
  filterStatus: null as string | null,
  filterType: null as string | null,
};

export const useDocumentStore = create<DocumentState>((set) => ({
  ...initialState,

  setDocuments: (docs, total, page) => set({ documents: docs, total, page }),
  setSelectedDocument: (doc) => set({ selectedDocument: doc }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setFilterStatus: (status) => set({ filterStatus: status }),
  setFilterType: (type) => set({ filterType: type }),
  reset: () => set(initialState),
}));
