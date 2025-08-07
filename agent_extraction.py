import os, json
import openai
from dotenv import load_dotenv
from typing import Dict
from models import CandidateInfo

class ExtractionAgent:
    """Agent that extracts structured candidate info using OpenAI."""

    def __init__(self, model: str = "gpt-4o-mini"):
        load_dotenv(override=True)
        self.model = model
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def extract(self, cv_data: Dict) -> CandidateInfo:
        prompt = f"""Extraia as seguintes informações do candidato do texto do CV abaixo e retorne como um objeto JSON com estes campos exatos:

        {{
            "name": "string - nome completo",
            "email": "string - endereço de email principal", 
            "phone": "string ou null - número de telefone se disponível",
            "uf": "string ou null - sigla do estado brasileiro (SP, RJ, MG, etc.)",
            "city": "string ou null - nome da cidade",
            "languages": ["array de strings - apenas nomes dos idiomas falados"],
            "programming_languages": ["array de strings - apenas nomes das linguagens de programação"],
            "frameworks": ["array de strings - apenas nomes dos frameworks"],
            "years_experience": "integer ou null - total de anos de experiência",
            "education": "string ou null - resumo da educação (diploma, instituição, ano)",
            "summary": "string ou null - resumo profissional"
        }}

        Importante:
        - Para idiomas: retorne apenas nomes dos idiomas como strings, não objetos
        - Para linguagens de programação: retorne apenas nomes das linguagens como strings, não objetos
        - Para frameworks: retorne apenas nomes dos frameworks como strings, não objetos
        - Para educação: forneça um resumo conciso, não objetos detalhados
        - Para anos de experiência: retorne apenas o número, não texto
        - Para email: retorne apenas o email principal, não uma lista
        - Para UF: retorne apenas a sigla do estado brasileiro (ex: SP, RJ, MG, RS, etc.)
        - Para cidade: retorne apenas o nome da cidade

        TEXTO DO CV:
        {cv_data['content']}
        """
        
        # Create a simplified schema for extraction that matches our model
        extraction_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nome completo do candidato"},
                "email": {"type": "string", "description": "Endereço de email principal"},
                "phone": {"type": ["string", "null"], "description": "Número de telefone se disponível"},
                "uf": {"type": ["string", "null"], "description": "Sigla do estado brasileiro"},
                "city": {"type": ["string", "null"], "description": "Nome da cidade"},
                "languages": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "Lista de idiomas que o candidato conhece"
                },
                "programming_languages": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "Lista de linguagens de programação que o candidato conhece"
                },
                "frameworks": { 
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "Lista de frameworks que o candidato conhece"
                },
                "years_experience": {
                    "type": ["integer", "null"], 
                    "description": "Total de anos de experiência profissional"
                },
                "education": {
                    "type": ["string", "null"], 
                    "description": "Resumo da educação (diploma, instituição, ano)"
                },
                "summary": {
                    "type": ["string", "null"], 
                    "description": "Resumo profissional ou objetivo"
                }
            },
            "required": ["name", "email"]
        }
        
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Você é um assistente de RH especializado. Extraia informações do candidato e retorne na estrutura JSON exata especificada. Para idiomas, retorne apenas nomes dos idiomas como strings. Para educação, forneça um resumo conciso. Para anos_experience, retorne apenas o número. Para UF, retorne apenas a sigla do estado brasileiro. Para cidade, retorne apenas o nome da cidade."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("No content received from OpenAI")
        data = json.loads(content)
        
        # Minimal post-processing since structured output should handle most cases
        # Handle languages field - ensure it's always a list
        if not isinstance(data.get('languages'), list):
            if data.get('languages') is None:
                data['languages'] = []
            elif isinstance(data.get('languages'), dict):
                data['languages'] = list(data['languages'].keys())
            else:
                data['languages'] = [str(data['languages'])]
        
        # Handle programming_languages field - ensure it's always a list    
        if not isinstance(data.get('programming_languages'), list):
            if data.get('programming_languages') is None:
                data['programming_languages'] = []
            elif isinstance(data.get('programming_languages'), dict):
                data['programming_languages'] = list(data['programming_languages'].keys())
            else:
                data['programming_languages'] = [str(data['programming_languages'])]

        # Handle frameworks field - ensure it's always a list
        if not isinstance(data.get('frameworks'), list):
            if data.get('frameworks') is None:
                data['frameworks'] = []
            elif isinstance(data.get('frameworks'), dict):
                data['frameworks'] = list(data['frameworks'].keys())
            else:
                data['frameworks'] = [str(data['frameworks'])]

        # Handle years_experience - ensure it's an integer or None
        if isinstance(data.get('years_experience'), str):
            import re
            numbers = re.findall(r'\d+', data['years_experience'])
            if numbers:
                data['years_experience'] = int(numbers[0])
            else:
                data['years_experience'] = None
        
        # Handle UF - normalize Brazilian state abbreviations
        if data.get('uf'):
            uf = str(data['uf']).strip().upper()
            # Common Brazilian state abbreviations
            brazilian_states = {
                'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
                'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
                'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
            }
            if uf in brazilian_states:
                data['uf'] = uf
            else:
                data['uf'] = None
        
        # Handle city - normalize city names
        if data.get('city'):
            city = str(data['city']).strip()
            if city and len(city) > 0:
                data['city'] = city.title()  # Capitalize first letter of each word
            else:
                data['city'] = None
        
        # Ensure required fields have defaults
        if data.get('name') is None:
            data['name'] = "Desconhecido"
        if data.get('email') is None:
            data['email'] = "Email não fornecido"
        
        return CandidateInfo(candidate_id=cv_data['candidate_id'], file=cv_data['file'], **data)
