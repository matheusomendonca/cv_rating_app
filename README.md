# Analisador de CV

Um sistema multi-agente sofisticado que processa CVs de candidatos em PDF através de um pipeline inteligente para extrair, avaliar e julgar candidatos contra descrições de vagas. A aplicação usa agentes LLM da OpenAI para processamento inteligente e fornece tanto análise em tempo real quanto relatórios Excel abrangentes.

## 🏗️ Arquitetura Multi-Agente

A aplicação implementa um pipeline sofisticado de 5 agentes que processam CVs em paralelo para performance otimizada:

### 🤖 Visão Geral dos Agentes

1. **📄 Agente Parser** (`parser.py`)
   - Extrai texto bruto de CVs em PDF
   - Lida com múltiplos formatos e estruturas de PDF
   - Gera `candidate_id` único para cada CV
   - Executa em paralelo para processamento em lote

2. **🔍 Agente de Extração** (`agent_extraction.py`)
   - Usa OpenAI GPT-4 para extrair informações estruturadas do candidato
   - Identifica: nome, email, telefone, UF, cidade, idiomas, linguagens de programação, frameworks
   - Extrai anos de experiência, educação e resumo profissional
   - Retorna objetos `CandidateInfo` validados com estrutura de dados consistente

3. **⭐ Agente de Avaliação** (`agent_rating.py`)
   - Avalia candidatos contra descrições de vagas usando OpenAI
   - Fornece pontuações (0-10) com pontos fortes, fracos e justificativa detalhada
   - Considera habilidades técnicas, nível de experiência e adequação cultural
   - Analisa alinhamento de senioridade e correspondência de requisitos da vaga

4. **⚖️ Agente Juiz** (`agent_judge.py`)
   - **Controle de Qualidade Crítico**: Re-avalia todos os candidatos para justiça e consistência
   - Processa candidatos em lotes para garantir comparação relativa
   - Identifica inconsistências de avaliação entre o pool de candidatos
   - Fornece pontuações finais com explicações de ajuste
   - Garante padrões de avaliação imparciais e consistentes

5. **🔗 Agente Combinador** (`combiner.py`)
   - Mescla todas as saídas dos agentes em estruturas de dados unificadas
   - Lida com dados ausentes graciosamente com junções externas
   - Preserva identificação do candidato ao longo do pipeline
   - Prepara dados para apresentação final e exportação Excel

### 🔄 Fluxo do Pipeline

```
Upload de PDFs → Parser → Extrator → Avaliador → Juiz → Combinador → Relatório Excel
     ↓           ↓        ↓         ↓         ↓      ↓         ↓
  Processamento Processamento Processamento Chamadas Chamadas Mesclagem Saída
  Paralelo      Paralelo      Paralelo      LLM      LLM      de Dados Final
```

### ⚡ Recursos de Performance

- **Processamento Paralelo**: Todos os agentes executam simultaneamente usando ThreadPoolExecutor
- **Processamento em Lote**: Agente juiz processa candidatos em lotes configuráveis
- **Lógica de Retry**: Tratamento robusto de erros com retry automático para chamadas LLM
- **Acompanhamento de Progresso**: Barras de progresso e atualizações de status em tempo real
- **Gerenciamento de Memória**: Fluxo de dados eficiente com pegada de memória mínima

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.8+
- Chave da API OpenAI
- Bibliotecas de processamento de PDF

### Instalação

```bash
# 1. Clone o repositório
git clone <repository-url>
cd cv_rating_app

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure sua chave da API OpenAI
export OPENAI_API_KEY="sk-..."

# 4. Execute a aplicação Streamlit
streamlit run app.py
```

### Uso

1. **Upload de CVs**: Selecione múltiplos arquivos PDF contendo CVs de candidatos
2. **Descrição da Vaga**: Cole a descrição da vaga alvo na área de texto
3. **Processar**: Clique em "Processar" para iniciar o pipeline multi-agente
4. **Monitorar**: Acompanhe o progresso em tempo real conforme cada agente processa os dados
5. **Resultados**: Visualize a tabela final classificada e baixe o relatório Excel

## 🧪 Testes

```bash
# Instale as dependências de teste
pip install pytest

# Execute todos os testes
pytest

# Execute arquivos de teste específicos
pytest tests/test_parser.py
pytest tests/test_judge.py
pytest tests/test_combiner.py
```

## 📊 Formato de Saída

A saída final inclui:

- **Pontuação Final**: Avaliação ajustada pelo juiz (0-10)
- **Pontuação Inicial**: Avaliação original para comparação
- **Informações do Candidato**: Nome, email, telefone, UF, cidade, idiomas, habilidades
- **Pontos Fortes & Fracos**: Análise detalhada
- **Justificativa**: Explicação das decisões de avaliação
- **Ajuste de Pontuação**: Justificativa para quaisquer mudanças da pontuação inicial

## 🔧 Configuração

### Parâmetros dos Agentes

```python
# Agente de Extração
extractor = ExtractionAgent(model="gpt-4o-mini")

# Agente de Avaliação  
rater = RatingAgent(job_description, model="gpt-4o-mini")

# Agente Juiz
judge = JudgeAgent(job_description, model="gpt-4o-mini", batch_size=5)
```

### Ajuste de Performance

- **Trabalhadores de Thread**: Ajuste `max_workers` para processamento paralelo
- **Tamanho do Lote**: Configure o tamanho do lote do agente juiz para uso otimizado de LLM
- **Seleção de Modelo**: Escolha entre GPT-4, GPT-4o-mini ou outros modelos OpenAI

## 🛡️ Garantia de Qualidade

### Validação de Dados
- Todas as saídas dos agentes são validadas contra modelos Pydantic
- IDs de candidatos garantem integridade dos dados ao longo do pipeline
- Junções externas preservam todos os candidatos mesmo se alguns agentes falharem

### Tratamento de Erros
- Degradação graciosa quando agentes individuais falham
- Mecanismos de fallback para dados ausentes
- Logging abrangente e informações de debugging

### Justiça e Consistência
- Agente juiz garante consistência de avaliação entre todos os candidatos
- Detecção e remoção de viés no processamento
- Comparação relativa previne decisões de avaliação isoladas

## 📁 Estrutura do Projeto

```
cv_rating_app/
├── app.py                 # Aplicação principal Streamlit
├── parser.py              # Agente de parsing de PDF
├── agent_extraction.py    # Agente de extração de informações
├── agent_rating.py        # Agente de avaliação de candidatos
├── agent_judge.py         # Agente juiz para consistência
├── combiner.py            # Agente combinador de dados
├── formatter.py           # Formatação e exportação Excel
├── models.py              # Modelos de dados Pydantic
├── requirements.txt       # Dependências Python
├── README.md              # Documentação
└── tests/                 # Testes unitários e de integração
    ├── test_parser.py
    ├── test_judge.py
    └── test_combiner.py
```

## 🌟 Recursos Principais

### 📍 Informações de Localização
- Extração automática de UF (Estado) e cidade dos CVs
- Normalização de siglas de estados brasileiros
- Capitalização automática de nomes de cidades

### 🇧🇷 Localização em Português
- Interface completamente em português brasileiro
- Todas as saídas dos agentes em português
- Colunas da tabela final em português
- Relatórios Excel com cabeçalhos em português

### ⚡ Performance Otimizada
- Remoção do agente de limpeza para processamento mais rápido
- Processamento paralelo em todas as etapas
- Redução de ~25% no tempo de processamento

### 📊 Relatórios Completos
- Exportação Excel com formatação adequada
- Tratamento de caracteres especiais
- Fallback para CSV em caso de erro no Excel
- Preservação de todos os candidatos na saída final
