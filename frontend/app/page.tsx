"use client";

import { FormEvent, useMemo, useState } from "react";

import { askQuestion, resetSession, uploadPdfs } from "@/lib/api";
import type { Citation } from "@/lib/types";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
};

export default function Home() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [indexedDocuments, setIndexedDocuments] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canAsk = useMemo(
    () => indexedDocuments.length > 0 && question.trim().length > 0 && !isAsking,
    [indexedDocuments.length, question, isAsking],
  );

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError("Please choose one or more PDF files first.");
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const response = await uploadPdfs(selectedFiles);
      setIndexedDocuments(response.indexed_documents);
      setMessages([]);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleAsk = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canAsk) {
      return;
    }

    const nextQuestion = question.trim();
    setQuestion("");
    setError(null);

    setMessages((existing) => [
      ...existing,
      {
        id: `${Date.now()}-user`,
        role: "user",
        content: nextQuestion,
      },
    ]);

    setIsAsking(true);
    try {
      const response = await askQuestion(nextQuestion);
      setMessages((existing) => [
        ...existing,
        {
          id: `${Date.now()}-assistant`,
          role: "assistant",
          content: response.answer,
          citations: response.citations,
        },
      ]);
    } catch (chatError) {
      setError(chatError instanceof Error ? chatError.message : "Could not answer that question.");
    } finally {
      setIsAsking(false);
    }
  };

  const handleReset = async () => {
    setError(null);
    try {
      await resetSession();
      setSelectedFiles([]);
      setIndexedDocuments([]);
      setMessages([]);
      setQuestion("");
    } catch (resetError) {
      setError(resetError instanceof Error ? resetError.message : "Reset failed.");
    }
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-6 px-4 py-6 sm:px-8 sm:py-10">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">PDF RAG Assistant</h1>
        <p className="text-sm text-slate-600 sm:text-base">
          Upload PDFs, then ask questions and review page-level citations.
        </p>
      </header>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <input
            type="file"
            accept="application/pdf"
            multiple
            onChange={(event) => setSelectedFiles(Array.from(event.target.files ?? []))}
            className="block w-full cursor-pointer rounded-lg border border-slate-300 p-2 text-sm file:mr-4 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-slate-700"
          />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleUpload}
              disabled={isUploading}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {isUploading ? "Indexing..." : "Upload & Index"}
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
            >
              Reset
            </button>
          </div>
        </div>

        <div className="mt-4 text-sm text-slate-700">
          {indexedDocuments.length > 0 ? (
            <>
              <p className="font-medium">Indexed documents:</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {indexedDocuments.map((name) => (
                  <li key={name}>{name}</li>
                ))}
              </ul>
            </>
          ) : (
            <p>No documents indexed yet.</p>
          )}
        </div>
      </section>

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      <section className="flex flex-1 flex-col rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
        <div className="mb-4 flex-1 space-y-4 overflow-y-auto">
          {messages.length === 0 ? (
            <p className="text-sm text-slate-500">Chat history will appear here after you ask a question.</p>
          ) : (
            messages.map((message) => (
              <article
                key={message.id}
                className={`rounded-lg p-3 text-sm ${
                  message.role === "assistant" ? "bg-slate-100" : "bg-blue-50"
                }`}
              >
                <p className="mb-2 font-semibold capitalize">{message.role}</p>
                <p className="whitespace-pre-wrap text-slate-800">{message.content}</p>
                {message.citations && message.citations.length > 0 ? (
                  <div className="mt-3 space-y-2 border-t border-slate-200 pt-2">
                    <p className="font-medium text-slate-700">Sources</p>
                    {message.citations.map((citation, index) => (
                      <div key={`${citation.document_name}-${citation.page_number}-${index}`}>
                        <p className="text-xs text-slate-600">
                          {citation.document_name} · page {citation.page_number}
                        </p>
                        {citation.excerpt ? (
                          <p className="text-xs text-slate-500">“{citation.excerpt}...”</p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : null}
              </article>
            ))
          )}
          {isAsking ? <p className="text-sm text-slate-500">Generating answer...</p> : null}
        </div>

        <form onSubmit={handleAsk} className="mt-auto flex flex-col gap-2 sm:flex-row">
          <input
            type="text"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question about your documents"
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={!canAsk}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            Ask
          </button>
        </form>
      </section>
    </main>
  );
}
