# Resume Builder — One-Time Setup

Run this command once after installing the plugin to enable the advanced ATS/HR scoring engine.

## Input
$ARGUMENTS

## Instructions

You are helping the user set up the Resume Builder plugin's scoring engine. This is a one-time setup that installs Python dependencies needed for the MCP-based ATS and HR scorers.

### Step 1: Check Python

Run `python --version` (or `python3 --version` on Mac/Linux).

- If Python 3.10+ is installed, proceed to Step 2.
- If Python is NOT installed, tell the user:

```
The scoring engine requires Python 3.10 or later.

Download it from: https://www.python.org/downloads/

During installation:
- CHECK "Add Python to PATH" (Windows)
- Mac/Linux: Use your package manager (brew install python3)

After installing Python, run /resume-builder:setup again.
```

Stop here if Python is not installed.

### Step 2: Install Dependencies

Run this command to install all required packages:

```bash
pip install -r requirements.txt
```

If `pip` is not found, try `pip3 install -r requirements.txt` or `python -m pip install -r requirements.txt`.

The requirements file is located in the plugin directory. Use `${CLAUDE_PLUGIN_ROOT}/requirements.txt` if needed.

Wait for it to complete. This may take 1-3 minutes (sentence-transformers downloads a ~80MB model).

### Step 3: Set Up Configuration

Check if the user has a `config.json` in their project. If not, create one from `config.example.json`:

1. Read `config.example.json` from the plugin directory
2. Ask the user for their details:
   - Full name
   - Credentials (e.g., M.D., MBA, CPA — or leave blank)
   - Email
   - Phone
   - LinkedIn URL
   - Path to their master resume file (a markdown file with their full work history)
3. Create `config.json` with their answers

### Step 4: (Optional) LLM Scorer Setup

Ask the user if they want to enable the LLM-augmented scorer (uses Claude API for deeper analysis).

If yes:
1. They need an Anthropic API key from https://console.anthropic.com/
2. Create a `.env` file with: `ANTHROPIC_API_KEY=sk-ant-...`
3. This enables the `score_llm` and `score_combined` tools

If no, skip this step. The rules-based ATS and HR scorers work without an API key.

### Step 5: Verify

Run a quick test to verify everything works:

```bash
python -c "import ats_scorer; import hr_scorer; print('Scoring engine ready!')"
```

If successful, tell the user:

```
Setup complete! You can now use:

  /resume-builder:resume [paste job description]    — Full resume + cover letter package
  /resume-builder:tailor-resume [paste JD]          — Resume only
  /resume-builder:cover-letter [paste JD]           — Cover letter only
  /resume-builder:writing-coach [resume file]       — Improve resume writing quality

The ATS/HR scoring engine is now active and will automatically score your resumes.
```

If it fails, show the error and suggest fixes.
