# ReAct-Based AI Assistant

A Python implementation of a ReAct (Reasoning and Acting) assistant that alternates between LLM decisions and external tool execution.

## Tools
- **Search:** DuckDuckGo search through the `ddgs` package.
- **Calculator:** Safe arithmetic evaluation using Python's `ast` and `operator` modules.

## Architecture

User question → Thought → Action → Observation → (repeat if needed) → Final answer

The LLM selects either the Search tool or Calculator tool. The tool result is returned to the LLM as an observation, allowing it to decide whether another action is needed.

## Technologies
- Python
- Groq API
- `openai/gpt-oss-120b` model
- DuckDuckGo Search (`ddgs`)

## Setup

### 1. Clone the repository
```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd ReAct_AI_Assistant
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure your Groq API key

Create an API key at https://console.groq.com/keys.

Windows PowerShell:
```powershell
$env:GROQ_API_KEY="your_groq_api_key"
```

macOS/Linux:
```bash
export GROQ_API_KEY="your_groq_api_key"
```

Do not commit or share your API key.

### 4. Run
```bash
python react_assistant.py
```

## Sample tests

1. **Calculator:** `What is 250 multiplied by 48 plus 500?`
   - Expected calculation: `12500`

2. **Search:** `Who invented the World Wide Web?`
   - Expected result: Tim Berners-Lee (verify against search results).

3. **Multiple tools:** `Search for the population of India and calculate 10 percent of it.`
   - Expected sequence: Search → Observation → Calculator → Observation → Final answer.
   - The result depends on the population estimate found by the search tool.

## Project files
- `react_assistant.py` — complete implementation.
- `requirements.txt` — Python dependencies.
- `.gitignore` — excludes local secrets and temporary files.
- `screenshots/` — add screenshots of your successful practical tests here.

## Notes
- An internet connection and a valid Groq API key are required.
- Model availability and API limits are controlled by Groq.
- The calculator supports basic arithmetic: `+`, `-`, `*`, `/`, `**`, and `%`.
