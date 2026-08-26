import requests
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def obter_ipca_acumulado_12m() -> float:
    """
    Consulta a API do Banco Central do Brasil (SGS - Sistema Gerenciador de Séries Temporais)
    Série 433: Índice Nacional de Preços ao Consumidor Amplo (IPCA) - variação mensal.
    Calcula o acumulado dos últimos 12 meses disponíveis.
    """
    try:
        # A URL da série 433 do SGS (retorna JSON com as variações mensais)
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/12?formato=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        dados = response.json()
        if not dados:
            return 0.0
            
        # Converte para Pandas DataFrame
        df = pd.DataFrame(dados)
        df['valor'] = df['valor'].astype(float)
        
        # Cálculo do acumulado: (1 + taxa1) * (1 + taxa2) ... - 1
        # Como os dados vêm em %, dividimos por 100
        taxas_decimais = df['valor'] / 100
        acumulado = (taxas_decimais + 1).prod() - 1
        
        return round(acumulado * 100, 2)
    
    except Exception as e:
        logger.error(f"Erro ao buscar IPCA na API do Banco Central: {e}")
        return 0.0 # Em caso de erro, retorna 0% de reajuste

def calcular_custo_oportunidade(taxa_ocupacao_atual: float, valor_diaria_curto: float, valor_aluguel_longo: float, custo_fixo_mensal: float) -> dict:
    """
    Compara o faturamento de um aluguel de temporada (curto prazo) com um aluguel fixo (longo prazo).
    Retorna uma análise clara sobre qual vale mais a pena no trimestre.
    """
    dias_no_mes = 30
    
    # Receita Curto Prazo
    dias_ocupados = dias_no_mes * (taxa_ocupacao_atual / 100)
    receita_curto = dias_ocupados * valor_diaria_curto
    lucro_curto = receita_curto - custo_fixo_mensal
    
    # Receita Longo Prazo
    lucro_longo = valor_aluguel_longo - custo_fixo_mensal
    
    if lucro_longo > lucro_curto:
        diferenca_percentual = ((lucro_longo - lucro_curto) / max(lucro_curto, 1)) * 100
        recomendacao = f"Neste trimestre, alugar por contrato fixo (longo prazo) renderia aproximadamente {diferenca_percentual:.1f}% a mais e daria menos trabalho, visto a ocupação atual de {taxa_ocupacao_atual}%."
        vencedor = "Longo Prazo"
    else:
        diferenca_percentual = ((lucro_curto - lucro_longo) / max(lucro_longo, 1)) * 100
        recomendacao = f"Sua estratégia atual de curto prazo é superior, rendendo {diferenca_percentual:.1f}% a mais do que um contrato fixo, justificando o trabalho da gestão."
        vencedor = "Curto Prazo"
        
    return {
        "lucro_estimado_curto": round(lucro_curto, 2),
        "lucro_estimado_longo": round(lucro_longo, 2),
        "vencedor": vencedor,
        "recomendacao": recomendacao
    }
