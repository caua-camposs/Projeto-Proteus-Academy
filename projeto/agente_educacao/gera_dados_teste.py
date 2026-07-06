"""
Script Auxiliar: Gerador de Dados Sintéticos do World Bank
Objetivo: Criar uma base de testes horizontal idêntica ao padrão do Kaggle
          para destravar o pipeline de dados imediatamente.
"""
import pandas as pd
import numpy as np

def gerar_base_teste():
    # Lista de países e indicadores exigidos no edital
    paises = ["Brazil", "United States", "Singapore", "Finland", "Angola", "Japan"]
    codigos_paises = ["BRA", "USA", "SGP", "FIN", "AGO", "JPN"]
    
    indicadores = {
        "SE.ADT.LITR.ZS": "Adult literacy rate, population 15+ years, both sexes (%)",
        "SE.XPD.TOTL.GB.ZS": "Government expenditure on education as % of total expenditure (%)",
        "SE.XPD.TOTL.GD.ZS": "Government expenditure on education as % of GDP (%)"
    }
    
    linhas = []
    
    # Gerando dados fictícios consistentes de 2010 a 2015 para simular o histórico
    for pais, cod_pais in zip(paises, codigos_paises):
        for ind_code, ind_name in indicadores.items():
            linha = {
                "Country Name": pais,
                "Country Code": cod_pais,
                "Indicator Name": ind_name,
                "Indicator Code": ind_code
            }
            
            # Simula a estrutura horizontal do World Bank (Anos como colunas)
            for ano in range(2010, 2016):
                if ind_code == "SE.ADT.LITR.ZS": # Alfabetização
                    base = 90.0 if pais != "Brazil" and pais != "Angola" else 70.0
                    ruido = np.random.uniform(0.5, 1.5) * (ano - 2010)
                    linha[str(ano)] = min(100.0, base + ruido)
                else: # Investimentos em Educação
                    base = 5.0 if pais != "Singapore" else 4.0
                    ruido = np.random.uniform(-0.2, 0.4)
                    linha[str(ano)] = base + ruido
            
            # Introduz alguns valores nulos (vazios) para testar a limpeza do seu pipeline
            linha["2012"] = np.nan
            
            linhas.append(linha)
            
    df = pd.DataFrame(linhas)
    
    # Salva com o nome exato que o script principal espera
    df.to_csv("EdStatsData.csv", index=False, encoding="utf-8")
    print("O arquivo 'EdStatsData.csv' fictício foi gerado na pasta")

if __name__ == "__main__":
    gerar_base_teste()