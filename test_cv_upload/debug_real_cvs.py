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
from parser import CVParser
from agent_extraction import ExtractionAgent
from agent_rating import RatingAgent
from agent_judge import JudgeAgent
from combiner import combine

# Load environment variables
load_dotenv()

def test_with_real_cvs():
    """Test the pipeline with real PDF CV files."""
    print("🚀 TESTING PIPELINE WITH REAL CV FILES")
    print("=" * 80)
    
    # Get the current directory (test_cv_upload)
    current_dir = Path(__file__).parent
    
    # Find all PDF files
    pdf_files = list(current_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files: {[f.name for f in pdf_files]}")
    
    if not pdf_files:
        print("❌ No PDF files found in test_cv_upload directory")
        return
    
    # Use the first PDF for testing
    test_pdf = pdf_files[0]
    print(f"\nTesting with: {test_pdf.name}")
    
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy the PDF to the temp directory
        import shutil
        temp_pdf = Path(tmpdir) / test_pdf.name
        shutil.copy2(test_pdf, temp_pdf)
        
        print(f"Copied {test_pdf.name} to {temp_pdf}")
        
        # Test 1: Parse the PDF
        print("\n" + "=" * 60)
        print("TESTING PDF PARSING")
        print("=" * 60)
        
        try:
            parser = CVParser(tmpdir)
            parsed_cvs = parser.parse(max_workers=1)
            
            if not parsed_cvs:
                print("❌ No CVs parsed from PDF")
                return
            
            cv_data = parsed_cvs[0]
            print(f"✅ PDF parsing successful!")
            print(f"File: {cv_data['file']}")
            print(f"Candidate ID: {cv_data['candidate_id']}")
            print(f"Content length: {len(cv_data['content'])} characters")
            print(f"Content preview: {cv_data['content'][:200]}...")
            
        except Exception as e:
            print(f"❌ PDF parsing failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 2: Extract information
        print("\n" + "=" * 60)
        print("TESTING EXTRACTION AGENT")
        print("=" * 60)
        
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
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 3: Rate the candidate
        print("\n" + "=" * 60)
        print("TESTING RATING AGENT")
        print("=" * 60)
        
        job_description = """
        Analista de Suporte I
        
        Requisitos:
        - Conhecimento em sistemas operacionais (Windows, Linux)
        - Experiência com atendimento ao cliente
        - Conhecimento básico em redes e infraestrutura
        - Boa comunicação e trabalho em equipe
        - Capacidade de resolução de problemas
        
        Responsabilidades:
        - Atendimento ao cliente via telefone, email e chat
        - Resolução de problemas técnicos de nível 1
        - Suporte a aplicações e sistemas
        - Documentação de procedimentos
        - Participação em projetos de melhoria
        """
        
        try:
            rater = RatingAgent(job_description)
            rating = rater.rate(candidate_info)
            
            print(f"✅ Rating successful!")
            print(f"Score: {rating.score}")
            print(f"Strengths: {rating.strengths}")
            print(f"Weaknesses: {rating.weaknesses}")
            print(f"Rationale: {rating.rationale}")
            
        except Exception as e:
            print(f"❌ Rating failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 4: Judge the candidate
        print("\n" + "=" * 60)
        print("TESTING JUDGE AGENT")
        print("=" * 60)
        
        try:
            judge = JudgeAgent(job_description, batch_size=1)
            
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
                
                # Check if judge fell back to original rating
                if "erro de processamento" in judge_rating.score_adjustment.lower():
                    print("⚠️  WARNING: Judge agent fell back to original rating!")
                    print("   This indicates the judge agent encountered an error")
                else:
                    print("✅ Judge agent worked properly!")
                
            else:
                print(f"❌ Judge returned empty results")
                return None
                
        except Exception as e:
            print(f"❌ Judge failed: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # Test 5: Combine results
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
    """Run the test with real CV files."""
    test_with_real_cvs()

if __name__ == "__main__":
    main() 