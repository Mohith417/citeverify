# CiteVerify

**Scientific claim & citation verification.** Upload an academic PDF. CiteVerify extracts the
claims that need evidence, maps in-text citations to the reference list, locates the original
publications, retrieves legal open-access full text and checks whether that research actually
supports each statement.

A citation existing is not the same as a citation proving the claim. Every verdict ships with the
source passage, a confidence indicator, the publication trace and a human-review flag.


## Live Demo

- **App:** https://citeverify-puce.vercel.app
- **API health check:** https://citeverify-8916.onrender.com/api/health
- **Source:** https://github.com/Mohith417/citeverify

> Hosted entirely on free tiers (Vercel for the frontend, Render for the backend). The free backend sleeps when idle, so the first request can take 30-60 seconds to wake up. Uploaded documents and history are not kept after the backend restarts.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, React Router, Axios, Lucide |
| Backend | Python 3, FastAPI, SQLAlchemy, SQLite, Pydantic |
| AI | Gemini (Google AI Studio) **or** any OpenAI-compatible free endpoint (Groq/Ollama) |
| Documents | pypdf, optional GROBID (Docker), lxml |
| Research | Crossref, OpenAlex, Europe PMC, Semantic Scholar, Unpaywall, arXiv |
| Retrieval | section-aware paragraph splitting; sentence-transformers + FAISS when installed, deterministic lexical ranking otherwise |
| Report | ReportLab PDF |

All services used are free of charge; no paid API or paywall access is required or performed.

---

## Run it locally

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in the AI provider + a contact email
uvicorn app.main:app --reload --port 8000
```

Check `http://127.0.0.1:8000/api/health` — `ai_configured` must be `true` for claim comparison.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev          # http://127.0.0.1:5173
```

Vite proxies `/api` to `http://127.0.0.1:8000`, so no CORS setup is needed for local development.

### 3. GROBID (optional)

```bash
docker compose up -d grobid
```

GROBID improves scientific structure extraction. When it is unavailable the regex-based citation
and reference parser is used instead — the pipeline never blocks on it.

---

## Configuration (`backend/.env`)

| Variable | Purpose |
|---|---|
| `AI_PROVIDER` | `gemini`, `groq`, `openai_compat`, `ollama` or `auto` |
| `AI_MODEL` / `AI_BASE_URL` / `AI_API_KEY` | OpenAI-compatible provider (e.g. Groq: `openai/gpt-oss-120b`, `https://api.groq.com/openai/v1`) |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Google AI Studio key (starts with `AIza`) and model name |
| `OLLAMA_URL` / `OLLAMA_MODEL` | Local model fallback |
| `CONTACT_EMAIL` | Polite-pool identification for Crossref/OpenAlex (recommended) |
| `UNPAYWALL_EMAIL` | Enables the Unpaywall open-access lookup |
| `SEMANTIC_SCHOLAR_API_KEY` | Optional; raises the Semantic Scholar rate limit |
| `OPENALEX_API_KEY` | Optional; avoids anonymous search throttling |
| `MAX_UPLOAD_MB`, `MAX_CLAIMS`, `MAX_VERIFY_CLAIMS` | Pipeline limits |
| `CORS_ORIGINS` | Comma-separated browser origins allowed to call the API; add the deployed frontend URL |

Keys stay server-side; the browser only talks to the FastAPI app.

---

## Deploy

Two pieces: the FastAPI app (a Python process, needs a real container/instance) and the Vite build
(static files). The frontend talks to the API directly, so the API must allow the frontend's origin
via `CORS_ORIGINS`.

### Backend — Render / Fly.io / Railway (or any Docker host)

Settings that matter:

| Setting | Value |
|---|---|
| Root directory | `backend` |
| Build command | `pip install -r requirements-deploy.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Disk | mount at `/opt/render/project/src/backend/storage` (SQLite + uploads survive restarts) |

`requirements-deploy.txt` is `requirements.txt` without `sentence-transformers`/`faiss-cpu`. Those
pull PyTorch (~800 MB) and exceed a free instance's memory during install; both imports are lazy, so
the pipeline falls back to lexical paragraph ranking and verdicts are unaffected.

Environment variables: `GEMINI_API_KEY` (or `AI_PROVIDER=groq`, `AI_BASE_URL`,
`AI_API_KEY`, `AI_MODEL`), `CONTACT_EMAIL`, `UNPAYWALL_EMAIL`, `CORS_ORIGINS=https://<your-frontend>`.
Skip `GROBID_URL` — GROBID is optional and the parser degrades to regex extraction.

Verify `https://<backend>/api/health` returns `ai_configured: true`.

### Frontend — Vercel / Netlify / Cloudflare Pages

| Setting | Value |
|---|---|
| Root directory | `frontend` |
| Build command | `npm run build` |
| Output directory | `dist` |
| Env var | `VITE_API_URL=https://<backend>` (build-time; no trailing slash) |

`VITE_API_URL` is baked into the bundle at build time, so set it before the first build and rebuild
after changing it. Client-side routes (`/dashboard`, `/library`, …) need an SPA fallback to
`index.html`; Vercel's Vite preset does this automatically, on Netlify add
`/* /index.html 200` to `netlify.toml`.

### Single box instead

Both services fit on one small VPS: build `frontend/dist`, serve it with nginx and proxy `/api` to
uvicorn on `127.0.0.1:8000` — the same shape as the Vite dev proxy, so no CORS entry is needed.

---

## Pipeline

1. **Upload** — PDF validated (type, size, header), text extracted page by page with pypdf, scanned
   files detected and refused instead of pretending text was read.
2. **Extract** — LLM returns claims verbatim; citations (`[1]`, `[2,3]`, `[1–4]`, author–year) and
   the bibliography are parsed, and claims are linked to reference rows. Ambiguity is preserved.
3. **Retrieve** — DOI → exact title → title + author/year matching across Crossref, OpenAlex,
   Europe PMC, Semantic Scholar and arXiv. A similar title is never accepted silently.
4. **Evidence** — open-access PDFs (OpenAlex/Unpaywall) and Europe PMC JATS XML are fetched behind
   an SSRF guard; abstracts are used only when flagged `abstract_only`.
5. **Compare** — section-aware paragraphs are ranked against the claim and the best passages go to
   the verifier. Every returned quotation is checked against the retrieved source text.
6. **Report** — verdict, explanation, facts, limitations, confidence, review flag, plus a
   downloadable ReportLab PDF.

### Verdicts

`supported` · `partially_supported` · `unsupported` · `contradictory` ·
`potentially_outdated` · `insufficient_evidence`

“Unsupported” means the accessible evidence did not establish the statement — not that it is false.
Every non-supported verdict is marked for human review and can be confirmed, overridden or annotated.

---

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | service + AI + provider status |
| GET | `/api/documents` | recent documents |
| POST | `/api/documents/upload` | multipart PDF upload |
| POST | `/api/documents/{id}/analyze` | start background analysis (idempotent while running) |
| GET | `/api/documents/{id}/status` | real processing stage |
| GET | `/api/documents/{id}/results` | dashboard payload with computed summary |
| DELETE | `/api/documents/{id}` | remove document + results |
| GET | `/api/claims/{claim_id}` | claim, references, evidence, verification |
| POST | `/api/claims/{claim_id}/review` | confirm / override / note |
| GET | `/api/references/{reference_id}` | reference + matched publication |
| POST | `/api/documents/{id}/extract-citations` | citation-only inspection (debug/tests) |
| GET | `/api/documents/{id}/report` | generated PDF report |

See `docs/API_CONTRACT.md` for schemas and rules.

---

## Repository hygiene

Runtime artefacts never enter version control: uploads, caches, generated reports, the SQLite
file, logs, screenshots and local provider backups are git-ignored, while `storage/.gitkeep` keeps
the required folders present. Secrets live only in `backend/.env` (untracked); `backend/.env.example`
documents every variable with empty values.

## Tests

```bash
cd backend && pytest -q        # 32 tests: parsing, discovery, upload, endpoints, quote guard, SSRF
cd frontend && npm run build   # type-check + production build
```

## Project layout

```
backend/
  app/          FastAPI application (api, services, models, schemas, config)
  tests/        pytest suite
  storage/      runtime uploads, cache and generated reports (git-ignored)
frontend/
  src/          React application
    pages/      landing, upload, analysis, dashboard, claim detail, references, report, library, method
    components/ layout + UI primitives
    lib/        api client, types, formatting
  public/       static assets (logo)
docs/           API contract
docker-compose.yml   optional GROBID service
```

Inside `backend/app/`:

```
backend/app/
  api/          upload, analysis, claims, references, reports
  services/     pdf_parser, citation_extractor, citation_pipeline, paper_search,
                discovery_pipeline, research_provider + semantic_scholar/unpaywall/arxiv,
                fulltext_retriever, evidence_retrieval, claim_extractor, ai_verifier, llm,
                misleading_reference_detector, grobid_service, report_generator
  models/       documents, claims, references, evidence, verifications, review events
  schemas/      Pydantic contracts
```

## Limitations (honest list)

- Only text-based PDFs are processed; OCR is not included and is reported as required.
- Reference parsing is heuristic; unusual citation styles may be marked incomplete or ambiguous.
- Full-text retrieval depends on legal open access. When only an abstract is available the verdict
  is labelled abstract-only; when nothing is available the claim is `insufficient_evidence`.
- Free AI tiers enforce rate limits; requests are retried with backoff, but a run can still leave
  some claims marked for review.
- Search APIs (notably OpenAlex anonymous search) are throttled unpredictably; every provider
  degrades gracefully and matching continues with the others.
- Automated verdicts are indications for a human reviewer, not final academic judgments.
