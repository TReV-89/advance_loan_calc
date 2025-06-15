FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY fast_api_main.py . 
COPY calculations.py .
COPY pydantic_models.py .

EXPOSE 8000

CMD [ "fastapi" , "run" , "fast_api_main.py"]