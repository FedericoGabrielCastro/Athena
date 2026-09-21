<p align="center">
  <img src="docs/banner.png" alt="Athena — Local AI Ticket Classifier" width="920"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-111?style=flat-square&logo=python&logoColor=d4a853&labelColor=10140f&color=d4a853" alt="Python"/>
  <img src="https://img.shields.io/badge/Django-5-111?style=flat-square&logo=django&logoColor=6b8f71&labelColor=10140f&color=6b8f71" alt="Django"/>
  <img src="https://img.shields.io/badge/React-19-111?style=flat-square&logo=react&logoColor=5b7fa6&labelColor=10140f&color=5b7fa6" alt="React"/>
  <img src="https://img.shields.io/badge/Vite-pnpm-111?style=flat-square&logo=vite&logoColor=d4a853&labelColor=10140f&color=c45c4a" alt="Vite"/>
  <img src="https://img.shields.io/badge/AI-100%25%20local-111?style=flat-square&labelColor=10140f&color=8b5e83" alt="Local AI"/>
</p>

<p align="center">
  <strong>Clasificá tickets de soporte en tu máquina.</strong><br/>
  Sin nube. Sin API keys. Sin GPU.
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#cómo-clasifica">Cómo clasifica</a> ·
  <a href="#api">API</a>
</p>

---

<p align="center">
  <img src="docs/screenshot.png" alt="Interfaz de Athena con bandeja, composer y detalle del ticket" width="920"/>
</p>

Pegá un título y una descripción: Athena etiqueta **categoría**, **prioridad**, **tags** y **confianza**. Si se equivoca, lo corregís a mano.

## Arquitectura

<p align="center">
  <img src="docs/architecture.svg" alt="React habla con Django por /api; Django clasifica con TF-IDF local u Ollama" width="920"/>
</p>

```mermaid
flowchart LR
  U[Operador] --> UI[React + Vite]
  UI -->|POST /api/tickets/| API[Django REST]
  API --> C{Ollama en :11434?}
  C -->|sí| LLM[LLM local]
  C -->|no / error| TF[TF-IDF + keywords]
  LLM --> T[(SQLite)]
  TF --> T
  T --> UI
```

## Cómo clasifica

<p align="center">
  <img src="docs/pipeline.svg" alt="Pipeline: texto, TF-IDF, similitud, prioridad, ticket" width="920"/>
</p>

1. El **título se cuenta dos veces** junto al cuerpo, para que el asunto pese más.
2. **TF-IDF** (n-gramas 1–2) mide similitud coseno contra prototipos en español e inglés.
3. Los **keywords** de cada categoría suman un boost y se convierten en tags.
4. La **prioridad** sale del lenguaje de urgencia (`outage`, `caído`, `breach`, `2FA`…).
5. La **confianza** es el margen entre el 1.º y el 2.º puesto.

Si Ollama está en `localhost:11434`, Athena lo intenta primero y cae al modelo local ante cualquier fallo.

### Puntajes de un ticket real

> *“Nos cobraron dos veces el plan”* → **Facturación · 97%**

<p align="center">
  <img src="docs/scores.svg" alt="Barras de puntaje: Facturación 0.664, el resto por debajo de 0.07" width="920"/>
</p>

## Categorías

<p align="center">
  <img src="docs/categories.svg" alt="Seis categorías: Facturación, Incidente técnico, Solicitud de función, Acceso a cuenta, Seguridad, Consulta general" width="920"/>
</p>

| Categoría | Qué entra |
| --- | --- |
| **Facturación** | cobros, facturas, reembolsos, planes |
| **Incidente técnico** | errores, caídas, bugs, timeouts |
| **Solicitud de función** | mejoras, roadmap, “sería útil” |
| **Acceso a cuenta** | login, 2FA, permisos, reset |
| **Seguridad** | accesos no autorizados, fugas, phishing |
| **Consulta general** | docs, onboarding, “cómo hago” |

## Quick start

```bash
make install
make migrate
make seed
```

Dos procesos:

```bash
make backend    # http://127.0.0.1:8000
make frontend   # http://127.0.0.1:5173
```

Abrí **http://127.0.0.1:5173**. Vite proxea `/api` a Django.

```mermaid
sequenceDiagram
  participant UI as React
  participant API as Django
  participant ML as Classifier
  UI->>API: POST /api/classify/
  API->>ML: title + body
  ML-->>API: category, priority, confidence
  API-->>UI: preview en vivo
  UI->>API: POST /api/tickets/
  API-->>UI: ticket persistido
```

## API

| Método | Path | Para qué |
| --- | --- | --- |
| `GET` | `/api/categories/` | catálogo |
| `GET` | `/api/tickets/` | bandeja |
| `POST` | `/api/tickets/` | crear + clasificar |
| `POST` | `/api/classify/` | preview sin guardar |
| `POST` | `/api/tickets/:id/correct/` | override humano |
| `GET` | `/api/stats/` | totales de la bandeja |

---

<p align="center">
  <sub>Hecho para correr 100% local · Django + Poetry · React + pnpm Vite</sub>
</p>
