# CV Rating Analyzer

A sophisticated multi-agent system that processes candidate CV PDFs through an intelligent pipeline to extract, rate, and judge candidates against job descriptions. The application uses OpenAI LLM agents for intelligent processing and provides both real-time analysis and comprehensive Excel reports.

## 🏗️ Multi-Agent Architecture

The application implements a sophisticated 6-agent pipeline that processes CVs in parallel for optimal performance:

### 🤖 Agent Overview

1. **📄 Parser Agent** (`parser.py`)
   - Extracts raw text from PDF CVs
   - Handles multiple PDF formats and structures
   - Generates unique `candidate_id` for each CV
   - Runs in parallel for batch processing

2. **🧹 Cleaning Agent** (`agent_cleaning.py`)
   - Removes malicious content, scripts, and harmful links
   - Eliminates biased content that could unfairly influence ratings
   - Preserves all professional information (contact details, experience, skills)
   - Ensures data quality and consistency

3. **🔍 Extraction Agent** (`agent_extraction.py`)
   - Uses OpenAI GPT-4 to extract structured candidate information
   - Identifies: name, email, phone, languages, programming languages, frameworks
   - Extracts years of experience, education, and professional summary
   - Returns validated `CandidateInfo` objects with consistent data structure

4. **⭐ Rating Agent** (`agent_rating.py`)
   - Evaluates candidates against job descriptions using OpenAI
   - Provides scores (0-10) with detailed strengths, weaknesses, and rationale
   - Considers technical skills, experience level, and cultural fit
   - Analyzes seniority alignment and job requirements match

5. **⚖️ Judge Agent** (`agent_judge.py`)
   - **Critical Quality Control**: Re-evaluates all candidates for fairness and consistency
   - Processes candidates in batches to ensure relative comparison
   - Identifies rating inconsistencies across the candidate pool
   - Provides final scores with adjustment explanations
   - Ensures unbiased, consistent evaluation standards

6. **🔗 Combiner Agent** (`combiner.py`)
   - Merges all agent outputs into unified data structures
   - Handles missing data gracefully with outer joins
   - Preserves candidate identification throughout the pipeline
   - Prepares data for final presentation and Excel export

### 🔄 Pipeline Flow

```
PDF Uploads → Parser → Cleaner → Extractor → Rater → Judge → Combiner → Excel Report
     ↓           ↓        ↓         ↓        ↓       ↓        ↓         ↓
  Parallel    Parallel  Parallel  LLM      LLM     LLM     Merge    Final
  Processing  Processing Processing Calls   Calls   Calls   Data     Output
```

### ⚡ Performance Features

- **Parallel Processing**: All agents run concurrently using ThreadPoolExecutor
- **Batch Processing**: Judge agent processes candidates in configurable batches
- **Retry Logic**: Robust error handling with automatic retries for LLM calls
- **Progress Tracking**: Real-time progress bars and status updates
- **Memory Management**: Efficient data flow with minimal memory footprint

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- PDF processing libraries

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd cv_rating_app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# 4. Run the Streamlit app
streamlit run app.py
```

### Usage

1. **Upload CVs**: Select multiple PDF files containing candidate CVs
2. **Job Description**: Paste the target job description in the text area
3. **Process**: Click "Process" to start the multi-agent pipeline
4. **Monitor**: Watch real-time progress as each agent processes the data
5. **Results**: View the final ranked table and download Excel report

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest

# Run specific test files
pytest tests/test_parser.py
pytest tests/test_judge.py
pytest tests/test_combiner.py
```

## 📊 Output Format

The final output includes:

- **Final Score**: Judge-adjusted rating (0-10)
- **Initial Score**: Original rating for comparison
- **Candidate Information**: Name, email, phone, languages, skills
- **Strengths & Weaknesses**: Detailed analysis
- **Rationale**: Explanation of rating decisions
- **Score Adjustment**: Justification for any changes from initial rating

## 🔧 Configuration

### Agent Parameters

```python
# Extraction Agent
extractor = ExtractionAgent(model="gpt-4o-mini")

# Rating Agent  
rater = RatingAgent(job_description, model="gpt-4o-mini")

# Judge Agent
judge = JudgeAgent(job_description, model="gpt-4o-mini", batch_size=5)
```

### Performance Tuning

- **Thread Workers**: Adjust `max_workers` for parallel processing
- **Batch Size**: Configure judge agent batch size for optimal LLM usage
- **Model Selection**: Choose between GPT-4, GPT-4o-mini, or other OpenAI models

## 🛡️ Quality Assurance

### Data Validation
- All agent outputs are validated against Pydantic models
- Candidate IDs ensure data integrity throughout the pipeline
- Outer joins preserve all candidates even if some agents fail

### Error Handling
- Graceful degradation when individual agents fail
- Fallback mechanisms for missing data
- Comprehensive logging and debugging information

### Fairness & Consistency
- Judge agent ensures rating consistency across all candidates
- Bias detection and removal in cleaning agent
- Relative comparison prevents isolated rating decisions

## 📁 Project Structure

```
cv_rating_app/
├── app.py                 # Main Streamlit application
├── parser.py              # PDF parsing and text extraction
├── agent_cleaning.py      # Content cleaning and sanitization
├── agent_extraction.py    # Structured information extraction
├── agent_rating.py        # Initial candidate rating
├── agent_judge.py         # Fairness and consistency evaluation
├── combiner.py            # Data merging and final preparation
├── formatter.py           # Excel export functionality
├── models.py              # Pydantic data models
├── requirements.txt       # Python dependencies
├── tests/                 # Unit tests
│   ├── test_parser.py
│   ├── test_judge.py
│   └── test_combiner.py
└── README.md             # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
