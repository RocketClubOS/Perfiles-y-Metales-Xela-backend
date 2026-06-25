import os
import json
from datetime import datetime

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    sheet_id = os.environ.get("SHEET_ID")

    if not creds_json or not sheet_id:
        print("Google Sheets no configurado")
        return None

    creds_info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def append_row(tab_name, values):
    service = get_service()
    if service is None:
        return False

    service.spreadsheets().values().append(
        spreadsheetId=os.environ["SHEET_ID"],
        range=f"{tab_name}!A:Z",
        valueInputOption="USER_ENTERED",
        body={"values": [values]}
    ).execute()

    return True


def guardar_memoria(mensaje_usuario, respuesta_agente, telefono="", tema="general"):
    return append_row("Memoria", [
        datetime.now().isoformat(),
        telefono,
        mensaje_usuario,
        respuesta_agente,
        tema
    ])


def guardar_encuesta(nombre, telefono, rating, comentario):
    return append_row("customer service survey", [
        datetime.now().isoformat(),
        nombre,
        telefono,
        rating,
        comentario
    ])


def guardar_cliente(nombre, telefono, puntos=5):
    return append_row("clientes", [
        datetime.now().isoformat(),
        nombre,
        telefono,
        puntos
    ])


def guardar_reward(telefono, accion="registro", puntos=5, saldo=5):
    return append_row("recompensas", [
        datetime.now().isoformat(),
        telefono,
        accion,
        puntos,
        saldo
    ])


def guardar_log(evento, resultado="OK", error=""):
    return append_row("Logs", [
        datetime.now().isoformat(),
        evento,
        resultado,
        error
    ])