FROM python:3.11

WORKDIR /app

COPY src/requirements.txt src/requirements.txt

RUN pip install --no-cache-dir -r ./src/requirements.txt

COPY . ./

EXPOSE 8000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
