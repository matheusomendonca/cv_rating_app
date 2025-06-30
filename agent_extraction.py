import os, json
import openai
from dotenv import load_dotenv
from typing import Dict
from models import CandidateInfo

class ExtractionAgent:
    """Agent that extracts structured candidate info using OpenAI."""

    def __init__(self, model: str = "gpt-4o-mini"):
        load_dotenv(override=True)
        self.model = model
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def extract(self, cv_data: Dict) -> CandidateInfo:
        prompt = f"""Extract the following candidate information from the CV text below and return it as a JSON object with these exact fields:

        {{
            "name": "string - full name",
            "email": "string - primary email address", 
            "phone": "string or null - phone number if available",
            "languages": ["array of strings - spoken language names only"],
            "programming_languages": ["array of strings - programming language names only"],
            "frameworks": ["array of strings - framework names only"],
            "years_experience": "integer or null - total years of experience",
            "education": "string or null - education summary (degree, institution, year)",
            "summary": "string or null - professional summary"
        }}

        Important:
        - For languages: return only language names as strings, not objects
        - For programming_languages: return only programming language names as strings, not objects
        - For frameworks: return only framework names as strings, not objects
        - For education: provide a concise summary, not detailed objects
        - For years_experience: return only the number, not text
        - For email: return only the primary email, not a list

        CV TEXT:
        {cv_data['content']}
        """
        
        # Create a simplified schema for extraction that matches our model
        extraction_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Full name of the candidate"},
                "email": {"type": "string", "description": "Primary email address"},
                "phone": {"type": ["string", "null"], "description": "Phone number if available"},
                "languages": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "List of languages the candidate knows"
                },
                "programming_languages": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "List of programming languages the candidate knows"
                },
                "frameworks": { 
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "List of frameworks the candidate knows"
                },
                "years_experience": {
                    "type": ["integer", "null"], 
                    "description": "Total years of professional experience"
                },
                "education": {
                    "type": ["string", "null"], 
                    "description": "Education summary (degree, institution, year)"
                },
                "summary": {
                    "type": ["string", "null"], 
                    "description": "Professional summary or objective"
                }
            },
            "required": ["name", "email"]
        }
        
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert HR assistant. Extract candidate information and return it in the exact JSON structure specified. For languages, return only language names as strings. For education, provide a concise summary. For years_experience, return only the number."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("No content received from OpenAI")
        data = json.loads(content)
        
        # Minimal post-processing since structured output should handle most cases
        # Handle languages field - ensure it's always a list
        if not isinstance(data.get('languages'), list):
            if data.get('languages') is None:
                data['languages'] = []
            elif isinstance(data.get('languages'), dict):
                data['languages'] = list(data['languages'].keys())
            else:
                data['languages'] = [str(data['languages'])]
        
        # Handle programming_languages field - ensure it's always a list    
        if not isinstance(data.get('programming_languages'), list):
            if data.get('programming_languages') is None:
                data['programming_languages'] = []
            elif isinstance(data.get('programming_languages'), dict):
                data['programming_languages'] = list(data['programming_languages'].keys())
            else:
                data['programming_languages'] = [str(data['programming_languages'])]

        # Handle frameworks field - ensure it's always a list
        if not isinstance(data.get('frameworks'), list):
            if data.get('frameworks') is None:
                data['frameworks'] = []
            elif isinstance(data.get('frameworks'), dict):
                data['frameworks'] = list(data['frameworks'].keys())
            else:
                data['frameworks'] = [str(data['frameworks'])]

        # Handle years_experience - ensure it's an integer or None
        if isinstance(data.get('years_experience'), str):
            import re
            numbers = re.findall(r'\d+', data['years_experience'])
            if numbers:
                data['years_experience'] = int(numbers[0])
            else:
                data['years_experience'] = None
        
        # Ensure required fields have defaults
        if data.get('name') is None:
            data['name'] = "Unknown"
        if data.get('email') is None:
            data['email'] = "No email provided"
        
        return CandidateInfo(candidate_id=cv_data['candidate_id'], file=cv_data['file'], **data)
