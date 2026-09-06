# Sonics — Instagram Policy & Evidence Analyzer

A read-only, AI-powered analyzer for **publicly accessible Instagram information**,
with an **isolated, hypothetical enforcement-prediction simulator**.

- It analyzes legitimately accessible Instagram information.
- It uses AI to assess content against a fixed set of policy categories.
- It includes a purely hypothetical enforcement-prediction simulator.
- It does **NOT** submit reports, ban accounts, or manipulate Instagram's
  enforcement system in any way.

---

## Features

| Feature | Description |
|---|---|
| Public-profile analysis | Username, display name, bio, follower/following counts, post count, account status |
| Public-content analysis | Captions and metadata of the most recent publicly accessible posts |
| Private-account limited analysis | Only information legitimately visible without authorization |
| Policy-category analysis | Fixed taxonomy: Spam, Harassment / Bullying, Hate Speech, Impersonation Risk, Sexually Explicit Material. Unknown signals are safely bucketed instead of guessed. |
| Evidence-based reasoning | Each category assessment references actual retrieved content (quote, source, reference) wherever possible |
| Evidence verification | Each piece of evidence is marked mechanically verified (verbatim match in the source) or LLM-judged, with a strength and relevance score |
| Confidence & severity | Per-category model confidence and severity |
| Uncertainties & notes | Explicitly reported limitations of the analysis |
| Deterministic fallback engine | If the local LLM is unavailable, the app still works in degraded mode using a rules-based engine |
| Hypothetical simulation tool | Standalone, isolated model estimate; never sent to Instagram |
| Local AI default | Ollama — no API key required, runs on your machine (8 GB RAM friendly) |
| FastAPI backend | Stateless REST API |
| React dashboard | Served by the backend itself; single `sonics` command to run everything |
| pip-installable package | `pip install .` starts the whole app |
| CLI with startup checks | Banner, port-in-use detection, Ollama health/model warning, browser auto-open |
| No OpenAI | OpenAI is **not** used anywhere |

---

## Read-Only Design

The application does **not**:

- Submit Instagram reports
- Automatically report accounts
- Ban accounts
- Control multiple Instagram accounts
- Bypass authentication, CAPTCHAs, or rate limits
- Access private posts without authorization
- Manipulate Instagram enforcement

The enforcement simulator is **purely hypothetical**. Report counts and
reporting-source counts exist solely as simulation variables — they are never
sent to Instagram. Simulator schemas are fully isolated from the analysis
schemas.

---

## Requirements

| Requirement | Detail |
|---|---|
| Python | 3.9 or newer |
| Node.js | 18 or newer (only needed to rebuild the frontend) |
| Internet connection | Required for permitted Instagram data retrieval |
| Ollama | Local LLM server — runs on a normal consumer PC; 8 GB RAM is sufficient with the default model |
---

## AI Configuration

The application uses a local-LLM provider with a deterministic fallback.

### Default: Ollama (local, no API key)

1. Install [Ollama](https://ollama.com/download) and leave it running.
2. Pull the default model once:

   ```bash
   ollama pull llama3.2:3b
   ```

   `llama3.2:3b` is intentionally lightweight so the app runs comfortably on a
   typical **8 GB RAM** machine. On machines with 16 GB+ RAM you can switch to a
   larger model (e.g. `llama3.1:8b`).

3. Start the app (see **Run** below). No `.env` file is required.

### Fallback: deterministic rules engine

If `AI_PROVIDER=ollama` is set but the Ollama server is unreachable (or the
model fails), the pipeline automatically degrades to a local rules-based
engine. The response clearly reports `analysis_status: "degraded"`,
`provider: "fallback-rules"`, and adds explanatory notes — the app never crashes
and never silently switches to a different model.

### Configuration reference

| Variable | Default | Purpose |
|---|---|---|
| `AI_PROVIDER` | `ollama` | `ollama`, or `local` to force the rules engine |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama HTTP server address |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model name |
| `OLLAMA_TIMEOUT` | `120` | Seconds to wait for an Ollama response |
| `HOST` | `127.0.0.1` | Server bind address |
| `PORT` | `8000` | Server port |
| `SONICS_NO_BROWSER` | `0` | `1` disables auto-opening the dashboard |

Copy `backend/.env.example` to `backend/.env` (or the project root `.env`) to
customize these values.
---

## Run

Start the application with the installed CLI command:

```bash
sonics
```

The CLI prints a startup banner with:

- The dashboard URL
- The active AI provider and model
- Any warnings (Ollama unreachable, model not installed, port in use)
- It auto-opens the dashboard in your browser (disable with `SONICS_NO_BROWSER=1`)

> If the configured port is already in use the CLI exits immediately with a
> clear message instead of crashing mid-startup.

If you are developing the frontend, you can also start a Vite dev server from
the `frontend/` directory (one-time `npm install`):

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to the backend at
`http://localhost:8000`.

---

## First Use

1. **Start the application** — run `sonics`.
2. **Open the dashboard** in your browser.
3. **Enter an account** — type `@username` or the supported Instagram profile URL.
4. **Click "Analyze Account"**.
5. **Wait** for the profile/content analysis to complete.
6. **Review the results** — Account Overview, Analysis Status, Policy Categories
   (ranked, with evidence, verification, confidence, severity), Overall
   Observations, and Uncertainties.
7. **Open the "Enforcement Prediction Simulator"** at the bottom of the results.
8. **Enter hypothetical simulation values** (violation / spam / impersonation
   report counts and source count).
9. **Click "Run Simulation"**.
10. **Review the model estimate**, confidence, uncertainty, and factors considered.

> **Note:** Ollama does **not** pull models automatically when accessed via the
> API. If the model is not yet installed, run `ollama pull <model>` once before
> using the app. The CLI banner will warn you if the model is missing.

---

## Analyzing Another Account

Once the application is installed, simply enter another username. No additional
installation is needed:

```text
@account_one  →  Analyze  →  Result
@account_two  →  Analyze  →  Result
```

The same installed application processes each new input. User input is data —
it never triggers installation, source-code changes, or AI-agent code changes.

---

## Public vs Private Accounts

### Public account

The application analyzes all legitimately accessible profile information and
public content — profile fields, posts, captions, and publicly accessible
metadata.

### Private account

The application **never attempts to bypass privacy controls**. It only analyzes
information legitimately visible without authorization — for example, username,
display name, bio, and public profile metadata — and displays a notice:

> "Limited analysis: this account is private or has limited publicly accessible
> information."

Private posts and private content are never accessed.
---

## Understanding Results

| Term | Meaning |
|---|---|
| **Policy category** | The model's fixed taxonomy label (Spam, Harassment / Bullying, Hate Speech, Impersonation Risk, Sexually Explicit Material) |
| **Severity** | Assessed potential impact of an identified signal (low / medium / high) |
| **Confidence** | How confident the model is in its own category assessment. It does **NOT** mean the probability that Instagram will act. |
| **Verification** | Whether each evidence piece is a mechanically verified quote (verbatim match in source) or an LLM-judged inference |
| **Evidence strength / relevance** | Per-evidence object scores derived from the reasoning layer |
| **Analysis status** | `completed`, `limited`, `degraded` (fallback-rules), or `unavailable` — tells you what happened during the LLM step |
| **Estimated enforcement likelihood** | A hypothetical model estimate produced by the simulator. It is **NOT** Instagram's official enforcement probability. |

**"Confidence"** means how confident the model is in its own classification. It
does **not** mean the probability that Instagram will ban the account.

**"Estimated enforcement likelihood"** is a hypothetical application-model
output. It is not Instagram's official enforcement probability.

---

## API Reference

All endpoints accept and return JSON. Full schemas are defined in
`backend/app/models/schemas.py` (analysis) and
`backend/app/models/policies.py` (analysis taxonomy and output policy data).

### `POST /api/analyze`

Request body:

| Field | Type | Required |
|---|---|---|
| `username` | string | yes |

Response body (key fields):

```json
{
  "profile": {
    "username": "example",
    "display_name": "...",
    "bio": "...",
    "is_private": false,
    "follower_count": 123,
    "following_count": 45,
    "post_count": 10,
    "recent_posts": [ ... ],
    "access_status": "Public"
  },
  "access_status": "full",
  "analysis": {
    "analysis_status": "completed",
    "provider": "ollama",
    "policy_categories": [
      {
        "rank": 1,
        "category": "Spam",
        "severity": "Medium",
        "confidence": 40,
        "reasoning": "...",
        "verification": "string",
        "evidence": [ ... ],
        "context": null
      }
    ],
    "overall_observations": [ ... ],
    "uncertainties": [ ... ],
    "notes": [ ... ]
  }
}
```

> Analysis results never include an `enforcement_simulation` object.
> The simulator is fully isolated.

### `POST /api/simulate`

Request body (the frontend derives the `risk` object locally from the analysis):

| Field | Type | Required |
|---|---|---|
| `risk` | object | yes (see `EnforcementRisk` schema) |
| `inputs` | object | yes (violation_reports, spam_reports, impersonation_reports, reporting_sources) |

Response body:

```json
{
  "estimated_likelihood": 22,
  "confidence": 60,
  "uncertainty": 22,
  "factors": [ ... ],
  "scenario_description": "..."
}
```

### `GET /api/healthz`

Returns `{"status": "ok"}`.
---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Frontend build not found" | Run `cd frontend && npm install && npm run build`, then copy `frontend/dist/*` into `backend/app/static/` (or re-install with `pip install .`) |
| "Port already in use" | Another Sonics instance or program is using the port. Set `PORT=8001` in your `.env` and retry |
| Local model unavailable | Install the model once with `ollama pull llama3.2:3b`. The CLI banner warns if the configured model is missing |
| Result says `analysis_status: "degraded"` | Ollama was unavailable for this request. Start the Ollama app and re-run |
| Result says `analysis_status: "unavailable"` | The LLM step failed (connection, timeout, or malformed JSON). Check Ollama is running and the model is installed |
| Instagram rate-limit / 429 errors | Wait and re-run later |

---

## Project Structure

```
.
├── backend/                     # Python FastAPI backend + tests
│   ├── app/
│   │   ├── main.py              # FastAPI application + `sonics` CLI
│   │   ├── agents/
│   │   │   ├── pipeline.py      # Orchestrator: Instagram → agents → judge → output
│   │   │   ├── analyzer.py      # Rule-based fallback + LLM orchestrator
│   │   │   ├── content_analyst.py
│   │   │   ├── context_analyst.py
│   │   │   ├── evidence_verifier.py
│   │   │   ├── judge.py         # Final arbitrator → AnalysisOutput
│   │   │   ├── policy_analyst.py
│   │   │   └── providers/
│   │   │       ├── ollama.py    # Ollama HTTP provider (local, no API key)
│   │   │       └── provider.py
│   │   ├── api/routes.py
│   │   ├── instagram/client.py
│   │   ├── models/
│   │   │   ├── schemas.py       # Core domain schemas (Profile, AnalysisOutput)
│   │   │   └── policies.py      # Static taxonomy + confidence/severity mapping
│   │   ├── simulation/
│   │   │   ├── simulator.py     # Deterministic math-only enforcement likelihood model
│   │   │   └── schemas.py       # EnforcementRisk, SimulationResult (isolated)
│   │   └── static/              # Pre-built React dashboard (from frontend/dist)
│   ├── tests/                   # test_api, test_pipeline, test_simulation, ...
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # React + Vite dashboard
│   └── src/App.jsx
├── pyproject.toml
└── README.md
```

---

## Development

### Running the test suite

```bash
cd backend
python -m pytest -q
```

### Rebuilding the frontend

```bash
cd frontend
npm install
npm run build
# Output lands in frontend/dist/ — copy it into backend/app/static/
```

---

## Disclaimer

> **Instagram is a trademark of Meta Platforms, Inc.**
> This application is not affiliated with, endorsed by, or connected to Meta
> Platforms, Inc. or Instagram.
>
> This application provides **read-only analysis of publicly accessible
> information**. It does **not** submit Instagram reports, ban accounts, or
> predict Instagram's enforcement decisions. The enforcement-prediction
> simulator produces **hypothetical model estimates** for educational and
> research purposes only — they are **not** official Instagram enforcement
> probabilities.
>
> Users are responsible for ensuring that any use of this application complies
> with Instagram's Terms of Service and applicable laws.