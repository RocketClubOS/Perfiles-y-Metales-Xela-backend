import os
import threading
import requests

from agent import answer_customer
from club_xela_db import (
    agregar_compra as db_agregar_compra,
    cliente_existe,
    crear_cliente,
    normalizar_telefono,
    obtener_cliente,
    obtener_movimientos,
)
from database import crear_tabla, guardar_conversacion
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
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

from flask import request

VERIFY_TOKEN = "bobby123"
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

@app.route("/webhook", methods=["POST"])
def messenger_webhook():
    data = request.get_json()
    print("MENSAJE RECIBIDO:")
    print(data)

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            message_text = event.get("message", {}).get("text")

            if sender_id and message_text:
                respuesta = answer_customer(message_text)
                enviar_mensaje_messenger(sender_id, respuesta)

    return "EVENT_RECEIVED", 200


def enviar_mensaje_messenger(sender_id, texto):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": texto}
    }

    r = requests.post(url, json=payload)
    print("RESPUESTA META:", r.status_code, r.text)


@app.route("/webhook", methods=["POST"])
def messenger_webhook():
    data = request.get_json()

    print("MENSAJE RECIBIDO:")
    print(data)

    return "EVENT_RECEIVED", 200

@app.route("/mobile")
def mobile():
    return send_from_directory(app.static_folder, "mobile.html")


@app.route("/desktop")
def desktop():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/health")
def health():
    return "Bobby is alive!"


@app.route("/club-xela")
def club_xela():
    return send_from_directory(app.static_folder, "rewards.html")


@app.route("/api/registro", methods=["POST"])
def registro_club_xela():
    data = request.get_json(silent=True) or {}

    nombre = str(data.get("nombre", "")).strip()
    telefono = normalizar_telefono(data.get("telefono"))

    if not nombre:
        return jsonify({"ok": False, "message": "El nombre es requerido."}), 400

    if not telefono:
        return jsonify({"ok": False, "message": "El WhatsApp es requerido."}), 400

    if cliente_existe(telefono):
        cliente = obtener_cliente(telefono)
        return jsonify({
            "ok": True,
            "message": "La cuenta ya existe. No se duplicó el registro.",
            "cliente": cliente
        })

    cliente = crear_cliente({
        "nombre": nombre,
        "telefono": telefono,
        "ciudad": data.get("ciudad", ""),
        "tipo_cliente": data.get("tipo_cliente", ""),
    })

    return jsonify({
        "ok": True,
        "message": "Cuenta creada correctamente",
        "cliente": cliente
    }), 201


@app.route("/api/saldo/<telefono>", methods=["GET"])
def saldo_club_xela(telefono):
    cliente = obtener_cliente(telefono)

    if not cliente:
        return jsonify({
            "ok": False,
            "message": "Cliente no encontrado"
        }), 404

    return jsonify({
        "ok": True,
        "nombre": cliente["nombre"],
        "telefono": cliente["telefono"],
        "saldo": cliente["saldo"],
        "movimientos": obtener_movimientos(telefono)
    })


@app.route("/api/agregar-compra", methods=["POST"])
def agregar_compra_club_xela():
    admin_key = os.getenv("ADMIN_KEY", "")

    if not admin_key or request.headers.get("X-ADMIN-KEY") != admin_key:
        return jsonify({
            "ok": False,
            "message": "No autorizado"
        }), 401

    data = request.get_json(silent=True) or {}
    telefono = normalizar_telefono(data.get("telefono"))
    monto_compra = data.get("monto_compra")

    if not telefono:
        return jsonify({"ok": False, "message": "El WhatsApp es requerido."}), 400

    try:
        monto_compra = float(monto_compra)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "El monto de compra no es válido."}), 400

    if monto_compra <= 0:
        return jsonify({"ok": False, "message": "El monto de compra debe ser mayor a cero."}), 400

    resultado = db_agregar_compra(
        telefono=telefono,
        monto_compra=monto_compra,
        producto=data.get("producto", ""),
        nota=data.get("nota", ""),
    )

    if not resultado:
        return jsonify({
            "ok": False,
            "message": "Cliente no encontrado"
        }), 404

    return jsonify({
        "ok": True,
        "message": "Compra agregada correctamente",
        "saldo_ganado": resultado["saldo_ganado"],
        "nuevo_saldo": resultado["nuevo_saldo"]
    })


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
