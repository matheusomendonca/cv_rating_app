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

def test_with_user_job_description():
    """Test the pipeline with the user's exact job description."""
    print("🚀 TESTING PIPELINE WITH USER'S JOB DESCRIPTION")
    print("=" * 80)
    
    # Get the current directory (test_cv_upload)
    current_dir = Path(__file__).parent
    
    # Find all PDF files
    pdf_files = list(current_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files: {[f.name for f in pdf_files]}")
    
    if not pdf_files:
        print("❌ No PDF files found in test_cv_upload directory")
        return
    
    # Use all PDFs for testing
    test_pdfs = pdf_files
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
            parsed_cvs = parser.parse(max_workers=8)
            
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
        
        # Use the user's exact job description
        job_description = """
        Analista de Suporte ao Cliente 

        Somos a Enacom Group, uma empresa com foco em Gêmeos Digitais, otimização e impacto na indústria. Estamos há mais de 15 anos no mercado como pioneira em tecnologia de ponta e queremos convidar você para fazer parte dessa história com a gente!  

        Nosso time está crescendo! Estamos em busca de Analista de Suporte I, que junto ao time de Sustentação será responsável por apoiar a manutenção dos projetos em etapa de pós projeto.  

        Esse é um trabalho para pessoas que tenham: 

        - Boa comunicação verbal e escrita 

        - Proatividade 

        - Boa capacidade analítica 

        - Habilidades para resolução de problemas  

        - Graduação em cursos de TI ou afins.  

        Desejável conhecimento em: 

        - Sistemas web/nuvem 

        - Atendimento de Suporte N1 e N2 

        - Ferramentas de help-desk (Service Now ou outra)  

        Durante seu trabalho na Enacom, suas responsabilidades principais serão: 

        - Atendimento ao usuário final 

        - Garantir o registro dos chamados de forma correta 

        - Garantir a resolução dos tickets com apoio da base de conhecimento 

        - Garantir o SLA de atendimento e comunicação constante com os usuários 

        - Acompanhamento de filas de chamados 

        - Registro das intercorrências, documentação e evidência dos atendimentos 

        E para isso oferecemos as seguintes condições e benefícios:  

        Trabalho Home Office + auxílio + equipamentos – Temos gente de todo lugar do mundo em nossa empresa!  

        Carga horária reduzida – Escolha o ritmo com as possibilidades de jornada reduzida!  

        Cultura ágil - Projetos dinâmicos e aprendizado contínuo.  

        Eventos de integração e Mimos – Tenha amigos em todos os cantos por meio de nossas dinâmicas exclusivas de formação de laços #SangueAzul! 

        Day Off de aniversário + presente exclusivo – Seu dia é especial para nós!  

        Vale alimentação e refeição - Tenha um cartão para uso em mercados e restaurantes! 

        Plano de saúde 100% pago pela empresa + Programas de saúde mental internos! 

        Seguro de via 100% pago pela empresa!  

        Plano de carreira + Mentoria e orientação em programas de acompanhamento de carreira! 

        Apoio para novos papais e mamães + Auxílio creche para os pequenos!   

        Deu Match? Se inscreva entraremos em contato por e-mail! 

        Roteiro de perguntas 

        Como você prioriza seus chamados quando tem múltiplos tickets abertos com prazos próximos? 

        Você já sugeriu melhorias em processos de suporte com base em análise de dados? Conte-me sobre isso. 

        Descreva um momento em que você identificou um problema antes que ele afetasse os usuários. O que você fez? 

        Conte-me sobre uma situação em que você precisou explicar um problema técnico complexo para alguém sem conhecimento técnico. Como você fez? 

        Como você documentaria uma solução para incluir na base de conhecimento? 

        O que você faz quando um chamado está prestes a vencer o prazo e ainda não tem solução? 

        Qual sua experiência com trabalho em equipe em ambientes de suporte? 

        Qual seu objetivo de carreira?
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
        
        # Test 4: Judge all candidates with Streamlit configuration
        print("\n" + "=" * 60)
        print("TESTING JUDGE AGENT (USER'S JOB DESCRIPTION)")
        print("=" * 60)
        
        try:
            # Use exact same configuration as Streamlit app
            judge = JudgeAgent(job_description, batch_size=5)  # batch_size=5 like Streamlit
            
            print(f"Testing judge with {len(candidate_infos)} candidates in batches of 5...")
            print(f"Using max_workers=4 like Streamlit app...")
            
            # Create a simple progress callback like Streamlit
            def update_judge_progress(progress, status_text):
                print(f"Judge Progress: {progress:.1%} - {status_text}")
            
            judge_ratings = judge.judge_all(candidate_infos, ratings, progress_callback=update_judge_progress, max_workers=4)
            
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
                error_count = 0
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
                        error_count += 1
                
                print(f"\nFinal Summary: {error_count} out of {len(df)} candidates had judge errors")
                
                if error_count > 0:
                    print("\n🔍 ISSUE FOUND!")
                    print("The judge agent is failing with your specific job description.")
                    print("This might be due to:")
                    print("1. Job description length/complexity")
                    print("2. Special characters or formatting")
                    print("3. Content that confuses the LLM")
                else:
                    print("\n✅ NO ISSUE FOUND!")
                    print("The judge agent works correctly with your job description.")
                    print("The issue might be in the Streamlit environment.")
            
            return df
            
        except Exception as e:
            print(f"❌ Combiner failed: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Run the test with user's job description."""
    test_with_user_job_description()

if __name__ == "__main__":
    main() 