# CV Rating Analyzer

A modular, testable application that:

1. Parses PDF CVs from a folder or uploaded files.
2. Extracts structured candidate information with OpenAI (Agent 1).
3. Rates each candidate against a job description with OpenAI (Agent 2).
4. Combines and sorts the results.
5. Exports everything to Excel.

## Quick Start

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# 3. Run the Streamlit app
streamlit run app.py
```

## Tests
```bash
pip install pytest
pytest
```
