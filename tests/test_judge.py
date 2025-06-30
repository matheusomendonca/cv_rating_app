from cv_rating_app.models import CandidateInfo, CandidateRating, JudgeRating
from cv_rating_app.agent_judge import JudgeAgent

def test_judge_agent_creation():
    """Test that JudgeAgent can be created with a job description."""
    job_description = "Python developer with 3+ years experience"
    judge = JudgeAgent(job_description)
    assert judge.job_description == job_description
    assert judge.model == "gpt-4o-mini"
    assert judge.batch_size == 10  # Default batch size

def test_judge_rating_model():
    """Test that JudgeRating model can be created."""
    judge_rating = JudgeRating(
        candidate_id="test-id",
        file="test.pdf",
        score=8.5,
        strengths="Strong Python skills",
        weaknesses="Limited frontend experience",
        rationale="Good fit for backend role",
        initial_score=7.0,
        score_adjustment="Increased score due to strong backend skills"
    )
    assert judge_rating.file == "test.pdf"
    assert judge_rating.score == 8.5
    assert judge_rating.initial_score == 7.0

def test_judge_agent_parallel_processing():
    """Test that JudgeAgent supports parallel processing parameters."""
    job_description = "Python developer with 3+ years experience"
    judge = JudgeAgent(job_description, batch_size=5)
    assert judge.batch_size == 5 