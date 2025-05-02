from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import time

app = FastAPI(title="Rotoro API", version="0.1.0")
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_path = "./sentiment_model"
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

class SentimentRequest(BaseModel):
    text: str
    entity: str

class SentimentResponse(BaseModel):
    sentiment: str
    confidence: list
    inference_time: float

def predict_sentiment(text, entity):
    combined_text = f"Đối với {entity}, {text}"
    inputs = tokenizer(combined_text, return_tensors="pt", truncation=True, padding=True)

    start_time = time.time()
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
    end_time = time.time()

    predicted_class = torch.argmax(predictions, dim=-1).item()
    sentiment_labels = {0: "NEGATIVE", 1: "NEUTRAL", 2: "POSITIVE"}
    inference_time = end_time - start_time

    return sentiment_labels[predicted_class], predictions[0].tolist(), inference_time

@app.post("/predict", response_model=SentimentResponse)
def predict(request: SentimentRequest):
    sentiment, confidence, inference_time = predict_sentiment(request.text, request.entity)
    return SentimentResponse(
        sentiment=sentiment,
        confidence=confidence,
        inference_time=round(inference_time, 4)
    )
