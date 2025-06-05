FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
COPY front_end/streamlit_main.py . 
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD [ "streamlit" , "run" , "streamlit_main.py"]