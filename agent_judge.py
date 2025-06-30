import os, json
from dotenv import load_dotenv
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import CandidateInfo, CandidateRating, JudgeRating

class JudgeAgent:
    """Agent that re-rates all candidates for fairness and consistency."""

    def __init__(self, job_description: str, model: str = "gpt-4o-mini", batch_size: int = 10):
        load_dotenv(override=True)
        self.job_description = job_description
        self.model = model
        self.batch_size = batch_size
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def judge_all(self, candidates: list[CandidateInfo], ratings: list[CandidateRating], progress_callback=None, max_workers: int = 4) -> list[JudgeRating]:
        """Re-rate all candidates for fairness and consistency."""
        
        all_judge_ratings = []
        total_batches = (len(candidates) + self.batch_size - 1) // self.batch_size
        
        # Create batches
        batches = []
        for i in range(0, len(candidates), self.batch_size):
            batch_candidates = candidates[i:i + self.batch_size]
            batch_ratings = ratings[i:i + self.batch_size]
            batches.append((batch_candidates, batch_ratings, i // self.batch_size + 1))
        
        # Process batches in parallel
        completed_batches = 0
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(self._judge_batch, batch_candidates, batch_ratings): (batch_candidates, batch_ratings, batch_num) 
                      for batch_candidates, batch_ratings, batch_num in batches}
            
            for fut in as_completed(futures):
                if progress_callback:
                    completed_batches += 1
                    progress_callback(completed_batches / total_batches, f"Completed batch {completed_batches}/{total_batches}")
                
                try:
                    batch_judge_ratings = fut.result()
                    all_judge_ratings.extend(batch_judge_ratings)
                except Exception as e:
                    batch_candidates, batch_ratings, batch_num = futures[fut]
                    print(f"Error processing batch {batch_num}: {e}")
                    # Create fallback ratings for this batch
                    for candidate, rating in zip(batch_candidates, batch_ratings):
                        all_judge_ratings.append(JudgeRating(
                            candidate_id=candidate.candidate_id,
                            file=candidate.file,
                            score=rating.score,
                            strengths=rating.strengths,
                            weaknesses=rating.weaknesses,
                            rationale=rating.rationale,
                            initial_score=rating.score,
                            score_adjustment=f"No adjustment - using original rating due to batch {batch_num} error"
                        ))
        
        print(f"Total candidates processed: {len(all_judge_ratings)}")
        
        # Validate that we processed all candidates
        if len(all_judge_ratings) != len(candidates):
            print(f"WARNING: Expected {len(candidates)} judge ratings, but got {len(all_judge_ratings)}")
            
            # Create missing ratings from original ratings
            processed_files = {rating.file for rating in all_judge_ratings}
            missing_files = [c.file for c in candidates if c.file not in processed_files]
            
            print(f"Missing files: {missing_files}")
            
            for candidate, rating in zip(candidates, ratings):
                if candidate.file not in processed_files:
                    print(f"Creating fallback rating for {candidate.file}")
                    all_judge_ratings.append(JudgeRating(
                        candidate_id=candidate.candidate_id,
                        file=candidate.file,
                        score=rating.score,
                        strengths=rating.strengths,
                        weaknesses=rating.weaknesses,
                        rationale=rating.rationale,
                        initial_score=rating.score,
                        score_adjustment="No adjustment - using original rating due to missing judge rating"
                    ))
        
        print(f"Final total candidates processed: {len(all_judge_ratings)}")
        return all_judge_ratings

    def _judge_batch(self, candidates: list[CandidateInfo], ratings: list[CandidateRating]) -> list[JudgeRating]:
        """Judge a batch of candidates."""
        
        # Create a summary of all candidates and their initial ratings
        candidates_summary = []
        for candidate, rating in zip(candidates, ratings):
            candidates_summary.append({
                "file": candidate.file,
                "name": candidate.name,
                "candidate_info": candidate.model_dump(),
                "initial_rating": rating.model_dump()
            })
        
        prompt = f"""You are a senior technical recruiter acting as a judge. You have received initial ratings for all candidates and must re-rate them to ensure fairness and consistency across all evaluations.

        Your role is to:
        1. Review all candidates and their initial ratings
        2. Identify any inconsistencies in the rating scale
        3. Ensure fair comparison between candidates
        4. Provide final scores that are consistent and justifiable
        5. Consider the relative strengths and weaknesses across all candidates
        6. Do not consider the candidate's name or other personal information when rating them

        Job description:
        {self.job_description}

        All candidates and their initial ratings:
        {json.dumps(candidates_summary, indent=2)}

        Instructions:
        - Rate each candidate on a scale of 0-10
        - Ensure your ratings are consistent and fair across all candidates
        - Consider the relative strengths and weaknesses when comparing candidates
        - Provide a brief rationale for any significant changes from initial ratings
        - Focus on the candidate's fit for the specific job requirements
        - Ensure the seniority level of the candidate is consistent with the job description, if it is not, even if the candidate is a good fit, adjust the score accordingly

        IMPORTANT: Return a JSON array (list) where each object contains:
        - file: the candidate's file name
        - score: your final score (0-10)
        - strengths: key strengths for this role
        - weaknesses: areas of concern
        - rationale: brief explanation of your rating
        - initial_score: the original score for comparison
        - score_adjustment: explanation of any significant changes from initial rating

        Example format:
        [
          {{
            "file": "candidate1.pdf",
            "score": 8.5,
            "strengths": "Strong Python skills",
            "weaknesses": "Limited frontend experience",
            "rationale": "Good fit for backend role",
            "initial_score": 7.0,
            "score_adjustment": "Increased score due to strong backend skills"
          }},
          {{
            "file": "candidate2.pdf",
            "score": 6.0,
            "strengths": "Good communication skills",
            "weaknesses": "Limited technical experience",
            "rationale": "Junior level candidate",
            "initial_score": 7.5,
            "score_adjustment": "Reduced score due to lack of required experience"
          }}
        ]

        Return only valid JSON array.
        """

        # Retry logic for LLM calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
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
                
                # Debug: Print the raw response
                print(f"DEBUG: Raw LLM response length: {len(content)} characters")
                
                # Parse the response - it should be an array of judge ratings, or a dict with 'ratings', or a single dict
                try:
                    parsed = json.loads(content)
                    print(f"DEBUG: Parsed JSON type: {type(parsed)}")
                    
                    if isinstance(parsed, list):
                        ratings_array = parsed
                    elif isinstance(parsed, dict):
                        # If it's a dict with a 'ratings' key, use that
                        if "ratings" in parsed and isinstance(parsed["ratings"], list):
                            ratings_array = parsed["ratings"]
                        # If it's a dict that looks like a single rating, wrap it in a list
                        elif all(k in parsed for k in ("file", "score")):
                            ratings_array = [parsed]
                        # Try to find any list in the dict that might contain ratings
                        elif any(isinstance(v, list) for v in parsed.values()):
                            for key, value in parsed.items():
                                if isinstance(value, list) and value and isinstance(value[0], dict) and "file" in value[0]:
                                    ratings_array = value
                                    break
                            else:
                                raise ValueError(f"Expected array of ratings or dict with 'ratings' key or a single rating dict. Got: {type(parsed)} with keys: {list(parsed.keys())}")
                        else:
                            raise ValueError(f"Expected array of ratings or dict with 'ratings' key or a single rating dict. Got: {type(parsed)} with keys: {list(parsed.keys())}")
                    else:
                        raise ValueError(f"Expected array or dict in judge response, got: {type(parsed)}")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: JSON decode error: {e}")
                    raise ValueError("Invalid JSON response from judge agent")
                
                print(f"DEBUG: Final ratings array length: {len(ratings_array)}")
                
                # Fallback: if we can't parse the response, create judge ratings from original ratings
                if not ratings_array:
                    print("WARNING: No ratings found in response, creating fallback ratings")
                    judge_ratings = []
                    for candidate, rating in zip(candidates, ratings):
                        judge_ratings.append(JudgeRating(
                            candidate_id=candidate.candidate_id,
                            file=candidate.file,
                            score=rating.score,
                            strengths=rating.strengths,
                            weaknesses=rating.weaknesses,
                            rationale=rating.rationale,
                            initial_score=rating.score,
                            score_adjustment="No adjustment - using original rating due to parsing error"
                        ))
                    return judge_ratings
                
                judge_ratings = []
                # Ensure we have the same number of ratings as candidates
                if len(ratings_array) != len(candidates):
                    print(f"WARNING: LLM returned {len(ratings_array)} ratings for {len(candidates)} candidates")
                    # If we have fewer ratings than candidates, create fallback ratings for missing ones
                    for i, (candidate, rating) in enumerate(zip(candidates, ratings)):
                        if i < len(ratings_array):
                            rating_data = ratings_array[i].copy()  # Make a copy to avoid modifying original
                            rating_data.pop('file', None)  # Remove file to avoid duplicate argument
                            # Handle strengths and weaknesses fields - convert lists to strings if needed
                            if isinstance(rating_data.get('strengths'), list):
                                rating_data['strengths'] = ', '.join(str(item) for item in rating_data['strengths'])
                            if isinstance(rating_data.get('weaknesses'), list):
                                rating_data['weaknesses'] = ', '.join(str(item) for item in rating_data['weaknesses'])
                            # Always include candidate_id from the original candidate
                            judge_ratings.append(JudgeRating(candidate_id=candidate.candidate_id, file=candidate.file, **rating_data))
                        else:
                            # Create fallback rating for missing candidate
                            judge_ratings.append(JudgeRating(
                                candidate_id=candidate.candidate_id,
                                file=candidate.file,
                                score=rating.score,
                                strengths=rating.strengths,
                                weaknesses=rating.weaknesses,
                                rationale=rating.rationale,
                                initial_score=rating.score,
                                score_adjustment="No adjustment - using original rating due to missing LLM response"
                            ))
                else:
                    # Normal case: same number of ratings as candidates
                    for rating_data, candidate, rating in zip(ratings_array, candidates, ratings):
                        rating_data = rating_data.copy()  # Make a copy to avoid modifying original
                        rating_data.pop('file', None)  # Remove file to avoid duplicate argument
                        # Handle strengths and weaknesses fields - convert lists to strings if needed
                        if isinstance(rating_data.get('strengths'), list):
                            rating_data['strengths'] = ', '.join(str(item) for item in rating_data['strengths'])
                        if isinstance(rating_data.get('weaknesses'), list):
                            rating_data['weaknesses'] = ', '.join(str(item) for item in rating_data['weaknesses'])
                        # Always include candidate_id from the original candidate
                        judge_ratings.append(JudgeRating(candidate_id=candidate.candidate_id, file=candidate.file, **rating_data))
                
                return judge_ratings
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    # Last attempt failed, create fallback ratings
                    print(f"All {max_retries} attempts failed, creating fallback ratings")
                    judge_ratings = []
                    for candidate, rating in zip(candidates, ratings):
                        judge_ratings.append(JudgeRating(
                            candidate_id=candidate.candidate_id,
                            file=candidate.file,
                            score=rating.score,
                            strengths=rating.strengths,
                            weaknesses=rating.weaknesses,
                            rationale=rating.rationale,
                            initial_score=rating.score,
                            score_adjustment=f"No adjustment - using original rating due to LLM failure after {max_retries} attempts"
                        ))
                    return judge_ratings
                else:
                    # Wait before retrying
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        # This should never be reached, but just in case
        judge_ratings = []
        for candidate, rating in zip(candidates, ratings):
            judge_ratings.append(JudgeRating(
                candidate_id=candidate.candidate_id,
                file=candidate.file,
                score=rating.score,
                strengths=rating.strengths,
                weaknesses=rating.weaknesses,
                rationale=rating.rationale,
                initial_score=rating.score,
                score_adjustment="No adjustment - using original rating due to unexpected error"
            ))
        return judge_ratings 