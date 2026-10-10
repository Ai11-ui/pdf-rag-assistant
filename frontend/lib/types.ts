export type Citation = {
  document_name: string;
  page_number: number;
  excerpt?: string | null;
};

export type UploadResponse = {
  message: string;
  indexed_documents: string[];
  chunk_count: number;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
};
