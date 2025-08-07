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
        Você é um recrutador técnico da Enacom Group, uma empresa que desenvolve softwares baseados em otimização, machine learning e ciência de dados. 
        
        Valores da Empresa (considere estes em sua avaliação):
        - SIMPLICIDADE, CLAREZA E OBJETIVIDADE
        - PESSOAS COMO FOCO E FONTE DAS TRANSFORMAÇÕES
        - RELAÇÕES DE LONGO PRAZO
        - EXCELÊNCIA
        - INOVAÇÃO CONTÍNUA (2019)
        - CORAGEM PARA INOVAR (2022)
        - RESPEITO À NATUREZA E
        
        Com base na descrição da vaga abaixo, avalie o candidato em uma escala de 0-10 e forneça pontos fortes, pontos fracos e uma justificativa curta.

        Para criar uma pontuação, considere o seguinte:
        - A experiência e habilidades do candidato em relação à descrição da vaga
        - As linguagens de programação e frameworks do candidato em relação à descrição da vaga
        - A educação e certificações do candidato em relação à descrição da vaga
        - As habilidades comportamentais do candidato em relação à descrição da vaga
        - A personalidade do candidato e adequação à cultura da empresa
        - O alinhamento do candidato com os valores da empresa acima
        
        Também infira o nível de senioridade necessário para a vaga e o nível de experiência do candidato em relação à descrição da vaga.

        Tenha cuidado com o seguinte:
        - Um candidato júnior para uma posição sênior não é uma boa adequação.
        - Um candidato sênior para uma posição júnior não é uma boa adequação.
        - Um candidato sem experiência para uma posição sênior não é uma boa adequação.
        - Um candidato sem experiência para uma posição júnior é uma boa adequação.
        - Um candidato sem experiência para uma posição de nível médio não é uma boa adequação.
        - Um candidato sem experiência para uma posição sênior não é uma boa adequação.
        
        Descrição da vaga:
        {self.job_description}
        
        Informações do candidato:
        Nome: {candidate.name}
        Email: {candidate.email}
        Telefone: {candidate.phone or 'Não fornecido'}
        UF: {candidate.uf or 'Não fornecido'}
        Cidade: {candidate.city or 'Não fornecida'}
        Idiomas: {', '.join(candidate.languages) if candidate.languages else 'Não especificado'}
        Linguagens de Programação: {', '.join(candidate.programming_languages) if candidate.programming_languages else 'Não especificado'}
        Frameworks: {', '.join(candidate.frameworks) if candidate.frameworks else 'Não especificado'}
        Anos de Experiência: {candidate.years_experience or 'Não especificado'}
        Educação: {candidate.education or 'Não especificado'}
        Resumo: {candidate.summary or 'Não fornecido'}
        
        Retorne um JSON com os seguintes campos:
        {{
            "score": "float - pontuação de 0 a 10",
            "strengths": "string - pontos fortes do candidato em português",
            "weaknesses": "string - pontos fracos do candidato em português", 
            "rationale": "string - justificativa da pontuação em português"
        }}
        """
        
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Você é um recrutador técnico especializado. Avalie candidatos com base na descrição da vaga e retorne a avaliação em português brasileiro. Forneça pontuações justas e justificativas detalhadas."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("No content received from OpenAI")
        
        obj = json.loads(content)
        
        # Ensure score is numeric
        if 'score' in obj:
            try:
                obj['score'] = float(obj['score'])
            except (ValueError, TypeError):
                print(f"Warning: Invalid score value '{obj['score']}' for candidate {candidate.name}, using 0.0")
                obj['score'] = 0.0
        
        return CandidateRating(candidate_id=candidate.candidate_id, file=candidate.file, **obj)
