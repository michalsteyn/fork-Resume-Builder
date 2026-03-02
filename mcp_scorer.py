"""
MCP Scorer Server — Exposes ATS, HR, and LLM resume scoring as MCP tools.

v3.0: Thin client mode — tries cloud API first, falls back to local scoring.

This wraps the existing scoring engines (ats_scorer, hr_scorer, llm_scorer)
so Claude Code and Claude Cowork can call them natively as MCP tools —
no manual server startup required.

Usage (standalone testing):
    fastmcp run mcp_scorer.py

As a plugin: configured via .mcp.json — auto-starts when plugin loads.
"""

import os
import sys
from pathlib import Path

# Load .env file from project root
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.isfile(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _ef:
        for _line in _ef:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ[_k.strip()] = _v.strip()

# Ensure project root is on sys.path for imports
PROJECT_ROOT = str(Path(__file__).parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP(
    "Resume Scorer",
    instructions="Dual ATS + HR resume scoring with semantic matching, recruiter simulation, and optional LLM-augmented analysis. Supports cloud and local scoring.",
)

# ─── Cloud client (optional — falls back to local) ───
try:
    from cloud.client import cloud_score, cloud_health
    CLOUD_CLIENT_AVAILABLE = True
except ImportError:
    CLOUD_CLIENT_AVAILABLE = False

# Lazy-load scorers on first call (SBERT model takes ~5s)
_scorers_loaded = False


def _ensure_scorers():
    global _scorers_loaded
    if not _scorers_loaded:
        global ats_scorer, hr_scorer
        import ats_scorer as _ats
        import hr_scorer as _hr
        ats_scorer = _ats
        hr_scorer = _hr
        _scorers_loaded = True


def _try_cloud(endpoint: str, resume_text: str, jd_text: str, extra: dict = None):
    """Try cloud API. Returns result dict or None if unavailable."""
    if not CLOUD_CLIENT_AVAILABLE:
        return None
    try:
        return cloud_score(endpoint, resume_text, jd_text, extra)
    except Exception:
        return None


@mcp.tool()
def score_ats(resume_text: str, jd_text: str) -> dict:
    """Score a resume against a job description using ATS (Applicant Tracking System) analysis.

    Returns keyword match %, semantic similarity, domain detection, missing keywords,
    readability analysis, and format risk assessment. Uses 8 weighted components:
    keyword match (20%), phrase match (25%), industry terms (15%),
    semantic similarity (10%), BM25 (10%), graph centrality (5%),
    skill recency (5%), job title match (10%).

    Args:
        resume_text: The full text content of the resume
        jd_text: The full text content of the job description

    Returns:
        Dictionary with total_score (0-100), matched/missing keywords, domain detection,
        readability analysis, and detailed component breakdowns.
    """
    # Try cloud first
    cloud_result = _try_cloud("/score/ats", resume_text, jd_text)
    if cloud_result and "total_score" in cloud_result:
        return cloud_result

    # Fall back to local
    _ensure_scorers()
    result = ats_scorer.calculate_ats_score(resume_text, jd_text)
    rating, likelihood, _color = ats_scorer.get_likelihood_rating(result["total_score"])
    result["rating"] = rating
    result["likelihood"] = likelihood
    result["_source"] = "local"
    return result


@mcp.tool()
def score_hr(resume_text: str, jd_text: str) -> dict:
    """Score a resume using HR recruiter simulation — evaluates like a human hiring manager.

    Analyzes experience fit, skills match, career trajectory, impact signals,
    competitive edge, and job fit. Includes F-pattern visual scoring, job-hopping
    penalty detection, and interview question generation.

    Args:
        resume_text: The full text content of the resume
        jd_text: The full text content of the job description

    Returns:
        Dictionary with overall_score (0-100), recommendation (INTERVIEW/MAYBE/PASS),
        factor breakdown, strengths, concerns, and suggested interview questions.
    """
    # Try cloud first
    cloud_result = _try_cloud("/score/hr", resume_text, jd_text)
    if cloud_result and "overall_score" in cloud_result:
        return cloud_result

    # Fall back to local
    _ensure_scorers()
    hr_result = hr_scorer.calculate_hr_score_from_text(resume_text, jd_text)
    result = hr_scorer.result_to_dict(hr_result)
    result["_source"] = "local"
    return result


@mcp.tool()
def score_both(resume_text: str, jd_text: str) -> dict:
    """Run both ATS and HR scoring in a single call. Most efficient for full analysis.

    Combines keyword/semantic ATS matching with human recruiter simulation.
    Use this when you need both scores at once (e.g., during resume optimization).

    Args:
        resume_text: The full text content of the resume
        jd_text: The full text content of the job description

    Returns:
        Dictionary with ats_score, hr_score, and full breakdowns for both.
    """
    # Try cloud first
    cloud_result = _try_cloud("/score/both", resume_text, jd_text)
    if cloud_result and "ats" in cloud_result:
        return cloud_result

    # Fall back to local
    _ensure_scorers()

    # ATS
    ats_result = ats_scorer.calculate_ats_score(resume_text, jd_text)
    rating, likelihood, _color = ats_scorer.get_likelihood_rating(ats_result["total_score"])
    ats_result["rating"] = rating
    ats_result["likelihood"] = likelihood

    # HR
    try:
        hr_result = hr_scorer.calculate_hr_score_from_text(resume_text, jd_text)
        hr_dict = hr_scorer.result_to_dict(hr_result)
    except Exception as e:
        hr_dict = {"overall_score": 0, "error": str(e)}

    return {
        "ats": ats_result,
        "hr": hr_dict,
        "summary": {
            "ats_score": round(ats_result.get("total_score", 0), 1),
            "hr_score": round(hr_dict.get("overall_score", 0), 1),
            "ats_rating": ats_result.get("rating", "Unknown"),
            "hr_recommendation": hr_dict.get("recommendation", "Unknown"),
        },
        "_source": "local",
    }


@mcp.tool()
def score_llm(resume_text: str, jd_text: str, domain_hint: str = "") -> dict:
    """Score a resume using Claude LLM-augmented analysis (requires ANTHROPIC_API_KEY).

    Uses Claude to evaluate the resume against a rubric covering keyword match,
    semantic similarity, industry terms, job fit, experience fit, impact signals,
    career trajectory, and competitive edge. Returns dimension-level scores with evidence.

    Args:
        resume_text: The full text content of the resume
        jd_text: The full text content of the job description
        domain_hint: Optional domain hint (technology, finance, consulting, clinical_research, healthcare, pharma_biotech)

    Returns:
        Dictionary with ats_score, hr_score, per-dimension scores with evidence,
        and a human-readable explanation.
    """
    # LLM scoring is always local (BYOK — user provides their own API key)
    try:
        from llm_scorer import score_with_llm, ANTHROPIC_AVAILABLE
        if not ANTHROPIC_AVAILABLE:
            return {"error": "anthropic package not installed. Run: pip install anthropic"}
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return {"error": "ANTHROPIC_API_KEY not set. Add it to your .env file."}
        return score_with_llm(resume_text, jd_text, domain_hint=domain_hint or None)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def extract_text(file_path: str) -> dict:
    """Extract text from a resume file (PDF, DOCX, MD, TXT).

    Reads the file and returns its plain text content. Use this when you need
    to read a .docx or .pdf file that Claude's Read tool can't handle directly.

    Args:
        file_path: Absolute or relative path to the file (.pdf, .docx, .md, .txt)

    Returns:
        Dictionary with text content, detected format, and character count.
    """
    from pathlib import Path

    p = Path(file_path)
    if not p.exists():
        return {"error": f"File not found: {file_path}"}

    ext = p.suffix.lower()
    text = ""

    try:
        if ext == ".pdf":
            import pdfplumber
            with pdfplumber.open(str(p)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif ext == ".docx":
            from docx import Document
            doc = Document(str(p))
            text = "\n".join(para.text for para in doc.paragraphs)
        elif ext in (".md", ".txt"):
            with open(str(p), "r", encoding="utf-8") as f:
                text = f.read()
        else:
            return {"error": f"Unsupported file format: {ext}. Supported: .pdf, .docx, .md, .txt"}
    except Exception as e:
        return {"error": f"Failed to extract text from {p.name}: {e}"}

    return {
        "text": text,
        "format": ext,
        "char_count": len(text),
    }


@mcp.tool()
def score_combined(resume_text: str, jd_text: str, domain_hint: str = "") -> dict:
    """Run all three scorers (ATS + HR + LLM) and return a blended result.

    Combines rules-based ATS/HR scores with LLM-augmented scoring using a
    70% rules / 30% LLM blend. Gracefully degrades to rules-only if LLM
    is unavailable (no API key or anthropic package).

    Args:
        resume_text: The full text content of the resume
        jd_text: The full text content of the job description
        domain_hint: Optional domain hint for LLM scorer

    Returns:
        Dictionary with combined_ats, combined_hr (blended scores),
        plus full breakdowns from all three scorers.
    """
    _ensure_scorers()

    # Rules-based scores (try cloud, fall back to local)
    cloud_result = _try_cloud("/score/both", resume_text, jd_text)

    if cloud_result and "ats" in cloud_result:
        rules_ats = cloud_result["ats"].get("total_score", 0)
        rules_hr = cloud_result["hr"].get("overall_score", 0)
        ats_result = cloud_result["ats"]
        hr_dict = cloud_result["hr"]
    else:
        ats_result = ats_scorer.calculate_ats_score(resume_text, jd_text)
        rules_ats = ats_result.get("total_score", 0)

        try:
            hr_result = hr_scorer.calculate_hr_score_from_text(resume_text, jd_text)
            hr_dict = hr_scorer.result_to_dict(hr_result)
            rules_hr = hr_result.overall_score
        except Exception:
            hr_dict = None
            rules_hr = 0

    # LLM score (always local — BYOK)
    llm_result = {"ats_score": None, "hr_score": None, "error": "skipped"}
    combined_ats, combined_hr = rules_ats, rules_hr
    blend_details = {"method": "rules_only"}

    try:
        from llm_scorer import score_with_llm, combine_scores, ANTHROPIC_AVAILABLE
        if ANTHROPIC_AVAILABLE and os.environ.get("ANTHROPIC_API_KEY"):
            llm_result = score_with_llm(resume_text, jd_text, domain_hint=domain_hint or None)
            combined_ats, combined_hr, blend_details = combine_scores(rules_ats, rules_hr, llm_result)
    except Exception as e:
        blend_details = {"method": "rules_only", "error": str(e)}

    return {
        "combined_ats": round(combined_ats, 1),
        "combined_hr": round(combined_hr, 1),
        "blend_details": blend_details,
        "rules_ats": {"total_score": rules_ats},
        "rules_hr": hr_dict,
        "llm": llm_result,
    }


if __name__ == "__main__":
    mcp.run()
