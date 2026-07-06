# 2º Projeto - Curso Imersivo de IA - Proteus Academy
# Agente Inteligente de Monitoramento Educacional Global
Projeto prático desenvolvido para o Desafio do Acelera AI (Proteus Academy) focado na análise automatizada de indicadores do World Bank Education Statistics.

## 📊 Estrutura de Arquivos do Repositório
- `processa_dados.py`: Pipeline em Python com Pandas que realiza a limpeza de dados, o tratamento inteligente de valores nulos (via mediana histórica local e global) e computa rankings competitivos de evolução temporal.
- `EdStatsData.csv`: Tabela horizontal simulando a extração bruta do Kaggle com dados educacionais.
- `dados_tratados.csv`: Arquivo de saída unificado contendo os agregados e cálculos estruturados gerados pelo script.
- `workflow.json`: O workflow de orquestração visual construído e exportado do n8n Cloud.
- `skills/`: Diretório contendo a engenharia de prompts estruturada e versionada.

---

## 🛠️ Uso Efetivo da IA (Claude Code / Assistants)
O desenvolvimento deste projeto foi realizado sob a metodologia de desenvolvimento assistido por inteligência artificial (AI-Assisted Development), utilizando o Claude como um parceiro de pair programming. O modelo foi guiado através das seguintes etapas:

1. **Arquitetura do Pipeline:** O Claude auxiliou no desenho lógico do tratamento de dados esparsos (característicos do World Bank), sugerindo uma estratégia de pivoteamento dinâmico (função `.melt()` do Pandas) para transpor dados horizontais de anos para linhas de forma automatizada.
2. **Tratamento Inteligente de Nulos (Fallback Strategy):** Foram injetadas lógicas onde a IA sugeriu tratar valores ausentes iterativamente: primeiro calculando a mediana histórica do próprio país para o indicador e, caso persistisse o nulo, aplicando a mediana do indicador global naquele respectivo ano.
3. **Refatoração Pró-Token:** O Claude foi instruído a otimizar o agrupamento matemático do script principal para reduzir o tamanho do CSV final (`dados_tratados.csv`). Isso evitou o estouro do limite de contexto de tokens na API da OpenAI dentro do n8n.

---

## 🔢 Estrutura da Skill Versionada
Para cumprir a reutilização de capacidades exigida no edital, a inteligência e o comportamento do Agente de IA foram encapsulados e isolados abaixo para versionamento:

### Skill: Analista de Políticas Públicas Educacionais (World Bank Specialist)
- **Engine Utilizada:** OpenAI GPT-4o
- **Arquivo de Input Esperado:** Tabela agregada com métricas de crescimento e posições no ranking mundial (`dados_tratados.csv`).
- **Prompt de Sistema (System Message):**
  ```text
  Atue como um Especialista em Políticas Públicas de Educação do Banco Mundial. O usuário enviará um bloco de dados tratados de rankings de educação. Produza uma análise executiva estruturada em Markdown contendo de forma obrigatória: 1) Uma avaliação crítica profunda do desempenho do Brasil em comparação com potências econômicas e educacionais como Estados Unidos e Singapura; 2) Identificação explícita de cenários de estagnação ou evolução acelerada com base no crescimento percentual; 3) Três recomendações macroestratégicas direcionadas para os gestores públicos brasileiros com base nos insights. Use tom analítico, formal e corporativo.
