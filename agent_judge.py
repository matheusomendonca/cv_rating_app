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
        """Judge a batch of candidates for fairness and consistency."""
        
        # Create a detailed prompt for the batch
        candidates_info = []
        for i, (candidate, rating) in enumerate(zip(candidates, ratings)):
            candidate_info = f"""
            CANDIDATO {i+1}:
            Nome: {candidate.name}
            Email: {candidate.email}
            UF: {candidate.uf or 'Não fornecido'}
            Cidade: {candidate.city or 'Não fornecida'}
            Idiomas: {', '.join(candidate.languages) if candidate.languages else 'Não especificado'}
            Linguagens de Programação: {', '.join(candidate.programming_languages) if candidate.programming_languages else 'Não especificado'}
            Frameworks: {', '.join(candidate.frameworks) if candidate.frameworks else 'Não especificado'}
            Anos de Experiência: {candidate.years_experience or 'Não especificado'}
            Educação: {candidate.education or 'Não especificado'}
            Resumo: {candidate.summary or 'Não fornecido'}
            Pontuação Inicial: {rating.score}
            Pontos Fortes: {rating.strengths or 'Não especificado'}
            Pontos Fracos: {rating.weaknesses or 'Não especificado'}
            Justificativa: {rating.rationale or 'Não especificado'}
            """
            candidates_info.append(candidate_info)
        
        prompt = f"""
        Você é um juiz especializado em recrutamento técnico. Sua tarefa é re-avaliar um grupo de candidatos para garantir justiça e consistência nas avaliações.

        Valores da Empresa (considere estes em sua avaliação):
        - SIMPLICIDADE, CLAREZA E OBJETIVIDADE
        - PESSOAS COMO FOCO E FONTE DAS TRANSFORMAÇÕES
        - RELAÇÕES DE LONGO PRAZO
        - EXCELÊNCIA
        - INOVAÇÃO CONTÍNUA (2019)
        - CORAGEM PARA INOVAR (2022)
        - RESPEITO À NATUREZA E

        Descrição da Vaga:
        {self.job_description}

        Candidatos para Re-avaliação:
        {chr(10).join(candidates_info)}

        Instruções:
        1. Compare todos os candidatos entre si para garantir consistência
        2. Ajuste pontuações se necessário para refletir diferenças reais
        3. Considere o contexto completo de cada candidato
        4. Mantenha a escala de 0-10
        5. Forneça justificativas claras para qualquer ajuste

        IMPORTANTE: Retorne um array JSON com exatamente {len(candidates)} objetos, um para cada candidato na mesma ordem.

        Formato de resposta OBRIGATÓRIO:
        [
            {{
                "score": 8.5,
                "strengths": "Pontos fortes do candidato 1",
                "weaknesses": "Pontos fracos do candidato 1",
                "rationale": "Justificativa da pontuação do candidato 1",
                "score_adjustment": "Explicação do ajuste (se houver)"
            }},
            {{
                "score": 7.0,
                "strengths": "Pontos fortes do candidato 2",
                "weaknesses": "Pontos fracos do candidato 2",
                "rationale": "Justificativa da pontuação do candidato 2",
                "score_adjustment": "Explicação do ajuste (se houver)"
            }}
        ]

        ATENÇÃO: Use exatamente estes nomes de campos: "score", "strengths", "weaknesses", "rationale", "score_adjustment"
        """

        # Retry logic for LLM calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Você é um juiz especializado em recrutamento técnico. Re-avalie candidatos para garantir justiça e consistência. Retorne sempre as avaliações em português brasileiro. IMPORTANTE: Retorne sempre um array JSON com exatamente o número de candidatos fornecido."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )
                
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("No content received from OpenAI")
                
                data = json.loads(content)
                
                # Parse the response - handle different formats
                ratings_array = []
                if isinstance(data, list):
                    ratings_array = data
                elif isinstance(data, dict) and 'ratings' in data:
                    ratings_array = data['ratings']
                elif isinstance(data, dict) and 'candidatos' in data:
                    ratings_array = data['candidatos']
                elif isinstance(data, dict):
                    # Single rating case
                    ratings_array = [data]
                else:
                    raise ValueError(f"Unexpected response format: {type(data)}")
                
                # Validate we got the right number of ratings
                if len(ratings_array) != len(candidates):
                    print(f"Warning: Expected {len(candidates)} ratings, got {len(ratings_array)}")
                    # Fallback: use original ratings
                    judge_ratings = []
                    for i, (candidate, rating) in enumerate(zip(candidates, ratings)):
                        judge_ratings.append(JudgeRating(
                            candidate_id=candidate.candidate_id,
                            file=candidate.file,
                            score=rating.score,
                            strengths=rating.strengths,
                            weaknesses=rating.weaknesses,
                            rationale=rating.rationale,
                            initial_score=rating.score,
                            score_adjustment="Avaliação original mantida devido a erro de processamento"
                        ))
                    return judge_ratings
                
                # Process the ratings
                judge_ratings = []
                for i, (rating_data, candidate, rating) in enumerate(zip(ratings_array, candidates, ratings)):
                    try:
                        rating_data = rating_data.copy()  # Make a copy
                        rating_data.pop('file', None)  # Remove file to avoid duplicate
                        
                        # Ensure all required fields are present
                        if 'score' not in rating_data:
                            rating_data['score'] = rating.score
                        else:
                            # Ensure score is numeric
                            try:
                                rating_data['score'] = float(rating_data['score'])
                            except (ValueError, TypeError):
                                print(f"Warning: Invalid score value '{rating_data['score']}' for candidate {candidate.name}, using original score")
                                rating_data['score'] = rating.score
                                
                        if 'strengths' not in rating_data:
                            rating_data['strengths'] = rating.strengths
                        if 'weaknesses' not in rating_data:
                            rating_data['weaknesses'] = rating.weaknesses
                        if 'rationale' not in rating_data:
                            rating_data['rationale'] = rating.rationale
                        if 'score_adjustment' not in rating_data:
                            rating_data['score_adjustment'] = "Sem ajuste necessário"
                        
                        judge_rating = JudgeRating(
                            candidate_id=candidate.candidate_id,
                            file=candidate.file,
                            initial_score=rating.score,
                            **rating_data
                        )
                        
                        judge_ratings.append(judge_rating)
                    except Exception as e:
                        print(f"Error processing rating {i}: {e}")
                        # Fallback to original rating
                        judge_ratings.append(JudgeRating(
                            candidate_id=candidate.candidate_id,
                            file=candidate.file,
                            score=rating.score,
                            strengths=rating.strengths,
                            weaknesses=rating.weaknesses,
                            rationale=rating.rationale,
                            initial_score=rating.score,
                            score_adjustment="Avaliação original mantida devido a erro de processamento"
                        ))
                
                return judge_ratings
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    # Final fallback: return original ratings
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
                            score_adjustment="Avaliação original mantida devido a erro de processamento"
                        ))
                    return judge_ratings
                else:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff 