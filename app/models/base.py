from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    login = Column(String, unique=True, index=True) # Antiga chave_acesso virou login
    senha = Column(String) # Novo campo de senha
    papel = Column(String, default="cliente") # admin ou cliente

    # Novos campos de Perfil
    sobrenome = Column(String, nullable=True)
    telefone = Column(String, nullable=True) # Prefixo + numero
    email = Column(String, nullable=True)
    cpf = Column(String, nullable=True)
    foto_perfil = Column(String, nullable=True) # URL ou path da foto

    propriedades = relationship("Propriedade", back_populates="dono")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    nome_usuario = Column(String)
    estrelas = Column(Float) # De 0.0 a 5.0
    comentario = Column(String)
    data_envio = Column(DateTime, default=datetime.datetime.utcnow)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    data_inicio = Column(DateTime)
    data_fim = Column(DateTime)
    ocupado_por = Column(String) # "hospede" ou "proprietario"
    valor_arrecadado = Column(Float, default=0.0)
    data_criacao = Column(DateTime, default=datetime.datetime.utcnow)

    propriedade_id = Column(Integer, ForeignKey("propriedades.id"))
    propriedade = relationship("Propriedade", back_populates="reservas")

class Propriedade(Base):
    __tablename__ = "propriedades"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    tipo = Column(String) # Flat, Residencial, Galpao, Sala, Outros
    tipo_aluguel = Column(String) # Curto_prazo, Longo_prazo
    regiao = Column(String)
    bairro = Column(String) # Novo campo de Bairro
    descricao = Column(String, nullable=True) # Novo campo de descricao do imovel
    fotos = Column(String, nullable=True) # Links de fotos separados por virgula
    link_ical = Column(String, nullable=True) # Link do Airbnb etc
    custo_fixo_mensal = Column(Float, default=0.0) # Condominio + IPTU

    valor_diaria = Column(Float, nullable=True)
    valor_mensalidade = Column(Float, nullable=True)

    # Configurações de IA e Alertas
    alerta_frequencia_meses = Column(Integer, default=3) # 3, 4, 5 ou 6 meses
    data_ultima_vistoria = Column(DateTime, default=datetime.datetime.utcnow) # Reseta quando o usuario marca como resolvido

    # Campos customizáveis para o Portal do Hóspede (PDF)
    pdf_wifi_rede = Column(String, default="SincroWifi")
    pdf_wifi_senha = Column(String, default="12345678")
    pdf_regras_casa = Column(String, default="Horário de Silêncio: Das 22h às 08h.\nProibido festas.")
    pdf_guia_uso = Column(String, default="Ar Condicionado: Manter em 23 graus.")
    pdf_contatos_emergencia = Column(String, default="Anfitrião: (11) 99999-9999\nSAMU: 192")

    dono_id = Column(Integer, ForeignKey("usuarios.id"))
    dono = relationship("Usuario", back_populates="propriedades")
    gastos = relationship("Gasto", back_populates="propriedade")
    reservas = relationship("Reserva", back_populates="propriedade", cascade="all, delete-orphan")

class Gasto(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    descricao_original = Column(String) # O que o usuario digitou, ex: "Troca de resistencia"
    categoria_ia = Column(String, nullable=True) # Ex: "Manutencao Eletrica" (gerado pela IA)
    valor = Column(Float)
    data_gasto = Column(DateTime, default=datetime.datetime.utcnow)

    propriedade_id = Column(Integer, ForeignKey("propriedades.id"))
    propriedade = relationship("Propriedade", back_populates="gastos")
