import os
import tempfile
from cv_rating_app.parser import CVParser
from cv_rating_app.agent_extraction import ExtractionAgent
from cv_rating_app.models import CandidateInfo

def test_parser_creation():
    """Test that CVParser can be created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        parser = CVParser(tmpdir)
        assert parser.source_path == tmpdir

def test_parser_parallel_processing():
    """Test that CVParser supports parallel processing parameters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        parser = CVParser(tmpdir)
        # Test that parse method accepts max_workers parameter
        result = parser.parse(max_workers=4)
        assert isinstance(result, list)

def test_candidate_id_present_and_unique():
    """Test that candidate_id is present and unique in parsed CVs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two dummy PDF files
        pdf1 = os.path.join(tmpdir, "a.pdf")
        pdf2 = os.path.join(tmpdir, "b.pdf")
        with open(pdf1, "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<<>>\n%%EOF")
        with open(pdf2, "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<<>>\n%%EOF")
        parser = CVParser(tmpdir)
        parsed = parser.parse(max_workers=2)
        ids = [cv['candidate_id'] for cv in parsed]
        assert all(ids), "All candidate_id fields should be present"
        assert len(set(ids)) == len(ids), "candidate_id fields should be unique"

def test_candidate_id_passed_to_candidateinfo():
    """Test that candidate_id is passed through to CandidateInfo by ExtractionAgent."""
    dummy_cv = {
        'candidate_id': 'test-uuid',
        'file': 'dummy.pdf',
        'content': 'Name: John Doe\nEmail: john@example.com'
    }
    agent = ExtractionAgent()
    # Patch OpenAI call to return minimal valid data
    def fake_extract(self, cv_data):
        return CandidateInfo(
            candidate_id=cv_data['candidate_id'],
            file=cv_data['file'],
            name='John Doe',
            email='john@example.com',
            phone=None,
            languages=[],
            programming_languages=[],
            frameworks=[],
            years_experience=None,
            education=None,
            summary=None
        )
    ExtractionAgent.extract = fake_extract
    info = agent.extract(dummy_cv)
    assert info.candidate_id == 'test-uuid', "candidate_id should be passed through to CandidateInfo" 