"""
Script de Análise: World Bank Education Statistics
Autor: Engenheiro de Dados Sênior (via Claude)
Objetivo: Limpar, selecionar indicadores, calcular crescimento/rankings
          e exportar um CSV tratado.

ESTRUTURA ESPERADA DO ARQUIVO DE ENTRADA
-----------------------------------------
Este script assume um CSV bruto exportado a partir do dataset público
"World Bank Intl Education" (o mesmo schema usado na consulta ao
BigQuery: bigquery-public-data.world_bank_intl_education.international_education),
com as colunas:

    country_name   -> nome do país (ex: "Brazil")
    country_code    -> código ISO do país (ex: "BRA")
    indicator_name  -> descrição do indicador (ex: "Adult literacy rate...")
    indicator_code  -> código do indicador (ex: "SE.ADT.LITR.ZS")
    year            -> ano da observação (int)
    value           -> valor numérico do indicador (float)

Caso seu CSV tenha nomes de coluna diferentes, ajuste o dicionário
RENOMEAR_COLUNAS na seção de configuração abaixo.
"""

# ==========================================================================
# 0. IMPORTAÇÕES
# ==========================================================================
import pandas as pd            # biblioteca principal para manipulação de dados
import numpy as np             # usado para operações numéricas e tratamento de NaN
import os                      # usado para checar existência de arquivos/pastas

# ==========================================================================
# CONFIGURAÇÃO GERAL (ajuste conforme seu ambiente)
# ==========================================================================

CAMINHO_ENTRADA = "world_bank_education.csv"   # arquivo bruto de entrada (ajuste o caminho)
CAMINHO_SAIDA = "dados_tratados.csv"           # nome exigido para o arquivo de saída

# Caso as colunas do seu arquivo tenham nomes diferentes dos esperados,
# mapeie aqui: {"nome_no_arquivo": "nome_padronizado"}
RENOMEAR_COLUNAS = {
    "country_name": "country_name",
    "country_code": "country_code",
    "indicator_name": "indicator_name",
    "indicator_code": "indicator_code",
    "year": "year",
    "value": "value",
}

# Indicadores de interesse: alfabetização e investimento em educação.
# Os códigos abaixo são os códigos oficiais usados pelo World Bank
# (mesmos códigos utilizados na notebook original de referência).
INDICADORES_DE_INTERESSE = {
    "SE.ADT.LITR.ZS": "taxa_alfabetizacao_adulta",        # % de adultos alfabetizados
    "SE.XPD.TOTL.GB.ZS": "pct_gasto_publico_em_educacao",  # % do gasto público total em educação
    "SE.XPD.TOTL.GD.ZS": "pct_pib_investido_em_educacao",  # % do PIB investido em educação
}


# ==========================================================================
# 1. FUNÇÃO: CARREGAR E LIMPAR OS DADOS (tratamento de valores ausentes)
# ==========================================================================
def carregar_e_limpar_dados(caminho_csv: str) -> pd.DataFrame:
    """
    Carrega o CSV bruto e realiza a limpeza inicial:
    - padroniza nomes de colunas
    - remove linhas totalmente vazias
    - converte tipos numéricos
    - trata valores ausentes na coluna 'value'
    """

    # Verifica se o arquivo existe antes de tentar ler, evitando erro genérico
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_csv}")

    # Lê o CSV bruto para um DataFrame do Pandas
    df = pd.read_csv(caminho_csv)

    # Renomeia colunas para o padrão esperado pelo script (caso necessário)
    df = df.rename(columns=RENOMEAR_COLUNAS)

    # Remove linhas em que TODAS as colunas estão vazias (lixo de exportação)
    df = df.dropna(how="all")

    # Garante que a coluna 'year' seja numérica; valores inválidos viram NaN
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Garante que a coluna 'value' seja numérica; valores inválidos viram NaN
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Remove espaços em branco extras em colunas de texto (nome/código do país e indicador)
    colunas_texto = ["country_name", "country_code", "indicator_name", "indicator_code"]
    for coluna in colunas_texto:
        df[coluna] = df[coluna].astype(str).str.strip()

    # Remove linhas sem 'country_name' ou 'indicator_code', pois são a chave da análise
    df = df.dropna(subset=["country_name", "indicator_code"])

    # Remove linhas sem 'year', pois não é possível calcular séries temporais sem ano
    df = df.dropna(subset=["year"])

    # Converte 'year' para inteiro após remover NaNs (evita erro de conversão)
    df["year"] = df["year"].astype(int)

    # Trata valores ausentes em 'value': ao invés de descartar a linha inteira,
    # preenchemos com a mediana do MESMO indicador e MESMO país, preservando
    # a tendência local em vez de usar uma média global distorcida.
    df["value"] = df.groupby(["country_name", "indicator_code"])["value"] \
                     .transform(lambda serie: serie.fillna(serie.median()))

    # Após o preenchimento por grupo, ainda pode haver NaN (grupo 100% vazio);
    # nesses casos, descartamos a linha por falta de informação suficiente
    df = df.dropna(subset=["value"])

    # Remove duplicatas exatas (mesmo país, indicador e ano registrados 2x)
    df = df.drop_duplicates(subset=["country_name", "indicator_code", "year"])

    # Reseta o índice do DataFrame após todas as remoções de linhas
    df = df.reset_index(drop=True)

    return df


# ==========================================================================
# 2. FUNÇÃO: SELECIONAR INDICADORES DE INTERESSE
# ==========================================================================
def selecionar_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra o DataFrame para manter apenas os indicadores definidos em
    INDICADORES_DE_INTERESSE (alfabetização e investimento em educação),
    e cria uma coluna com um nome amigável para cada indicador.
    """

    # Filtra apenas as linhas cujo 'indicator_code' está no dicionário de interesse
    df_filtrado = df[df["indicator_code"].isin(INDICADORES_DE_INTERESSE.keys())].copy()

    # Cria uma coluna 'indicador_amigavel' mapeando o código para um nome legível
    df_filtrado["indicador_amigavel"] = df_filtrado["indicator_code"].map(INDICADORES_DE_INTERESSE)

    # Alerta caso nenhum indicador de interesse tenha sido encontrado no dataset
    if df_filtrado.empty:
        print("Aviso: nenhum dos indicadores de interesse foi encontrado no dataset.")

    return df_filtrado


# ==========================================================================
# 3. FUNÇÃO: AGREGAÇÕES — CRESCIMENTO E RANKINGS ENTRE PAÍSES
# ==========================================================================
def calcular_crescimento_e_rankings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula, para cada país e indicador:
    - valor do primeiro e do último ano disponível
    - crescimento absoluto e percentual entre o primeiro e o último ano
    - ranking dos países por crescimento percentual, dentro de cada indicador
    """

    # Ordena os dados por país, indicador e ano, para garantir sequência temporal correta
    df = df.sort_values(by=["indicator_code", "country_name", "year"])

    # Agrupa por país e indicador para pegar o primeiro (min) e último (max) ano de cada série
    primeiro_ano = df.groupby(["country_name", "indicator_code"])["year"].transform("min")
    ultimo_ano = df.groupby(["country_name", "indicator_code"])["year"].transform("max")

    # Cria máscaras booleanas para identificar as linhas do primeiro e do último ano
    eh_primeiro_ano = df["year"] == primeiro_ano
    eh_ultimo_ano = df["year"] == ultimo_ano

    # Extrai o valor do primeiro ano por grupo (país + indicador)
    valores_iniciais = (
        df[eh_primeiro_ano]
        .groupby(["country_name", "indicator_code"])["value"]
        .first()
        .rename("valor_inicial")
    )

    # Extrai o valor do último ano por grupo (país + indicador)
    valores_finais = (
        df[eh_ultimo_ano]
        .groupby(["country_name", "indicator_code"])["value"]
        .first()
        .rename("valor_final")
    )

    # Extrai também os anos inicial e final, para deixar claro o período analisado
    anos_iniciais = df[eh_primeiro_ano].groupby(["country_name", "indicator_code"])["year"].first().rename("ano_inicial")
    anos_finais = df[eh_ultimo_ano].groupby(["country_name", "indicator_code"])["year"].first().rename("ano_final")

    # Junta valores iniciais, finais e anos em uma única tabela de resumo por país/indicador
    resumo = pd.concat([anos_iniciais, anos_finais, valores_iniciais, valores_finais], axis=1).reset_index()

    # Calcula o crescimento absoluto (valor final menos valor inicial)
    resumo["crescimento_absoluto"] = resumo["valor_final"] - resumo["valor_inicial"]

    # Calcula o crescimento percentual, evitando divisão por zero (substitui 0 por NaN antes de dividir)
    denominador_seguro = resumo["valor_inicial"].replace(0, np.nan)
    resumo["crescimento_percentual"] = (resumo["crescimento_absoluto"] / denominador_seguro) * 100

    # Adiciona a coluna com o nome amigável do indicador para facilitar a leitura do ranking
    resumo["indicador_amigavel"] = resumo["indicator_code"].map(INDICADORES_DE_INTERESSE)

    # Gera o RANKING: dentro de cada indicador, ordena os países do maior para o menor
    # crescimento percentual, atribuindo uma posição (1 = maior crescimento)
    resumo["ranking_crescimento"] = (
        resumo.groupby("indicator_code")["crescimento_percentual"]
        .rank(method="min", ascending=False)
    )

    # Converte o ranking para inteiro (removendo casas decimais desnecessárias)
    resumo["ranking_crescimento"] = resumo["ranking_crescimento"].astype("Int64")

    # Ordena o resultado final por indicador e depois por posição no ranking
    resumo = resumo.sort_values(by=["indicator_code", "ranking_crescimento"]).reset_index(drop=True)

    return resumo


# ==========================================================================
# 4. FUNÇÃO: EXPORTAR O RESULTADO FINAL PARA CSV
# ==========================================================================
def exportar_csv(df: pd.DataFrame, caminho_saida: str) -> None:
    """
    Exporta o DataFrame final tratado para um arquivo CSV, sem o índice
    do Pandas, usando codificação UTF-8 para preservar acentuação.
    """

    # Salva o DataFrame em disco, sem escrever a coluna de índice do Pandas
    df.to_csv(caminho_saida, index=False, encoding="utf-8-sig")

    # Confirma no console que o arquivo foi gerado com sucesso
    print(f"Arquivo exportado com sucesso: {caminho_saida}")


# ==========================================================================
# EXECUÇÃO PRINCIPAL DO PIPELINE
# ==========================================================================
def main():
    # Etapa 1: carrega o CSV bruto e aplica limpeza + tratamento de ausentes
    dados_limpos = carregar_e_limpar_dados(CAMINHO_ENTRADA)

    # Etapa 2: seleciona apenas os indicadores de alfabetização e investimento
    dados_selecionados = selecionar_indicadores(dados_limpos)

    # Etapa 3: calcula crescimento entre primeiro/último ano e gera rankings por país
    resultado_final = calcular_crescimento_e_rankings(dados_selecionados)

    # Etapa 4: exporta o resultado tratado para 'dados_tratados.csv'
    exportar_csv(resultado_final, CAMINHO_SAIDA)

    # Exibe uma prévia do resultado final no console, para conferência rápida
    print(resultado_final.head(20))


# Garante que main() só rode quando o script for executado diretamente
# (e não quando for importado como módulo em outro script)
if __name__ == "__main__":
    main()