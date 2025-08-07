from cv_rating_app.models import CandidateInfo, CandidateRating, JudgeRating
from cv_rating_app.combiner import combine
from cv_rating_app.formatter import clean_text_for_excel

def test_combine():
    info = CandidateInfo(
        candidate_id="id1",
        file="a.pdf",
        name="Alice",
        email="alice@example.com",
        uf="SP",
        city="São Paulo",
        languages=["Python"],
        programming_languages=[],
        frameworks=[],
        years_experience=5,
        education=None,
        summary=None,
        phone=None
    )
    rating = CandidateRating(
        candidate_id="id1",
        file="a.pdf",
        score=90,
        strengths="Great Python skills",
        weaknesses="None",
        rationale=None
    )
    df = combine([info], [rating])
    assert df.iloc[0]["Pontuação Inicial"] == "90,0"  # Brazilian format with comma
    assert df.iloc[0]["Nome"] == "Alice"
    assert df.iloc[0]["Email"] == "alice@example.com"
    assert df.iloc[0]["UF"] == "SP"
    assert df.iloc[0]["Cidade"] == "São Paulo"
    assert "Python" in df.iloc[0]["Idiomas"]

def test_integration_final_candidate_count():
    """Integration test: number of final candidates matches input infos."""
    infos = [
        CandidateInfo(
            candidate_id=f"id{i}",
            file=f"cv_{i}.pdf",
            name=f"Name {i}",
            email=f"email{i}@example.com",
            languages=[],
            programming_languages=[],
            frameworks=[],
            years_experience=None,
            education=None,
            summary=None,
            phone=None
        ) for i in range(10)
    ]
    ratings = [
        CandidateRating(
            candidate_id=f"id{i}",
            file=f"cv_{i}.pdf",
            score=5.0 + i,
            strengths="",
            weaknesses="",
            rationale=""
        ) for i in range(10)
    ]
    judge_ratings = [
        JudgeRating(
            candidate_id=f"id{i}",
            file=f"cv_{i}.pdf",
            score=6.0 + i,
            strengths="",
            weaknesses="",
            rationale="",
            initial_score=5.0 + i,
            score_adjustment=""
        ) for i in range(10)
    ]
    df = combine(infos, ratings, judge_ratings).reset_index(drop=True)
    assert len(df) == len(infos), f"Expected {len(infos)} candidates, got {len(df)}"
    assert set(df['file']) == set(info.file for info in infos)

def test_single_file_column():
    """Test that there's only one 'file' column in the final output."""
    info = CandidateInfo(
        candidate_id="id1",
        file="test.pdf",
        name="Test User",
        email="test@example.com",
        languages=[],
        programming_languages=[],
        frameworks=[],
        years_experience=None,
        education=None,
        summary=None,
        phone=None
    )
    rating = CandidateRating(
        candidate_id="id1",
        file="test.pdf",
        score=85,
        strengths="Good skills",
        weaknesses="None",
        rationale="Good candidate"
    )
    judge_rating = JudgeRating(
        candidate_id="id1",
        file="test.pdf",
        score=87,
        strengths="Good skills",
        weaknesses="None",
        rationale="Good candidate",
        initial_score=85,
        score_adjustment="+2 points"
    )
    
    # Test with judge ratings
    df_with_judge = combine([info], [rating], [judge_rating])
    file_columns = [col for col in df_with_judge.columns if 'file' in col.lower()]
    assert len(file_columns) == 1, f"Expected 1 file column, got {len(file_columns)}: {file_columns}"
    assert 'file' in df_with_judge.columns, "Expected 'file' column to be present"
    
    # Test without judge ratings
    df_without_judge = combine([info], [rating])
    file_columns = [col for col in df_without_judge.columns if 'file' in col.lower()]
    assert len(file_columns) == 1, f"Expected 1 file column, got {len(file_columns)}: {file_columns}"
    assert 'file' in df_without_judge.columns, "Expected 'file' column to be present"

def test_special_character_cleaning():
    """Test that special characters are properly cleaned for Excel export."""
    # Test various special characters
    test_cases = [
        ("Sémela", "Semela"),
        ("José", "Jose"),
        ("François", "Francois"),
        ("João", "Joao"),
        ("Müller", "Muller"),
        ("Café", "Cafe"),
        ("Niño", "Nino"),
        ("", ""),  # Empty string
        (None, ""),  # None value
        ("Normal text", "Normal text"),  # Normal text unchanged
    ]
    
    for input_text, expected_output in test_cases:
        result = clean_text_for_excel(input_text)
        assert result == expected_output, f"Expected '{expected_output}', got '{result}' for input '{input_text}'"

def test_combine_edge_cases():
    """Test combine function with edge cases that could cause the ambiguous truth value error."""
    # Test with empty ratings list
    info = CandidateInfo(
        candidate_id="id1",
        file="test.pdf",
        name="Test User",
        email="test@example.com",
        languages=[],
        programming_languages=[],
        frameworks=[],
        years_experience=None,
        education=None,
        summary=None,
        phone=None
    )

    # This should not raise an error even with empty ratings
    df = combine([info], [])
    assert len(df) == 1, "Should have one row even with empty ratings"
    assert 'file' in df.columns, "Should have file column"
