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

def test_multiple_cvs():
    """Test the pipeline with multiple real PDF CV files."""
    print("🚀 TESTING PIPELINE WITH MULTIPLE REAL CV FILES")
    print("=" * 80)
    
    # Get the current directory (test_cv_upload)
    current_dir = Path(__file__).parent
    
    # Find all PDF files
    pdf_files = list(current_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files: {[f.name for f in pdf_files]}")
    
    if not pdf_files:
        print("❌ No PDF files found in test_cv_upload directory")
        return
    
    # Use the first 3 PDFs for testing
    test_pdfs = pdf_files[:3]
    print(f"\nTesting with: {[f.name for f in test_pdfs]}")
    
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy the PDFs to the temp directory
        import shutil
        for pdf_file in test_pdfs:
            temp_pdf = Path(tmpdir) / pdf_file.name
            shutil.copy2(pdf_file, temp_pdf)
            print(f"Copied {pdf_file.name} to {temp_pdf}")
        
        # Test 1: Parse all PDFs
        print("\n" + "=" * 60)
        print("TESTING PDF PARSING")
        print("=" * 60)
        
        try:
            parser = CVParser(tmpdir)
            parsed_cvs = parser.parse(max_workers=3)
            
            if not parsed_cvs:
                print("❌ No CVs parsed from PDFs")
                return
            
            print(f"✅ PDF parsing successful! Parsed {len(parsed_cvs)} CVs")
            for cv in parsed_cvs:
                print(f"  - {cv['file']}: {len(cv['content'])} characters")
            
        except Exception as e:
            print(f"❌ PDF parsing failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 2: Extract information from all CVs
        print("\n" + "=" * 60)
        print("TESTING EXTRACTION AGENT")
        print("=" * 60)
        
        candidate_infos = []
        try:
            extractor = ExtractionAgent()
            for cv_data in parsed_cvs:
                candidate_info = extractor.extract(cv_data)
                candidate_infos.append(candidate_info)
                print(f"✅ Extracted: {candidate_info.name} ({candidate_info.email})")
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 3: Rate all candidates
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
        
        ratings = []
        try:
            rater = RatingAgent(job_description)
            for candidate_info in candidate_infos:
                rating = rater.rate(candidate_info)
                ratings.append(rating)
                print(f"✅ Rated: {candidate_info.name} - Score: {rating.score}")
            
        except Exception as e:
            print(f"❌ Rating failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 4: Judge all candidates
        print("\n" + "=" * 60)
        print("TESTING JUDGE AGENT")
        print("=" * 60)
        
        try:
            judge = JudgeAgent(job_description, batch_size=2)  # Test with batch size 2
            
            print(f"Testing judge with {len(candidate_infos)} candidates in batches...")
            judge_ratings = judge.judge_all(candidate_infos, ratings, max_workers=2)
            
            if judge_ratings:
                print(f"✅ Judge successful! Processed {len(judge_ratings)} candidates")
                
                # Check each judge rating
                error_count = 0
                for i, judge_rating in enumerate(judge_ratings):
                    print(f"\nCandidate {i+1}: {judge_rating.file}")
                    print(f"  Final Score: {judge_rating.score}")
                    print(f"  Initial Score: {judge_rating.initial_score}")
                    print(f"  Score Adjustment: {judge_rating.score_adjustment}")
                    
                    # Check if judge fell back to original rating
                    if "erro de processamento" in judge_rating.score_adjustment.lower():
                        print("  ⚠️  WARNING: Judge agent fell back to original rating!")
                        error_count += 1
                    else:
                        print("  ✅ Judge agent worked properly!")
                
                print(f"\nSummary: {error_count} out of {len(judge_ratings)} candidates had judge errors")
                
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
            df = combine(candidate_infos, ratings, judge_ratings)
            
            print(f"✅ Combiner successful!")
            print(f"DataFrame shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            
            if len(df) > 0:
                print(f"\nFinal Results Summary:")
                for i, row in df.iterrows():
                    print(f"\nRow {i+1}:")
                    print(f"  File: {row['file']}")
                    print(f"  Pontuação Final: {row.get('Pontuação Final', 'N/A')}")
                    print(f"  Pontuação Inicial: {row.get('Pontuação Inicial', 'N/A')}")
                    print(f"  Nome: {row.get('Nome', 'N/A')}")
                    print(f"  Ajuste de Pontuação: {row.get('Ajuste de Pontuação', 'N/A')}")
                    
                    # Check for error messages
                    ajuste = row.get('Ajuste de Pontuação', '')
                    if "erro de processamento" in ajuste.lower():
                        print(f"  ⚠️  ERROR: Judge agent failed for this candidate!")
            
            return df
            
        except Exception as e:
            print(f"❌ Combiner failed: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Run the test with multiple real CV files."""
    test_multiple_cvs()

if __name__ == "__main__":
    main() 