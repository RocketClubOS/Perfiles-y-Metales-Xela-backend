from database import crear_tabla, guardar_conversacion
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agent import answer_customer
import threading
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__, static_folder="../frontend", static_url_path="")

CORS(app, origins=[
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://192.168.1.156:5500",
    "https://rocketclubos.github.io",
    "https://rocketclubos.github.io/Perfiles-y-Metales-Xela"
])

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per hour"]
)

crear_tabla()


@app.route("/")
def home():
    user_agent = request.headers.get("User-Agent", "").lower()

    mobile_keywords = ["iphone", "android", "mobile", "ipad"]

    if any(word in user_agent for word in mobile_keywords):
        return send_from_directory(app.static_folder, "mobile.html")

    return send_from_directory(app.static_folder, "index.html")


@app.route("/mobile")
def mobile():
    return send_from_directory(app.static_folder, "mobile.html")


@app.route("/desktop")
def desktop():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/health")
def health():
    return "Bobby is alive!"


@app.route("/preguntar", methods=["POST"])
@limiter.limit("10 per minute")
def preguntar():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"answer": "Solicitud inválida."}), 400

    question = data.get("question", "").strip()

    if not question:
        return jsonify({"answer": "¿Qué producto necesitas?"})

    if len(question) > 500:
        return jsonify({"answer": "Tu pregunta es muy larga. Escríbela más corta."}), 400

    try:
        answer = answer_customer(question)

        threading.Thread(
            target=guardar_conversacion,
            args=(question, answer),
            daemon=True
        ).start()

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({
            "answer": f"ERROR: {str(e)}"
        }), 500
    

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)