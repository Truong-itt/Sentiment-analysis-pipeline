FROM python:3.10-slim

WORKDIR /rotoro_sentiment

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-deps torch==2.3.1+cpu torchvision==0.18.1+cpu -f https://download.pytorch.org/whl/torch_stable.html && \
    pip install -r requirements.txt
COPY app.py .
COPY sentiment_model/ ./sentiment_model/

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8020"]
