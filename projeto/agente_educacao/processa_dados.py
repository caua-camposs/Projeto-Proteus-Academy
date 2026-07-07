"""
Script de Análise: World Bank Education Statistics
Autor: Cauã Campos
Objetivo: Limpar, selecionar indicadores, calcular crescimento/rankings com fallback de nulos.
"""

import pandas as pd
import numpy as np
import os

# ==========================================================================
# CONFIGURAÇÃO GERAL
# ==========================================================================

CAMINHO_ENTRADA = "EdStatsData.csv"
CAMINHO_SAIDA = "dados_tratados.csv"

RENOMEAR_COLUNAS = {
    "Country Name": "country_name",
    "Country Code": "country_code",
    "Indicator Name": "indicator_name",
    "Indicator Code": "indicator_code",
    "Year": "year",
    "Value": "value",
}

INDICADORES_DE_INTERESSE = {
    "SE.ADT.LITR.ZS": "taxa_alfabetizacao_adulta",        
    "SE.XPD.TOTL.GB.ZS": "pct_gasto_publico_em_educacao",  
    "SE.XPD.TOTL.GD.ZS": "pct_pib_investido_em_educacao",  
}

# ==========================================================================
# 1. FUNÇÃO: CARREGAR E LIMPAR OS DADOS (Com Fallback de Mediana Global)
# ==========================================================================
def carregar_e_limpar_dados(caminho_csv: str) -> pd.DataFrame:
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"🚨 Arquivo de entrada não encontrado! Verifique se o nome do arquivo em CAMINHO_ENTRADA está correto: {caminho_csv}")

    print("🔄 Carregando base de dados (pode demorar alguns segundos devido ao tamanho)...")
    df = pd.read_csv(caminho_csv)
    
    # Se o dataset do Kaggle vier no formato horizontal (anos como colunas de 1970 a 2015)
    # fazemos o pivotamento (melt) para transformar anos em linhas de forma automática
    if "Indicator Code" in df.columns and any(str(col).isdigit() for col in df.columns):
        print("🔄 Detectado formato horizontal. Transpondo colunas de anos para linhas...")
        colunas_identificadoras = ["Country Name", "Country Code", "Indicator Name", "Indicator Code"]
        colunas_anos = [col for col in df.columns if str(col).isdigit()]
        df = df.melt(id_vars=colunas_identificadoras, value_vars=colunas_anos, var_name="Year", value_name="Value")

    df = df.rename(columns=RENOMEAR_COLUNAS)
    df = df.dropna(how="all")

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    colunas_texto = ["country_name", "country_code", "indicator_name", "indicator_code"]
    for coluna in colunas_texto:
        df[coluna] = df[coluna].astype(str).str.strip()

    df = df.dropna(subset=["country_name", "indicator_code", "year"])
    df["year"] = df["year"].astype(int)

    # --- TRATAMENTO DE NULOS INTELIGENTE ---
    # Passo A: Tenta preencher com a mediana do histórico do PRÓPRIO PAÍS
    df["value"] = df.groupby(["country_name", "indicator_code"])["value"] \
                     .transform(lambda serie: serie.fillna(serie.median()) if not serie.median() is np.nan else serie)

    # Passo B (FALLBACK): Se o país nunca registrou o dado, preenche com a mediana GLOBAL daquele indicador no ano
    df["value"] = df.groupby(["indicator_code", "year"])["value"] \
                     .transform(lambda serie: serie.fillna(serie.median()))

    # Se ainda assim sobrar nulo, removemos por segurança física dos cálculos
    df = df.dropna(subset=["value"])
    df = df.drop_duplicates(subset=["country_name", "indicator_code", "year"])
    
    return df.reset_index(drop=True)

# ==========================================================================
# 2. FUNÇÃO: SELECIONAR INDICADORES DE INTERESSE
# ==========================================================================
def selecionar_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    df_filtrado = df[df["indicator_code"].isin(INDICADORES_DE_INTERESSE.keys())].copy()
    df_filtrado["indicador_amigavel"] = df_filtrado["indicator_code"].map(INDICADORES_DE_INTERESSE)
    return df_filtrado

# ==========================================================================
# 3. FUNÇÃO: AGREGAÇÕES E RANKINGS
# ==========================================================================
def calcular_crescimento_e_rankings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(by=["indicator_code", "country_name", "year"])

    primeiro_ano = df.groupby(["country_name", "indicator_code"])["year"].transform("min")
    ultimo_ano = df.groupby(["country_name", "indicator_code"])["year"].transform("max")

    eh_primeiro_ano = df["year"] == primeiro_ano
    eh_ultimo_ano = df["year"] == ultimo_ano

    valores_iniciais = df[eh_primeiro_ano].groupby(["country_name", "indicator_code"])["value"].first().rename("valor_inicial")
    valores_finais = df[eh_ultimo_ano].groupby(["country_name", "indicator_code"])["value"].first().rename("valor_final")
    anos_iniciais = df[eh_primeiro_ano].groupby(["country_name", "indicator_code"])["year"].first().rename("ano_inicial")
    anos_finais = df[eh_ultimo_ano].groupby(["country_name", "indicator_code"])["year"].first().rename("ano_final")

    resumo = pd.concat([anos_iniciais, anos_finais, valores_iniciais, valores_finais], axis=1).reset_index()
    resumo["crescimento_absoluto"] = resumo["valor_final"] - resumo["valor_inicial"]

    denominador_seguro = resumo["valor_inicial"].replace(0, np.nan)
    resumo["crescimento_percentual"] = (resumo["crescimento_absoluto"] / denominador_seguro) * 100
    resumo["indicador_amigavel"] = resumo["indicator_code"].map(INDICADORES_DE_INTERESSE)

    # Gera o ranking competitivo global
    resumo["ranking_crescimento"] = resumo.groupby("indicator_code")["crescimento_percentual"].rank(method="min", ascending=False)
    resumo["ranking_crescimento"] = resumo["ranking_crescimento"].astype("Int64")

    return resumo.sort_values(by=["indicator_code", "ranking_crescimento"]).reset_index(drop=True)

def exportar_csv(df: pd.DataFrame, caminho_saida: str) -> None:
    df.to_csv(caminho_saida, index=False, encoding="utf-8-sig")
    print(f"Arquivo exportado com sucesso para a automação: {caminho_saida}")

# ==========================================================================
# EXECUÇÃO DO PIPELINE
# ==========================================================================
def main():
    try:
        dados_limpos = carregar_e_limpar_dados(CAMINHO_ENTRADA)
        dados_selecionados = selecionar_indicadores(dados_limpos)
        resultado_final = calcular_crescimento_e_rankings(dados_selecionados)
        exportar_csv(resultado_final, CAMINHO_SAIDA)
        
        print("\nPrévia dos dados tratados para conferência:")
        print(resultado_final.head(10))
    except Exception as e:
        print(f"\nOcorreu um erro durante a execução: {e}")

if __name__ == "__main__":
    main()
    