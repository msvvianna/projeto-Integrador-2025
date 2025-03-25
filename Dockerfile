# Use uma imagem oficial do Python como base
FROM python:3.11

# Defina o diretório de trabalho no container
WORKDIR /app

# Copie o arquivo de requisitos para dentro do container
COPY requirements.txt .

# Instale as dependências
RUN apt-get update && apt-get install -y default-mysql-client netcat-openbsd

# Copie o restante do código da aplicação para dentro do container
COPY . .

# Exponha a porta em que a aplicação irá rodar
EXPOSE 8000

# Defina o comando para rodar a aplicação com Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
