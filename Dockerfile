FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt . || true
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY . /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt || true
RUN pip install pydantic requests || true
ENV PYTHONPATH=/app
EXPOSE 8765
CMD ["python3", "-u", "-m", "runtime.mock_server"]
