import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def categorizar_gasto_nlp(descricao: str) -> str:
    texto = descricao.lower()
    
    regras = {
        "Manutenção Hidráulica": [r"chuveiro", r"cano", r"vazamento", r"torneira", r"pia", r"vaso", r"agua", r"água"],
        "Manutenção Elétrica": [r"luz", r"lampada", r"lâmpada", r"fio", r"disjuntor", r"tomada", r"resistencia", r"resistência", r"ar[- ]condicionado"],
        "Manutenção Estrutural": [r"parede", r"pintura", r"tinta", r"gesso", r"janela", r"porta", r"telhado", r"piso", r"fechadura"],
        "Limpeza e Higienização": [r"limpeza", r"faxina", r"diarista", r"produto", r"lavanderia", r"lixo"],
        "Impostos e Taxas": [r"iptu", r"condominio", r"condomínio", r"multa", r"taxa"],
        "Reposição de Inventário": [r"lencol", r"lençol", r"toalha", r"talher", r"copo", r"prato", r"travesseiro", r"colchao", r"colchão"]
    }

    for categoria, padroes in regras.items():
        for padrao in padroes:
            if re.search(padrao, texto):
                return categoria
                
    return "Outros Diversos"

def motor_sazonalidade(regiao: str, mes_atual: int = None) -> dict:
    if not mes_atual:
        mes_atual = datetime.now().month
        
    regiao = regiao.lower()
    
    # STATUS: 🔥 Região Quente (Alta demanda) ou ❄️ Fria / Normal
    
    if "porto de galinhas" in regiao or "praia" in regiao or "recife" in regiao or "ipojuca" in regiao or "olinda" in regiao:
        # Meses de chuva intensa no nordeste (Maio a Agosto)
        if 5 <= mes_atual <= 8:
            return {
                "status": "Baixa Temporada (Chuvas)",
                "sugestao": "A IA sugere aplicar descontos estratégicos de -15% a -25% na diária para maximizar a capitalização e evitar vacância total.",
                "percentual_sugerido": -15,
                "quente": False
            }
        # Meses de alta (Dezembro a Março) + Carnaval
        elif mes_atual in [12, 1, 2, 3]:
            return {
                "status": "Alta Temporada (Verão)",
                "sugestao": "Clima ideal e férias. Aumente o valor da diária em até +30% em relação à média anual.",
                "percentual_sugerido": 30,
                "quente": True
            }
            
    if "gravat" in regiao or "sair" in regiao:
        # Inverno no Nordeste = Alta serra e Festas Juninas
        if mes_atual in [6, 7]:
            return {
                "status": "Alta Temporada (Frio / Festividades)",
                "sugestao": "Festividades de São João e Clima Frio. Procura fortíssima. Aumente o valor em +40%.",
                "percentual_sugerido": 40,
                "quente": True
            }
            
    return {
        "status": "Sazonalidade Padrão",
        "sugestao": "Mantenha o preço alinhado com a média. Não há eventos climáticos ou alta demanda previstos para este mês.",
        "percentual_sugerido": 0,
        "quente": False
    }

def alerta_desgaste(regiao: str, data_ultima_manutencao: datetime, frequencia_escolhida: int = 3) -> str:
    meses_passados = (datetime.now() - data_ultima_manutencao).days / 30.0
    regiao = regiao.lower()

    if meses_passados >= frequencia_escolhida:
        if "ipojuca" in regiao or "porto de galinhas" in regiao or "praia" in regiao or "litoral" in regiao or "olinda" in regiao:
            return f"ALERTA (Ciclo de {frequencia_escolhida}m): Risco alto de oxidação em eletrodomésticos e janelas devido à maresia intensa na região. Agende vistoria preventiva!"
        elif "campo" in regiao or "mata" in regiao or "gravat" in regiao or "sair" in regiao:
            return f"ALERTA (Ciclo de {frequencia_escolhida}m): Região de alta incidência de insetos/umidade de serra. Considere dedetização preventiva."
        else:
            return f"ALERTA (Ciclo de {frequencia_escolhida}m): Tempo limite sem manutenção preventiva atingido. Verifique ar-condicionados e hidráulica básica."

    return None
