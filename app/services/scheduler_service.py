import schedule
import time
import threading
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.base import Propriedade, Gasto
from app.services.ai_service import alerta_desgaste
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Memória temporária para guardar os alertas e mostrar na tela depois
alertas_memoria = []

def rotina_verificar_desgaste():
    """
    Função que o cron vai executar. Varre as propriedades, encontra a data 
    da última manutenção (ou a criação da propriedade) e emite os alertas.
    """
    logger.info("Iniciando varredura de Alertas de Desgaste...")
    db = SessionLocal()
    global alertas_memoria
    alertas_memoria.clear() # Limpa os antigos

    try:
        propriedades = db.query(Propriedade).all()
        for prop in propriedades:
            if prop.data_ultima_vistoria:
                data_base = prop.data_ultima_vistoria
            else:
                data_base = datetime.now() - timedelta(days=200) # Força alerta se não tiver data

            alerta = alerta_desgaste(prop.regiao, data_base, prop.alerta_frequencia_meses)
            
            if alerta:
                alertas_memoria.append({
                    "propriedade_id": prop.id,
                    "nome": prop.nome,
                    "mensagem": alerta
                })
                logger.warning(f"Alerta gerado para {prop.nome}: {alerta}")
    finally:
        db.close()

def iniciar_scheduler():
    """
    Inicia o schedule em uma thread separada para não travar o FastAPI.
    No mundo real rodaria a cada X horas, aqui rodaremos a cada 1 minuto para testes.
    """
    schedule.every(1).minutes.do(rotina_verificar_desgaste)
    
    def run_scheduler():
        # Roda a primeira vez imediatamente
        rotina_verificar_desgaste()
        while True:
            schedule.run_pending()
            time.sleep(10)
            
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    logger.info("Scheduler de IA em background iniciado.")
