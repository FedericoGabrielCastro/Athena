import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { api } from "./api";
import type { Category, ClassificationPreview, Stats, Ticket } from "./types";

const priorityLabel: Record<Ticket["priority"], string> = {
  low: "Baja",
  medium: "Media",
  high: "Alta",
  urgent: "Urgente",
};

function formatTime(iso: string) {
  return new Intl.DateTimeFormat("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "short",
  }).format(new Date(iso));
}

export default function App() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [preview, setPreview] = useState<ClassificationPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [nextCategories, nextTickets, nextStats] = await Promise.all([
      api.categories(),
      api.tickets(),
      api.stats(),
    ]);
    setCategories(nextCategories);
    setTickets(nextTickets);
    setStats(nextStats);
    setSelectedId((current) => current ?? nextTickets[0]?.id ?? null);
  }, []);

  useEffect(() => {
    refresh().catch(() => setError("No se pudo hablar con el backend en :8000."));
  }, [refresh]);

  useEffect(() => {
    if (title.trim().length < 8 || body.trim().length < 12) {
      setPreview(null);
      return;
    }
    const handle = window.setTimeout(() => {
      api
        .classify(title, body)
        .then(setPreview)
        .catch(() => setPreview(null));
    }, 420);
    return () => window.clearTimeout(handle);
  }, [title, body]);

  const visibleTickets = useMemo(
    () => (filter === "all" ? tickets : tickets.filter((ticket) => ticket.category.slug === filter)),
    [filter, tickets],
  );
  const selected = tickets.find((ticket) => ticket.id === selectedId) ?? null;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim() || !body.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const created = await api.createTicket(title.trim(), body.trim());
      setTitle("");
      setBody("");
      setPreview(null);
      await refresh();
      setSelectedId(created.id);
    } catch {
      setError("No se pudo clasificar el ticket.");
    } finally {
      setLoading(false);
    }
  }

  async function onCorrect(slug: string) {
    if (!selected) return;
    const updated = await api.correct(selected.id, slug);
    setTickets((current) => current.map((ticket) => (ticket.id === updated.id ? updated : ticket)));
    const nextStats = await api.stats();
    setStats(nextStats);
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Clasificador local</p>
          <h1>Athena</h1>
        </div>
        <p className="lede">
          Django + React. El modelo corre en tu máquina: TF-IDF local, Ollama si está disponible.
        </p>
      </header>

      {error ? <p className="banner">{error}</p> : null}

      <main className="layout">
        <section className="panel composer">
          <h2>Nuevo ticket</h2>
          <form onSubmit={onSubmit}>
            <label>
              Título
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Ej. Cobro duplicado en la factura"
                maxLength={240}
              />
            </label>
            <label>
              Descripción
              <textarea
                value={body}
                onChange={(event) => setBody(event.target.value)}
                placeholder="Contá el problema, el impacto y lo que ya intentaron…"
                rows={8}
              />
            </label>
            <button type="submit" disabled={loading || !title.trim() || !body.trim()}>
              {loading ? "Clasificando…" : "Clasificar y guardar"}
            </button>
          </form>

          {preview ? (
            <aside className="preview">
              <div className="preview-head">
                <span className="chip" style={{ color: preview.category.color }}>
                  {preview.category.name}
                </span>
                <span className={`priority ${preview.priority}`}>
                  {priorityLabel[preview.priority]}
                </span>
              </div>
              <div className="meter">
                <span>Confianza {Math.round(preview.confidence * 100)}%</span>
                <i style={{ width: `${Math.round(preview.confidence * 100)}%` }} />
              </div>
              <p>{preview.rationale}</p>
              <ul className="tags">
                {preview.tags.map((tag) => (
                  <li key={tag}>{tag}</li>
                ))}
              </ul>
            </aside>
          ) : (
            <p className="hint">Escribí un título y una descripción para ver la clasificación en vivo.</p>
          )}
        </section>

        <section className="inbox">
          <div className="inbox-head">
            <h2>Bandeja</h2>
            <p>{stats ? `${stats.total} tickets` : "—"}</p>
          </div>
          <div className="filters">
            <button
              className={filter === "all" ? "active" : ""}
              onClick={() => setFilter("all")}
              type="button"
            >
              Todas
            </button>
            {categories.map((category) => (
              <button
                key={category.slug}
                className={filter === category.slug ? "active" : ""}
                onClick={() => setFilter(category.slug)}
                type="button"
              >
                {category.name}
              </button>
            ))}
          </div>
          {stats ? (
            <div className="bars">
              {stats.by_category.map((row) => (
                <div key={row.slug} className="bar">
                  <span>{row.name}</span>
                  <b style={{ width: `${Math.max(8, (row.count / Math.max(stats.total, 1)) * 100)}%`, background: row.color }} />
                  <em>{row.count}</em>
                </div>
              ))}
            </div>
          ) : null}
          <ul className="ticket-list">
            {visibleTickets.map((ticket) => (
              <li key={ticket.id}>
                <button
                  className={ticket.id === selected?.id ? "ticket active" : "ticket"}
                  onClick={() => setSelectedId(ticket.id)}
                  type="button"
                >
                  <span className="chip" style={{ color: ticket.category.color }}>
                    {ticket.category.name}
                  </span>
                  <strong>{ticket.title}</strong>
                  <small>
                    {priorityLabel[ticket.priority]} · {Math.round(ticket.confidence * 100)}% · {formatTime(ticket.created_at)}
                  </small>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel detail">
          {selected ? (
            <>
              <div className="preview-head">
                <span className="chip" style={{ color: selected.category.color }}>
                  {selected.category.name}
                </span>
                <span className={`priority ${selected.priority}`}>
                  {priorityLabel[selected.priority]}
                </span>
              </div>
              <h2>{selected.title}</h2>
              <p className="body">{selected.body}</p>
              <p className="rationale">{selected.rationale}</p>
              <ul className="tags">
                {selected.tags.map((tag) => (
                  <li key={tag}>{tag}</li>
                ))}
                <li>{selected.engine}</li>
                {selected.corrected ? <li>corregido</li> : null}
              </ul>
              <label className="correct">
                Corregir categoría
                <select
                  value={selected.category.slug}
                  onChange={(event) => onCorrect(event.target.value)}
                >
                  {categories.map((category) => (
                    <option key={category.slug} value={category.slug}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </label>
            </>
          ) : (
            <p className="hint">La bandeja está vacía. Clasificá el primer ticket.</p>
          )}
        </section>
      </main>
    </div>
  );
}
