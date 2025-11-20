FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libglib2.0-0 libsm6 libxrender1 libxext6 poppler-utils \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 4000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "4000"]
