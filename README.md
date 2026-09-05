# Sonics — Instagram AI Account Analyzer & Enforcement Prediction Simulator

A read-only AI-powered Instagram profile and public-content analysis tool with a hypothetical enforcement prediction simulator.

- **It analyzes legitimately accessible Instagram information.**
- **It uses AI to analyze accessible content.**
- **It provides hypothetical enforcement predictions.**
- **It does NOT submit reports.**
- **It does NOT ban accounts.**
- **It does NOT manipulate Instagram's enforcement system.**

---

## 🎬 Demo

Below is an example of the complete application workflow and the type of result users can expect.

> ⚠️ **Important:** `@demo_account` below is a **fictional example account**. All numbers shown are **illustrative only** and are **NOT real Instagram enforcement probabilities**. When you run the application, it analyzes the **actual retrieved data** for whatever account you enter.

### Step 1 — Enter Instagram Account

```text
Instagram Username / Profile URL

@demo_account

[ Analyze Account ]
```

### Step 2 — Account Overview

```text
ACCOUNT OVERVIEW

Username: @demo_account
Display Name: Demo Account
Bio: Example profile for demonstration
Account Status: Public

Followers: 12,481
Following: 823
Posts: 147

Accessible Content Analyzed: 25 posts
```

> Demo values above are illustrative. Real values are retrieved from whatever information is legitimately available through the configured data source. If a field cannot be retrieved, the application returns **"Unavailable"** — it never invents data.

### Step 3 — AI Content Analysis

```text
CONTENT ANALYSIS

Spam
Classification: Low Risk
Confidence: 87%
Severity: Low

Harassment / Bullying
Classification: Potential Risk
Confidence: 72%
Severity: Medium

Hate Speech
Classification: No Clear Violation
Confidence: 91%
Severity: Low

Impersonation Risk
Classification: Potential Risk
Confidence: 68%
Severity: Medium
```

> ⚠️ This is ONLY an example UI/result. When the application is running, the AI analyzes the **actual retrieved content** of the account you enter — it does not generate results from the example above.

### Step 4 — Account-Level Analysis

```text
ACCOUNT RISK SUMMARY

Overall Model Risk: 63%

Accessible Items Analyzed: 25

Primary Signals:
• Repeated promotional patterns
• Several potentially abusive interactions
• Profile characteristics requiring additional review

Model Confidence: 76%
```

> This is an application-generated risk assessment, **not an official Instagram score**.

---

## ⚡ Sonics Enforcement Prediction Simulator

The Sonics simulator **does not submit reports and does not ban accounts**. It allows users to experiment with hypothetical reporting variables and produces a **model estimate**.

### Hypothetical Scenario

```text
HYPOTHETICAL SCENARIO

Violation reports:        5
Spam reports:             4
Impersonation reports:    4
Hypothetical sources:     8

[ Run Simulation ]
```

### Simulation Result

```text
SIMULATION RESULT

Estimated Enforcement Likelihood
87%

Model Confidence
71%

Uncertainty
±14%

Result Type
Hypothetical Model Estimate
```

> ⚠️ **The 87% above is NOT an actual Instagram probability.** It is an illustrative output from the application's hypothetical model. Instagram does not publicly disclose its enforcement thresholds, and this application never claims that a specific number of reports will ban an account.

---

## 🔄 Complete Workflow

1. User enters an Instagram username or profile URL.
2. The application checks what information is legitimately accessible.
3. Publicly accessible profile information is collected.
4. Publicly accessible content is collected where supported.
5. Content is normalized.
6. AI analysis agents analyze the retrieved content.
7. The account-level agent combines the results.
8. The user opens the Sonics Enforcement Prediction Simulator.
9. The user enters hypothetical simulation parameters.
10. The simulator produces an estimated model result.
11. Results are displayed in the dashboard.

> The same installed application can analyze many different accounts. **User input does not modify the source code.**

---

## ✨ Features

| Feature | Description |
|---|---|
| Public Instagram profile analysis | Username, display name, bio, follower/following counts, post count, account status |
| Public-content analysis | Captions and publicly accessible metadata |
| Private-account limited analysis | Only information legitimately visible without authorization |
| Spam analysis | Detects spam-like characteristics in retrieved content |
| Harassment / bullying analysis | Detects harassment, bullying, threats, or targeted abuse |
| Hate-speech analysis | Detects potentially prohibited hateful content. Political criticism is **not** automatically classified as hate speech |
| Impersonation-risk analysis | Flags indicators that may suggest impersonation |
| General policy-risk analysis | Other relevant policy-risk categories |
| Account-level AI analysis | Combines per-category results into an overall model risk score |
| Confidence & severity scores | Per-category model confidence and severity |
| Evidence-based analysis | References actual retrieved content wherever possible |
| Sonics Enforcement Prediction Simulator | Hypothetical, model-based enforcement likelihood |
| Scenario comparison | Compare different hypothetical scenarios side by side |
| Local AI mode | **Default** — no API key required, runs on your machine |
| Optional Google Gemini mode | Uses Gemini only when explicitly configured |
| FastAPI backend | Stateless REST API |
| React frontend | Interactive dashboard |
| pip-installable package | `pip install .` |
| CLI support | Start via the `sonics` command |
| No OpenAI API key required | OpenAI is **not** used at all |
| No mandatory API key in local mode | Local AI works out of the box |

---

## 🛡️ Read-Only Design

The application does **not**:

- Submit Instagram reports
- Automatically report accounts
- Ban accounts
- Control multiple Instagram accounts
- Bypass authentication
- Bypass CAPTCHAs
- Bypass rate limits
- Access private posts without authorization
- Manipulate Instagram enforcement

The enforcement simulator is **purely hypothetical**. Report counts and reporting-source counts exist solely as simulation variables — they are never sent to Instagram.

---

## 📋 Requirements

| Requirement | Detail |
|---|---|
| Python | 3.9 or newer |
| Node.js | 18 or newer (for the React frontend) |
| Internet connection | Required for permitted Instagram data retrieval |
| Local AI hardware | Runs on a normal consumer PC — CPU inference is supported. A GPU improves speed but is **not** required. |
| Optional Google Gemini | Requires a Google API key, and **only** when `AI_PROVIDER=gemini` |

---

## 🚀 Installation

> ⚠️ **Installation is a ONE-TIME process.** After installing, you never run `pip install` again for each account. User input is data — it does not trigger installation or source-code changes.

### Step 1 — Download or clone the project

Download or clone this repository and enter its directory:

```bash
cd banning-tool-by-me
```

### Step 2 — Create a virtual environment (recommended)

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install the application

```bash
pip install .
```

All required Python dependencies are declared in `pyproject.toml` and installed by this single command. This is the **one-time** installation — you do **not** run `pip install` for every account you analyze.

---

## 🤖 AI Configuration

### Default: Local AI (no API key required)

Local AI is the default. It runs entirely on your machine and requires **no API key**, no billing information, and no paid service. Create a `.env` file next to the backend configuration (or rely on defaults):

```env
AI_PROVIDER=local
```

> **DEFAULT MODE: Local AI — no API key required.**

### Optional: Google Gemini

Only if you want to use Gemini instead of local AI:

```env
AI_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key
```

> **OPTIONAL MODE: Google Gemini — requires a Google API key.**

**Important notes:**

- OpenAI is **not required** and is **not used** anywhere in this application.
- Gemini is **optional**.
- Local AI requires **no API key**.
- Gemini availability, free-tier access, quotas, and usage limits are controlled by Google and **may change at any time**.

---

## ▶️ Run

Start the backend with the installed CLI command:

```bash
sonics
```

This launches the FastAPI backend and serves the dashboard.

If you are developing the frontend, start it in development mode from the `frontend/` directory (one-time `npm install`):

```bash
cd frontend
npm install
npm run dev
```

When running in development mode, the backend normally listens on `http://localhost:8000`.

---

## 🧭 First Use

1. **Start the application** — run `sonics` (backend) and, if in development, `npm run dev` (frontend).
2. **Open the dashboard** in your browser.
3. **Enter an account** — type `@username` or the supported Instagram profile URL.
4. **Click "Analyze Account"**.
5. **Wait** for the profile/content analysis to complete.
6. **Review** the results:
   - Account Overview
   - Content Analysis (Spam, Harassment/Bullying, Hate Speech, Impersonation, Other Policy Risk)
   - Risk Summary
   - Evidence
   - Confidence
   - Severity
7. **Open** the **"Sonics Enforcement Prediction Simulator"**.
8. **Enter hypothetical simulation values** (violation / spam / impersonation report counts and source count).
9. **Click "Run Simulation"**.
10. **Review** the model estimate, confidence, uncertainty, and scenario comparison.

---

## 🔁 Analyzing Another Account

Once the application is installed, simply enter another username. The same installed application processes each new input:

```text
@account_one  →  Analyze  →  Result
@account_two  →  Analyze  →  Result
```

No additional installation. No source-code changes. No AI-agent code changes. No dependency installation. The application simply retrieves the new account's accessible data and runs the same analysis pipeline.

---

## 👤 Public vs Private Accounts

### Public account

The application analyzes all legitimately accessible profile information and public content — profile fields, posts, captions, and publicly accessible metadata.

### Private account

The application **never attempts to bypass privacy controls**. It only analyzes information legitimately visible without authorization — for example, username, display name, bio, and public profile metadata — and displays:

> "Limited analysis: this account is private or has limited publicly accessible information."

Private posts and private content are never accessed.

---

## 📊 Understanding Results

| Term | Meaning |
|---|---|
| **Classification** | The model's category label for a signal (e.g., "Low Risk", "Potential Risk", "No Clear Violation") |
| **Confidence** | How confident the model is in its **own classification**. It does **NOT** mean the probability that Instagram will ban the account. |
| **Severity** | The assessed potential impact or severity of an identified signal |
| **Risk score** | The account-level model's overall risk assessment. Application-generated, **not an official Instagram score**. |
| **Estimated enforcement likelihood** | A hypothetical model estimate produced by the Sonics simulator. It is **NOT** Instagram's official enforcement probability. |

**"Confidence"** means how confident the model is in its own classification. It does not mean probability that Instagram will ban the account.

**"Estimated enforcement likelihood"** is a hypothetical application-model output. It is not Instagram's official enforcement probability.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `pip install .` fails | Make sure your virtual environment is activated and Python 3.9+ is on your PATH |
| Missing dependencies | Re-run `pip install .` once in an activated environment. Dependencies are installed at setup, never during analysis. |
| Local model unavailable | The first analysis may download the configured local model once. Ensure you have internet access and storage space for that one-time download. A clear message explains which model is required. |
| Gemini API key missing | If `AI_PROVIDER=gemini`, set `GOOGLE_API_KEY` in your `.env`. Otherwise switch back to `AI_PROVIDER=local`. |
| Instagram data unavailable | The account may be private, or Instagram may be rate-limiting requests. The application shows **"Data unavailable"** instead of inventing data. |
| Private account | The application intentionally limits the analysis to publicly visible information. |
| Invalid username or profile URL | Enter `@username` or a full Instagram profile URL such as `https://www.instagram.com/username/`. |
| Network / API failure | Check your internet connection and retry. |
| Frontend cannot reach backend | Ensure the backend is running on `http://localhost:8000` and the frontend is configured to call that origin. |

> This application never provides instructions for bypassing Instagram restrictions.

---

## 📂 Project Structure

```
banning-tool-by-me/
├── backend/
│   ├── app/
│   │   ├── agents/            # AI analysis agents (analyzer + providers)
│   │   │   └── providers/     # AIProvider (LocalAIProvider, GeminiAIProvider)
│   │   ├── instagram/         # Instagram data-access layer
│   │   ├── models/            # Data schemas
│   │   └── simulation/        # Sonics Enforcement Prediction Simulator
│   ├── tests/                 # Backend automated tests
│   ├── .env.example           # Environment-variable template
│   └── requirements.txt       # Backend dependencies (mirrors pyproject.toml)
├── frontend/
│   ├── src/                   # React source code
│   ├── index.html             # Frontend entry HTML
│   └── package.json           # Frontend dependencies and scripts
├── pyproject.toml              # Package configuration + `sonics` CLI entry point
└── README.md
```

---

## ⚖️ Disclaimer

This project is an independent analysis and simulation application. It is **not affiliated with or endorsed by Instagram or Meta**.

- Instagram's actual enforcement system is **proprietary** and is not publicly known.
- Simulation results are **model estimates**.
- Results should **not** be interpreted as guaranteed enforcement outcomes.
- This application operates **read-only** with respect to Instagram: it never submits reports, bans accounts, or manipulates enforcement.

---

**One build. One install. Unlimited normal user inputs. Dynamic analysis outputs.**