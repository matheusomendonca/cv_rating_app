import os, json
from dotenv import load_dotenv
import openai
from models import CandidateInfo, CandidateRating

class RatingAgent:
    """Agent that rates candidates according to a job description."""

    def __init__(self, job_description: str, model: str = "gpt-4o-mini"):
        load_dotenv(override=True)
        self.job_description = job_description
        self.model = model
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def rate(self, candidate: CandidateInfo) -> CandidateRating:
        prompt = f"""
        You are a technical recruiter for Enacom Group, a company that devolops softwares based on optimization, machine learning and data science. 
                
        Based on the job description below, rate the candidate on a scale 0-10 and provide strengths, weaknesses, and a short rationale.

        To create a score, consider the following:
        - The candidate's experience and skills in relation to the job description
        - The candidate's programming languages and frameworks in relation to the job description
        - The candidate's education and certifications in relation to the job description
        - The candidate's soft skills in relation to the job description
        - The candidate's personality and fit with the company culture
        - The candidate's alignment with the company values above
        
        Also infer the seniority level required for the job and the candidate's level of experience in relation to the job description.

        Beware of the following:
        - A junior candidate for a senior position is not a good fit.
        - A senior candidate for a junior position is not a good fit.
        - A candidate with no experience for a senior position is not a good fit.
        - A candidate with no experience for a junior position is a good fit.
        - A candidate with no experience for a mid-level position is not a good fit.
        - A candidate with no experience for a senior position is not a good fit.
        
        Job description:
        {self.job_description}

        Candidate JSON:
        {candidate.model_dump_json()}

        Return JSON with keys: score (number), strengths, weaknesses, rationale.
        """  # noqa: E501

        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant who returns JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("No content received from OpenAI")
        obj = json.loads(content)
        
        # Handle strengths and weaknesses fields - convert lists to strings if needed
        if isinstance(obj.get('strengths'), list):
            obj['strengths'] = ', '.join(str(item) for item in obj['strengths'])
        if isinstance(obj.get('weaknesses'), list):
            obj['weaknesses'] = ', '.join(str(item) for item in obj['weaknesses'])
        
        return CandidateRating(candidate_id=candidate.candidate_id, file=candidate.file, **obj)
