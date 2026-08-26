# Usamos uma imagem base leve do Python 3.9
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema necessárias para algumas libs em Python (se houver)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o arquivo de dependências primeiro (aproveita cache do Docker)
COPY requirements.txt .

# Instala as dependências listadas
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Expõe a porta 8000
EXPOSE 8000

# Comando para rodar a aplicação quando o container iniciar
CMD ["python", "run.py"]
