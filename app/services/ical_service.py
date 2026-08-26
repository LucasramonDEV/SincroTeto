import requests
from icalendar import Calendar
import pandas as pd
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def parse_ical_to_dataframe(url: str) -> pd.DataFrame:
    """
    Baixa um arquivo .ics de uma URL (ex: Airbnb), extrai os eventos 
    e retorna um DataFrame do Pandas com os períodos ocupados.
    """
    try:
        # Se a URL não for fornecida ou for inválida, retorna um DataFrame vazio com as colunas corretas
        if not url or not url.startswith("http"):
            return pd.DataFrame(columns=["data_inicio", "data_fim", "resumo", "duracao_dias"])

        # Faz o download do arquivo iCal
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Lança erro se o HTTP não for 200 OK

        # Faz o parse do calendário
        cal = Calendar.from_ical(response.text)
        
        eventos = []
        for component in cal.walk('vevent'):
            inicio = component.get('dtstart').dt
            fim = component.get('dtend').dt
            resumo = str(component.get('summary', 'Ocupado'))

            # Se for datetime (com hora), converte para date simples para facilitar análise
            if isinstance(inicio, datetime):
                inicio = inicio.date()
            if isinstance(fim, datetime):
                fim = fim.date()
            
            duracao = (fim - inicio).days

            eventos.append({
                "data_inicio": inicio,
                "data_fim": fim,
                "resumo": resumo,
                "duracao_dias": duracao
            })

        df = pd.DataFrame(eventos)
        
        if not df.empty:
            # Ordena os eventos pela data de inicio
            df = df.sort_values(by="data_inicio").reset_index(drop=True)
            
        return df

    except Exception as e:
        logger.error(f"Erro ao processar iCal da URL {url}: {str(e)}")
        # Em caso de falha silenciosa, retorna o esqueleto
        return pd.DataFrame(columns=["data_inicio", "data_fim", "resumo", "duracao_dias"])

def calcular_ocupacao_mensal(df_ical: pd.DataFrame, ano: int, mes: int) -> float:
    """
    Exemplo prático de uso do DataFrame:
    Calcula quantos dias do mês solicitado estão ocupados (cruza as datas).
    """
    if df_ical.empty:
        return 0.0
    
    import calendar
    from datetime import date

    # Quantos dias o mês tem
    _, ultimo_dia = calendar.monthrange(ano, mes)
    inicio_mes = date(ano, mes, 1)
    fim_mes = date(ano, mes, ultimo_dia)
    
    dias_ocupados = set()

    for _, row in df_ical.iterrows():
        # Verifica se o evento ocorre (pelo menos parcialmente) neste mês
        if row['data_fim'] > inicio_mes and row['data_inicio'] <= fim_mes:
            # Pega a intersecção
            start = max(row['data_inicio'], inicio_mes)
            end = min(row['data_fim'], fim_mes)
            
            # Adiciona os dias ao set para evitar duplicidade
            delta = (end - start).days
            for i in range(delta):
                dias_ocupados.add(start.day + i)
                
    total_ocupado = len(dias_ocupados)
    
    # Retorna o percentual de ocupação
    taxa = (total_ocupado / ultimo_dia) * 100
    return round(taxa, 2)
