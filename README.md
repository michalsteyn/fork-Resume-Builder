# Resume Builder — AI-Powered ATS & HR Optimized Resume Generator

An open-source, AI-powered resume and cover letter generator that tailors your applications to specific job descriptions using **dual-scoring optimization** and **parallel agent execution**. Works for **any profession** — software engineers, marketers, lawyers, finance, healthcare, and more. Available as a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)

---

## What This Does

You paste a job description. The system:

1. **Analyzes** the JD — extracts keywords, required skills, domain, seniority level
2. **Tailors** your master resume — rewrites bullets, reorders sections, matches terminology
3. **Scores** the result with two independent engines (ATS + HR simulation)
4. **Iterates** automatically until scores hit targets (ATS 75-85%, HR 70%+)
5. **Generates** production-ready DOCX files (resume + cover letter)
6. **Tracks** every application in an Excel spreadsheet

All of this runs in **parallel** — scoring happens in the background while the resume is being written, cover letters generate simultaneously, and DOCX files are created in parallel. ~50% faster than sequential execution.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│             Claude Code / Claude Cowork                      │
│     /resume  /tailor-resume  /cover-letter  /setup          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │  ATS     │  │  HR      │  │  LLM     │  │  Writing   │  │
│  │  Scorer  │  │  Scorer  │  │  Scorer  │  │  Coach     │  │
│  │ (7-comp) │  │ (6-fact) │  │ (Claude) │  │ (10 rules) │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │              │             │               │        │
│       └──────────────┴─────────────┘               │        │
│                      │                             │        │
│              ┌───────┴───────┐              ┌──────┴─────┐  │
│              │  MCP Server   │              │   DOCX     │  │
│              │ (auto-starts) │              │ Generator  │  │
│              │  FastMCP 3.0  │              │ (Workday)  │  │
│              └───────────────┘              └────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Orchestration State (state.json) — Multi-Agent DAG        │
│  Application Tracker (Excel) — Auto-updated per run        │
└─────────────────────────────────────────────────────────────┘
```

---

## Dual Scoring System

### ATS Scorer — 7 Weighted Components

Simulates how Applicant Tracking Systems filter resumes before a human ever sees them.

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| Keyword Match | 22% | Lemmatized keywords with synonym expansion |
| Semantic Similarity | 22% | SBERT vector cosine similarity between resume and JD |
| Weighted Industry Terms | 18% | Domain-specific terminology with recency decay |
| Phrase Match | 13% | Multi-word industry phrases (e.g., "clinical trial management") |
| BM25 Score | 13% | Probabilistic relevance ranking (BM25Plus) |
| Graph Centrality | 7% | Infers missing skills from related skills via NetworkX |
| Skill Recency | 5% | Exponential decay — recent experience weighted higher |

**Additional checks:** Hidden text detection, readability analysis (Flesch-Kincaid Grade 10-12 optimal), format risk assessment.

### HR Scorer — 6 Factors + Visual Analysis

Simulates how a human recruiter evaluates a resume in their typical 7-second scan.

| Factor | Weight | What It Measures |
|--------|--------|------------------|
| Experience Fit | 30% | Years of experience vs. JD requirements, Goldilocks zone |
| Skills Match | 20% | Demonstrated skills (action verbs) vs. listed skills |
| Career Trajectory | 20% | Title progression via linear regression slope |
| Impact Signals | 20% | Metrics density + Bloom's Taxonomy verb power levels |
| Competitive Edge | 10% | Company/university prestige signals |
| F-Pattern Visual | +/-5pts | Eye-tracking compliance (golden triangle, left-rail alignment) |

**Risk penalties:** Job hopping (-8 to -15 pts), unexplained gaps (-5 to -15 pts), recent instability.

### LLM Scorer (Optional)

Claude-powered rubric evaluation that catches nuances the algorithmic scorers miss — tone, coherence, storytelling quality.

---

## Getting Started

### Quick Start — 3 Steps

Works with **Claude Code** (CLI/IDE) and **Claude Cowork** (web).

**Step 1: Install the plugin**

```bash
# In Claude Code or Cowork
/plugin marketplace add jananthan30/Resume-Builder
/plugin install resume-builder
```

**Step 2: Run the setup wizard**

```
/resume-builder:setup
```

This walks you through everything:
- Checks if Python is installed (tells you where to download it if not)
- Installs all dependencies automatically (`pip install -r requirements.txt`)
- Creates your `config.json` with your name, email, phone, LinkedIn
- Optionally sets up the LLM scorer (Claude API key)

**Step 3: Start building resumes**

```
/resume-builder:resume [paste a job description here]
```

That's it. The plugin handles scoring, iteration, DOCX generation, and tracking.

### What Works Without Setup

Even before running `/resume-builder:setup`, these commands work immediately (they're just Claude prompts — no Python needed):

| Command | Works immediately? | With setup? |
|---------|-------------------|-------------|
| `/resume-builder:resume` | Yes — Claude writes the resume | + automated ATS/HR scoring and DOCX output |
| `/resume-builder:cover-letter` | Yes — Claude writes the letter | + DOCX output |
| `/resume-builder:writing-coach` | Yes — full writing audit | Same |
| `/resume-builder:setup` | Yes — runs the setup wizard | N/A |
| MCP scoring tools | No — needs Python | score_ats, score_hr, score_both, score_llm, score_combined |

### Alternative: Clone & Run Locally

If you prefer not to use the plugin system:

```bash
# Clone the repository
git clone https://github.com/jananthan30/Resume-Builder.git
cd Resume-Builder

# Install Python dependencies
pip install -r requirements.txt

# Download NLTK data (one-time)
python -c "import nltk; nltk.download('wordnet'); nltk.download('punkt_tab')"

# Copy config templates
cp .env.example .env
cp config.example.json config.json
```

Then edit `.env` (API key) and `config.json` (your info), and use the commands without the `resume-builder:` prefix (e.g., `/resume` instead of `/resume-builder:resume`).

### Your Master Resume

Create a Markdown file with your complete work history. This is the single source of truth — all tailored resumes are generated from it:

```markdown
FULL NAME, CREDENTIALS
City, State ZIP | Phone | Email | LinkedIn

PROFESSIONAL SUMMARY
[Your comprehensive summary with all skills and experience]

PROFESSIONAL EXPERIENCE

JOB TITLE | COMPANY NAME | City, State
Month Year – Month Year

• Achievement with quantified impact
• Another achievement with metrics

EDUCATION

Degree Name
University Name, City, State | Year – Year

CERTIFICATIONS
• Certification Name – Issuing Body
```

Set the path to this file in your `config.json` as `master_resume_path`.

---

## Usage

### Workflow Order

```
1. /resume-builder:setup          One-time setup (install deps, create config)
2. Create your master resume       YOUR_MASTER_RESUME.md with full work history
3. /resume-builder:resume [JD]    Paste a job description — get a full application
4. /resume-builder:writing-coach   Optional — audit and improve writing quality
```

### Slash Commands

| Command | What It Does |
|---------|-------------|
| `/resume-builder:setup` | One-time setup wizard (installs Python deps, creates config) |
| `/resume-builder:resume [JD]` | Full application: tailored resume + cover letter + scoring + DOCX + tracking |
| `/resume-builder:tailor-resume [JD]` | Resume only (no cover letter) |
| `/resume-builder:cover-letter [JD]` | Cover letter only |
| `/resume-builder:batch-resume` | Process multiple job descriptions in parallel |
| `/resume-builder:writing-coach [file]` | Audit and rewrite resume bullets using 10 writing rules |

If running locally (cloned repo), use short names: `/resume`, `/tailor-resume`, etc.

Each command runs a multi-phase parallel workflow:
- **Phase 1:** Parallel research (reads master resume, finds best match, sets up output folder)
- **Phase 2:** Background scoring + resume writing (non-blocking)
- **Phase 3:** Parallel scoring + cover letter generation
- **Phase 4:** Auto-iteration if scores < threshold (max 2 rounds)
- **Phase 5:** Parallel DOCX creation + tracker update
- **Phase 6:** Cleanup + score report

### Option 2: Scoring Server (REST API)

Run the scorers as a standalone service:

```bash
# Start the scoring server
python scorer_server.py --port 8100

# Health check
curl http://localhost:8100/health

# Score a resume against a job description
curl -X POST http://localhost:8100/score/ats \
  -F "resume=@resume.pdf" \
  -F "jd=@job_description.txt"

curl -X POST http://localhost:8100/score/hr \
  -F "resume=@resume.pdf" \
  -F "jd=@job_description.txt"

# Combined scoring (ATS + HR + optional LLM)
curl -X POST http://localhost:8100/score/combined \
  -F "resume=@resume.pdf" \
  -F "jd=@job_description.txt"
```

### Option 3: CLI Scorers (Standalone)

```bash
# ATS scoring
python ats_scorer.py --score resume.pdf job_description.txt --json

# HR scoring
python hr_scorer.py --score resume.pdf job_description.txt --json

# Web UI for scoring
python ats_scorer.py --web
python hr_scorer.py --score resume.pdf job_description.txt --web
```

---

## Claude Code / Cowork Plugin — How It Works

This project ships as a **Claude Code and Cowork plugin** with 6 slash commands + 5 MCP scoring tools. It works in Claude Code (CLI/IDE) and Claude Cowork (web).

### Slash Commands (6)

| Command | What It Does |
|---------|-------------|
| `/resume-builder:setup` | One-time setup wizard |
| `/resume-builder:resume` | Full application package with Swarm v3.0 parallel execution |
| `/resume-builder:tailor-resume` | Resume-only tailoring with dual scoring |
| `/resume-builder:cover-letter` | Standalone cover letter generation |
| `/resume-builder:batch-resume` | Batch process multiple JDs in parallel |
| `/resume-builder:writing-coach` | Resume writing quality audit (10 rules) |

### MCP Scoring Tools (5)

After running `/resume-builder:setup`, the MCP scorer auto-starts and provides these tools that Claude can call natively:

| Tool | What It Does |
|------|-------------|
| `score_ats` | ATS keyword + semantic scoring (7 components) |
| `score_hr` | HR recruiter simulation (6 factors + F-pattern) |
| `score_both` | ATS + HR combined in one call |
| `score_llm` | Claude-augmented scoring (requires API key) |
| `score_combined` | All 3 blended (70% rules / 30% LLM) |

### How It Works Under the Hood

The plugin uses slash commands (Markdown files in `commands/`) that define complex, multi-step workflows. When you type `/resume-builder:resume` followed by a job description, it loads the prompt template and `$ARGUMENTS` gets replaced with your input.

The MCP server (`mcp_scorer.py`) auto-starts via `.mcp.json` when the plugin loads, exposing scoring functions as native tools that Claude can call directly — no manual server startup needed.

These commands turn Claude into a specialized resume optimization agent that:
- Reads your master resume and the target job description
- Orchestrates multiple background agents (scorers, generators, trackers)
- Iterates on quality until score thresholds are met
- Produces production-ready DOCX files

### Writing Coach — 10 Rules Engine

The `/writing-coach` command applies these writing rules to every bullet point:

1. **Power Verb Start** — Every bullet begins with a strong action verb (Led, Directed, Spearheaded)
2. **Quantified Impact** — 40%+ of bullets must contain metrics (%, $, numbers)
3. **So-What Test** — Every bullet answers "why does this matter?"
4. **Jargon Calibration** — Match terminology level to the target role
5. **Tense Consistency** — Past tense for past roles, present for current
6. **Parallel Structure** — Consistent grammatical patterns within sections
7. **Length Optimization** — 1-2 lines per bullet, no walls of text
8. **Keyword Integration** — Natural placement, never forced
9. **Achievement vs. Duty** — Frame responsibilities as accomplishments
10. **Readability** — Flesch-Kincaid Grade 10-12 target

---

## Project Structure

```
Resume-Builder/
├── .claude-plugin/             # Plugin manifest
│   └── plugin.json             # Plugin metadata (name, version, author)
├── commands/                   # Slash commands (plugin format)
│   ├── setup.md                # One-time setup wizard
│   ├── resume.md               # Full application (Swarm v3.0)
│   ├── tailor-resume.md        # Resume only
│   ├── cover-letter.md         # Cover letter only
│   ├── batch-resume.md         # Batch processing
│   └── writing-coach.md        # Writing enhancement (10 rules)
├── hooks/                      # Plugin hooks
│   └── hooks.json              # SessionStart: checks if scoring is ready
├── .mcp.json                   # MCP server config (auto-starts scorer)
├── mcp_scorer.py               # MCP scoring server (5 tools via FastMCP)
├── data/                       # Reference databases for scoring
│   ├── keywords_*.json         # Domain-specific keyword databases (6 domains)
│   ├── skill_taxonomy.json     # Skill categories with decay constants
│   ├── company_prestige.json   # Company prestige scoring
│   ├── university_rankings.json# University prestige scores
│   ├── acronyms.json           # Industry acronym expansion
│   └── action_verbs.json       # Verb power classifications
├── ats_scorer.py               # ATS scoring engine (2,800+ lines)
├── hr_scorer.py                # HR scoring engine (2,900+ lines)
├── llm_scorer.py               # Claude-powered rubric scorer
├── scorer_server.py            # FastAPI REST API for scoring (standalone)
├── docx_generator.py           # ATS/Workday-compliant DOCX generator
├── orchestration_state.py      # Multi-agent state management (DAG)
├── tracker_utils.py            # Excel application tracker utilities
├── resume_builder.py           # CLI entry point
├── requirements.txt            # Python dependencies (including fastmcp)
├── config.example.json         # Config template
├── .env.example                # Environment variable template
├── CLAUDE.md                   # Project context for Claude Code
├── LICENSE                     # MIT License
└── README.md                   # You are here
```

---

## Domain-Specific Scoring

The ATS scorer auto-detects the job domain and applies domain-specific adjustments:

| Domain | Detection Method | Key Adjustments |
|--------|------------------|-----------------|
| **Clinical Research** | SBERT prototype embeddings | Publications bonus, transferable skills mapping |
| **Pharma/Biotech** | Keyword + semantic hybrid | Regulatory terminology weighting, pipeline experience |
| **Technology** | Keyword + semantic hybrid | Portfolio links bonus, 1.3x skill recency weight |
| **Finance** | Keyword + semantic hybrid | Deal artifacts required, 1.5x prestige weight |
| **Consulting** | Keyword + semantic hybrid | Impact metrics required, 1.4x prestige weight |
| **Healthcare** | Keyword + semantic hybrid | Certifications required, quality improvement focus |

---

## ATS-Compliant DOCX Output

The DOCX generator produces files optimized for Applicant Tracking Systems (Workday, Taleo, Greenhouse, Lever):

- **No tables, text boxes, columns, or graphics** (ATS parsers can't read these)
- **Heading styles** for section detection (Workday XML parsing)
- **Safe fonts**: Calibri, Arial, Times New Roman (10-12pt body)
- **Clean structure**: Contact info in body (not headers/footers)
- **Bold metrics** for visual impact during human review

---

## Scoring Reference

### ATS Score Interpretation

| Score | Rating | Meaning |
|-------|--------|---------|
| 80-100% | Excellent | Top candidate — likely to pass all ATS filters |
| 65-79% | Good | Strong match — will pass most filters |
| 50-64% | Fair | Competitive — may need optimization |
| 35-49% | Low | Below average — significant gaps |
| 0-34% | Poor | Unlikely to pass automated screening |

### HR Score Interpretation

| Score | Recommendation | Meaning |
|-------|---------------|---------|
| 85%+ | STRONG INTERVIEW | Top candidate |
| 70-84% | INTERVIEW | Competitive |
| 55-69% | MAYBE | Marginal — depends on candidate pool |
| <55% | PASS | Weak match |

---

## API Endpoints

When running the scorer server (`python scorer_server.py --port 8100`):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server health check |
| `/score/ats` | POST | ATS scoring (multipart: resume + jd files) |
| `/score/hr` | POST | HR scoring (multipart: resume + jd files) |
| `/score/llm` | POST | LLM scoring via Claude (requires API key) |
| `/score/combined` | POST | All three scorers combined |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| AI Agent Framework | [Claude Code](https://docs.anthropic.com/en/docs/claude-code) / [Claude Cowork](https://claude.ai) |
| LLM | [Claude](https://www.anthropic.com/claude) (Anthropic) |
| MCP Server | [FastMCP 3.0](https://gofastmcp.com/) (auto-starts with plugin) |
| Embeddings | [Sentence Transformers](https://sbert.net/) (all-MiniLM-L6-v2) |
| NLP | NLTK (lemmatization), TextStat (readability) |
| Search | BM25Plus (rank-bm25), NetworkX (skill graphs) |
| API Server | FastAPI + Uvicorn (standalone mode) |
| Document Generation | python-docx |
| PDF Parsing | pdfplumber |
| Tracking | openpyxl (Excel) |

---

## Contributing

Contributions are welcome! Some ideas:

- **New domain profiles** — add keyword databases for law, marketing, academia, etc.
- **Additional ATS parsers** — test against more ATS systems (Taleo, iCIMS, Greenhouse)
- **UI/Dashboard** — build a web frontend for the scoring API
- **Resume templates** — add more DOCX template styles
- **Internationalization** — support for non-English resumes and job markets

```bash
# Fork the repo, create a branch, make changes, submit a PR
git checkout -b feature/your-feature
# ... make changes ...
git commit -m "Add your feature"
git push origin feature/your-feature
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) by [Anthropic](https://www.anthropic.com/)
- ATS scoring research based on real-world Applicant Tracking System behavior
- HR scoring model informed by eye-tracking research on recruiter behavior
- Domain keyword databases curated from thousands of real job descriptions

---

## Supported Professions

This tool works for **any profession**. The ATS scorer auto-detects the job domain and applies domain-specific adjustments:

| Domain | Example Roles |
|--------|---------------|
| **Clinical Research** | Clinical Research Associate, Medical Monitor, Study Director |
| **Pharma/Biotech** | Regulatory Affairs, Medical Science Liaison, Drug Safety |
| **Technology** | Software Engineer, Product Manager, Data Scientist |
| **Finance** | Investment Analyst, Financial Controller, Risk Manager |
| **Consulting** | Management Consultant, Strategy Analyst, Business Advisor |
| **Healthcare** | Nurse Manager, Quality Director, Health Administrator |
| **General** | Any role not matching a specific domain — uses universal scoring |

The master resume can be from any field. Simply create your `YOUR_MASTER_RESUME.md` with your complete work history in the Workday-compatible format shown above, and the system will automatically detect your domain and the target role's domain to apply appropriate scoring weights.

---

**If this project helps you land interviews, give it a star!**
