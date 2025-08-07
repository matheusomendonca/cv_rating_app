#!/usr/bin/env python3

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from models import CandidateInfo, CandidateRating, JudgeRating
from agent_extraction import ExtractionAgent
from agent_rating import RatingAgent
from agent_judge import JudgeAgent
from combiner import combine

# Load environment variables
load_dotenv()

def test_extraction_agent():
    """Test the extraction agent with sample CV data."""
    print("=" * 60)
    print("TESTING EXTRACTION AGENT")
    print("=" * 60)
    
    # Read the sample CV
    with open("sample_cv.txt", "r", encoding="utf-8") as f:
        cv_content = f.read()
    
    cv_data = {
        "candidate_id": "test_001",
        "file": "sample_cv.txt",
        "content": cv_content
    }
    
    try:
        extractor = ExtractionAgent()
        candidate_info = extractor.extract(cv_data)
        
        print(f"✅ Extraction successful!")
        print(f"Name: {candidate_info.name}")
        print(f"Email: {candidate_info.email}")
        print(f"Phone: {candidate_info.phone}")
        print(f"UF: {candidate_info.uf}")
        print(f"City: {candidate_info.city}")
        print(f"Languages: {candidate_info.languages}")
        print(f"Programming Languages: {candidate_info.programming_languages}")
        print(f"Frameworks: {candidate_info.frameworks}")
        print(f"Years Experience: {candidate_info.years_experience}")
        print(f"Education: {candidate_info.education}")
        print(f"Summary: {candidate_info.summary}")
        
        return candidate_info
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_rating_agent(candidate_info):
    """Test the rating agent with the extracted candidate info."""
    print("\n" + "=" * 60)
    print("TESTING RATING AGENT")
    print("=" * 60)
    
    job_description = """
    Desenvolvedor Full-Stack Sênior
    
    Requisitos:
    - 5+ anos de experiência em desenvolvimento web
    - Conhecimento avançado em Python e JavaScript
    - Experiência com frameworks como Django, Flask, React, Node.js
    - Conhecimento em bancos de dados (PostgreSQL, MongoDB)
    - Experiência com APIs RESTful
    - Conhecimento em Docker e cloud (AWS/GCP)
    - Boa comunicação e trabalho em equipe
    - Liderança técnica e mentoria
    
    Responsabilidades:
    - Desenvolvimento de aplicações web complexas
    - Arquitetura de sistemas escaláveis
    - Liderança técnica de equipes
    - Code review e mentoria de desenvolvedores
    - Participação em decisões técnicas
    """
    
    try:
        rater = RatingAgent(job_description)
        rating = rater.rate(candidate_info)
        
        print(f"✅ Rating successful!")
        print(f"Score: {rating.score}")
        print(f"Strengths: {rating.strengths}")
        print(f"Weaknesses: {rating.weaknesses}")
        print(f"Rationale: {rating.rationale}")
        
        return rating
        
    except Exception as e:
        print(f"❌ Rating failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_judge_agent(candidate_info, rating):
    """Test the judge agent with the candidate info and rating."""
    print("\n" + "=" * 60)
    print("TESTING JUDGE AGENT")
    print("=" * 60)
    
    job_description = """
    Desenvolvedor Full-Stack Sênior
    
    Requisitos:
    - 5+ anos de experiência em desenvolvimento web
    - Conhecimento avançado em Python e JavaScript
    - Experiência com frameworks como Django, Flask, React, Node.js
    - Conhecimento em bancos de dados (PostgreSQL, MongoDB)
    - Experiência com APIs RESTful
    - Conhecimento em Docker e cloud (AWS/GCP)
    - Boa comunicação e trabalho em equipe
    - Liderança técnica e mentoria
    
    Responsabilidades:
    - Desenvolvimento de aplicações web complexas
    - Arquitetura de sistemas escaláveis
    - Liderança técnica de equipes
    - Code review e mentoria de desenvolvedores
    - Participação em decisões técnicas
    """
    
    try:
        judge = JudgeAgent(job_description, batch_size=1)  # Process one at a time for debugging
        
        print(f"Testing judge with 1 candidate...")
        judge_ratings = judge._judge_batch([candidate_info], [rating])
        
        if judge_ratings:
            judge_rating = judge_ratings[0]
            print(f"✅ Judge successful!")
            print(f"Final Score: {judge_rating.score}")
            print(f"Initial Score: {judge_rating.initial_score}")
            print(f"Strengths: {judge_rating.strengths}")
            print(f"Weaknesses: {judge_rating.weaknesses}")
            print(f"Rationale: {judge_rating.rationale}")
            print(f"Score Adjustment: {judge_rating.score_adjustment}")
            
            return judge_ratings
        else:
            print(f"❌ Judge returned empty results")
            return None
            
    except Exception as e:
        print(f"❌ Judge failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_combiner(candidate_info, rating, judge_ratings):
    """Test the combiner with all the data."""
    print("\n" + "=" * 60)
    print("TESTING COMBINER")
    print("=" * 60)
    
    try:
        df = combine([candidate_info], [rating], judge_ratings)
        
        print(f"✅ Combiner successful!")
        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        if len(df) > 0:
            row = df.iloc[0]
            print(f"\nFinal Results:")
            print(f"File: {row['file']}")
            print(f"Pontuação Final: {row.get('Pontuação Final', 'N/A')}")
            print(f"Pontuação Inicial: {row.get('Pontuação Inicial', 'N/A')}")
            print(f"Nome: {row.get('Nome', 'N/A')}")
            print(f"Email: {row.get('Email', 'N/A')}")
            print(f"UF: {row.get('UF', 'N/A')}")
            print(f"Cidade: {row.get('Cidade', 'N/A')}")
            print(f"Pontos Fortes: {row.get('Pontos Fortes', 'N/A')}")
            print(f"Pontos Fracos: {row.get('Pontos Fracos', 'N/A')}")
            print(f"Justificativa: {row.get('Justificativa', 'N/A')}")
            print(f"Ajuste de Pontuação: {row.get('Ajuste de Pontuação', 'N/A')}")
        
        return df
        
    except Exception as e:
        print(f"❌ Combiner failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run the complete pipeline test."""
    print("🚀 STARTING COMPLETE PIPELINE DEBUG TEST")
    print("=" * 80)
    
    # Test 1: Extraction
    candidate_info = test_extraction_agent()
    if not candidate_info:
        print("❌ Pipeline failed at extraction step")
        return
    
    # Test 2: Rating
    rating = test_rating_agent(candidate_info)
    if not rating:
        print("❌ Pipeline failed at rating step")
        return
    
    # Test 3: Judge
    judge_ratings = test_judge_agent(candidate_info, rating)
    if not judge_ratings:
        print("❌ Pipeline failed at judge step")
        return
    
    # Test 4: Combiner
    df = test_combiner(candidate_info, rating, judge_ratings)
    if df is None:
        print("❌ Pipeline failed at combiner step")
        return
    
    print("\n" + "=" * 80)
    print("🎉 COMPLETE PIPELINE TEST SUCCESSFUL!")
    print("=" * 80)
    
    # Check if judge worked properly
    if len(df) > 0:
        ajuste = df.iloc[0].get('Ajuste de Pontuação', '')
        if 'erro de processamento' in ajuste.lower():
            print("⚠️  WARNING: Judge agent fell back to original rating")
            print("   This indicates the judge agent encountered an error")
        else:
            print("✅ Judge agent worked properly!")

if __name__ == "__main__":
    main() 