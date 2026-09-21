"""Local ticket classifier with an optional Ollama adapter."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from tickets.catalog import CATEGORY_SPECS, SPEC_BY_SLUG, CategorySpec

logger = logging.getLogger(__name__)

URGENT_TERMS = (
    "outage",
    "down",
    "breach",
    "leak",
    "cannot access",
    "blocked",
    "urgent",
    "caído",
    "caida",
    "filtración",
    "no puedo acceder",
    "bloqueada",
    "urgente",
    "producción caída",
)
HIGH_TERMS = (
    "error",
    "bug",
    "fail",
    "timeout",
    "crash",
    "broken",
    "cannot",
    "no funciona",
    "falla",
    "no carga",
    "locked",
    "bloquead",
)
LOW_TERMS = (
    "how do i",
    "how to",
    "feature",
    "would be nice",
    "question",
    "cómo",
    "duda",
    "sería útil",
    "documentación",
    "wishlist",
)


@dataclass(frozen=True)
class Classification:
    category_slug: str
    priority: str
    confidence: float
    tags: list[str]
    rationale: str
    engine: str
    scores: dict[str, float]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


class LocalTicketClassifier:
    def __init__(self, specs: tuple[CategorySpec, ...] = CATEGORY_SPECS) -> None:
        self.specs = specs
        corpus = [" ".join(spec.prototypes + spec.keywords) for spec in specs]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform(corpus)

    def classify(self, title: str, body: str) -> Classification:
        ollama = self._try_ollama(title, body)
        if ollama is not None:
            return ollama
        return self._classify_local(title, body)

    def _classify_local(self, title: str, body: str) -> Classification:
        combined = _normalize(f"{title} {title} {body}")
        vector = self.vectorizer.transform([combined])
        similarities = cosine_similarity(vector, self.matrix)[0]

        scores: dict[str, float] = {}
        keyword_hits: dict[str, list[str]] = {}
        for spec, similarity in zip(self.specs, similarities, strict=True):
            hits = [kw for kw in spec.keywords if kw in combined]
            keyword_hits[spec.slug] = hits
            boost = min(0.28, 0.07 * len(hits))
            scores[spec.slug] = float(similarity) + boost

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_slug, top_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = max(0.0, top_score - second_score)
        confidence = round(min(0.97, 0.42 + top_score * 0.35 + margin * 0.9), 3)

        spec = SPEC_BY_SLUG[top_slug]
        hits = keyword_hits[top_slug]
        tags = list(dict.fromkeys([*spec.tags, *hits[:3]]))
        priority = self._priority(combined, top_slug)
        rationale = self._rationale(spec, hits, confidence, engine="local")

        return Classification(
            category_slug=top_slug,
            priority=priority,
            confidence=confidence,
            tags=tags[:6],
            rationale=rationale,
            engine="local",
            scores={slug: round(score, 3) for slug, score in ranked},
        )

    def _try_ollama(self, title: str, body: str) -> Classification | None:
        catalog = [
            {"slug": spec.slug, "name": spec.name, "description": spec.description}
            for spec in self.specs
        ]
        payload = {
            "model": settings.OLLAMA_MODEL,
            "stream": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Classify a support ticket. Return JSON with keys: "
                        "category_slug, priority (low|medium|high|urgent), "
                        "confidence (0-1), tags (string array), rationale. "
                        f"Allowed category_slug values: {[s.slug for s in self.specs]}. "
                        f"Catalog: {json.dumps(catalog, ensure_ascii=False)}"
                    ),
                },
                {"role": "user", "content": f"Title: {title}\n\nBody: {body}"},
            ],
        }
        request = urllib.request.Request(
            f"{settings.OLLAMA_URL}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=0.6) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None

        try:
            content = json.loads(raw["message"]["content"])
            slug = content["category_slug"]
            if slug not in SPEC_BY_SLUG:
                return None
            spec = SPEC_BY_SLUG[slug]
            confidence = float(content.get("confidence", 0.8))
            priority = content.get("priority", "medium")
            if priority not in {"low", "medium", "high", "urgent"}:
                priority = "medium"
            tags = content.get("tags") or list(spec.tags)
            rationale = str(content.get("rationale") or self._rationale(spec, [], confidence, "ollama"))
        except (KeyError, TypeError, ValueError):
            logger.debug("Ollama response was not usable", exc_info=True)
            return None

        return Classification(
            category_slug=slug,
            priority=priority,
            confidence=round(min(0.99, max(0.2, confidence)), 3),
            tags=[str(tag) for tag in tags][:6],
            rationale=rationale,
            engine="ollama",
            scores={slug: 1.0},
        )

    def _priority(self, text: str, slug: str) -> str:
        if slug == "security" or any(term in text for term in URGENT_TERMS):
            return "urgent"
        if any(term in text for term in HIGH_TERMS):
            return "high"
        if slug == "feature" or any(term in text for term in LOW_TERMS):
            return "low"
        return "medium"

    def _rationale(
        self, spec: CategorySpec, hits: list[str], confidence: float, engine: str
    ) -> str:
        source = "Ollama" if engine == "ollama" else "clasificador local"
        if hits:
            shown = ", ".join(hits[:4])
            return (
                f"{source}: encaja con {spec.name} "
                f"(confianza {confidence:.0%}) por términos como {shown}."
            )
        return f"{source}: el texto se alinea con prototipos de {spec.name} ({confidence:.0%})."


classifier = LocalTicketClassifier()
