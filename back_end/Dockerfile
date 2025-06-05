FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
COPY back_end/fast_api_main.py . 
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD [ "uvicorn" , "fast_api_main:loan_salary_app" , "--host" , "0.0.0.0" , "--port" , "8000"]