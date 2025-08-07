# CV Pipeline Debug Test

This folder contains a comprehensive test setup to debug the CV rating pipeline and identify issues with the judge agent.

## Files

- `sample_cv.txt` - A sample CV in text format for testing
- `debug_pipeline.py` - Comprehensive debug script that tests the entire pipeline step by step
- `README.md` - This file

## How to Use

### 1. Prerequisites
Make sure you have:
- Python virtual environment activated
- OpenAI API key set in your environment
- All dependencies installed

### 2. Run the Debug Test
```bash
cd test_cv_upload
python debug_pipeline.py
```

### 3. What the Test Does

The debug script will:

1. **Test Extraction Agent**: Extract information from the sample CV
2. **Test Rating Agent**: Rate the candidate against a job description
3. **Test Judge Agent**: Re-rate the candidate for fairness and consistency
4. **Test Combiner**: Combine all data into the final DataFrame

### 4. Expected Output

The script will show detailed output for each step, including:
- Success/failure status
- Extracted data
- Scores and evaluations
- Any errors or warnings

### 5. Debugging the Judge Agent

If the judge agent is failing, you'll see:
- The raw response from the LLM
- Parsing errors
- Field mapping issues
- Fallback messages

### 6. Upload Your Own CV

To test with your own CV:
1. Replace the content in `sample_cv.txt` with your CV text
2. Run the debug script again
3. Check the output for any issues

## Common Issues

### Judge Agent Falls Back to Original Rating
If you see "Avaliação original mantida devido a erro de processamento", it means:
- The LLM response couldn't be parsed
- The response format was incorrect
- There was a network or API error

### Field Mapping Issues
If "Pontos Fracos" contains justification text:
- The LLM returned the wrong field structure
- The parsing logic has a bug
- The prompt needs to be more explicit

### Decimal Separator Issues
If scores have inconsistent formatting:
- Check the combiner.py formatting logic
- Ensure all agents return numeric scores
- Verify the final formatting step

## Next Steps

After running the debug script:
1. Check the console output for any error messages
2. Look for the specific step that's failing
3. Examine the LLM responses and parsing logic
4. Fix the identified issues
5. Re-run the test to verify the fix 