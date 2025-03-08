import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoModelForSequenceClassification, AutoTokenizer, MarianMTModel, MarianTokenizer
import torch

# Configurar logging para depuración
logging.basicConfig(level=logging.DEBUG)

# Crear la aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas las rutas

### 📌 MODELO DE ANÁLISIS DE SENTIMIENTOS
model_sentiment_name = "distilbert-base-uncased-finetuned-sst-2-english"
logging.info("Cargando el modelo de análisis de sentimientos...")
model_sentiment = AutoModelForSequenceClassification.from_pretrained(model_sentiment_name)
tokenizer_sentiment = AutoTokenizer.from_pretrained(model_sentiment_name)
logging.info("Modelo de análisis de sentimientos cargado correctamente.")

@app.route("/predict", methods=["POST"])
def predict():
    """Recibe un texto y devuelve el sentimiento"""
    try:
        data = request.get_json()
        if "text" not in data or not data["text"].strip():
            logging.warning("Texto vacío en la solicitud de predicción")
            return jsonify({"error": "No text provided"}), 400

        logging.info(f"Texto recibido para análisis de sentimiento: {data['text']}")
        inputs = tokenizer_sentiment(data["text"], return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = model_sentiment(**inputs)
        prediction = torch.argmax(outputs.logits).item()

        sentiment = "Positivo" if prediction == 1 else "Negativo"

        return jsonify({"prediction": sentiment})

    except Exception as e:
        logging.error(f"Error en análisis de sentimiento: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


### 📌 MODELO DE TRADUCCIÓN
model_translation_name = "Helsinki-NLP/opus-mt-en-es"
logging.info("Cargando el modelo de traducción...")
model_translation = MarianMTModel.from_pretrained(model_translation_name)
tokenizer_translation = MarianTokenizer.from_pretrained(model_translation_name)
logging.info("Modelo de traducción cargado correctamente.")

@app.route("/translate", methods=["POST", "OPTIONS"])
def translate():
    """Recibe un texto en inglés y lo traduce al español"""
    logging.info(f"Solicitud recibida en /translate con método {request.method}")

    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200

    try:
        data = request.get_json()
        if not data or "text" not in data or not data["text"].strip():
            logging.warning("Texto vacío en la solicitud de traducción")
            return jsonify({"error": "No text provided"}), 400

        logging.info(f"Texto recibido para traducción: {data['text']}")
        inputs = tokenizer_translation(data["text"], return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            translated_tokens = model_translation.generate(**inputs)
        translated_text = tokenizer_translation.decode(translated_tokens[0], skip_special_tokens=True)

        logging.info(f"Texto traducido: {translated_text}")
        return jsonify({"translated_text": translated_text})

    except Exception as e:
        logging.error(f"Error en la traducción: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logging.info("🚀 Servidor Flask iniciándose en http://127.0.0.1:5555")
    app.run(host="0.0.0.0", port=5555, debug=True)