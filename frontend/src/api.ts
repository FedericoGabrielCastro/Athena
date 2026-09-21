import type { Category, ClassificationPreview, Stats, Ticket } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  categories: () => request<Category[]>("/api/categories/"),
  tickets: () => request<Ticket[]>("/api/tickets/"),
  stats: () => request<Stats>("/api/stats/"),
  classify: (title: string, body: string) =>
    request<ClassificationPreview>("/api/classify/", {
      method: "POST",
      body: JSON.stringify({ title, body }),
    }),
  createTicket: (title: string, body: string) =>
    request<Ticket>("/api/tickets/", {
      method: "POST",
      body: JSON.stringify({ title, body }),
    }),
  correct: (id: number, category_slug: string) =>
    request<Ticket>(`/api/tickets/${id}/correct/`, {
      method: "POST",
      body: JSON.stringify({ category_slug }),
    }),
};
