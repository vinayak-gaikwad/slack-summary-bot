FROM python:3.10.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
    
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3000

ENV PORT 3000

CMD ["python", "main.py"]
