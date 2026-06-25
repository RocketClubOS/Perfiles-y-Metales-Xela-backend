import json
import os
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials


CLIENTES_SHEET = "Clientes"
MOVIMIENTOS_SHEET = "Movimientos"

CLIENTES_HEADERS = [
    "telefono",
    "nombre",
    "ciudad",
    "tipo_cliente",
    "saldo",
    "fecha_registro",
]

MOVIMIENTOS_HEADERS = [
    "telefono",
    "fecha",
    "tipo",
    "monto_compra",
    "saldo_ganado",
    "producto",
    "nota",
]


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_service_account_info():
    raw_value = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not raw_value:
        raise RuntimeError("Falta configurar GOOGLE_SERVICE_ACCOUNT_JSON.")

    if os.path.exists(raw_value):
        with open(raw_value, "r", encoding="utf-8") as service_file:
            return json.load(service_file)

    service_info = json.loads(raw_value)

    if "private_key" in service_info:
        service_info["private_key"] = service_info["private_key"].replace("\\n", "\n")

    return service_info


def _get_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        _load_service_account_info(),
        scopes=scopes,
    )
    return gspread.authorize(credentials)


def _ensure_worksheet(spreadsheet, title, headers):
    try:
        worksheet = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(headers))

    current_headers = worksheet.row_values(1)

    if current_headers != headers:
        worksheet.update(values=[headers], range_name="A1")

    return worksheet


def get_sheet():
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    if not sheet_id:
        raise RuntimeError("Falta configurar GOOGLE_SHEET_ID.")

    spreadsheet = _get_client().open_by_key(sheet_id)
    _ensure_worksheet(spreadsheet, CLIENTES_SHEET, CLIENTES_HEADERS)
    _ensure_worksheet(spreadsheet, MOVIMIENTOS_SHEET, MOVIMIENTOS_HEADERS)
    return spreadsheet


def _clientes_ws():
    return get_sheet().worksheet(CLIENTES_SHEET)


def _movimientos_ws():
    return get_sheet().worksheet(MOVIMIENTOS_SHEET)


def normalizar_telefono(telefono):
    digits = "".join(ch for ch in str(telefono or "") if ch.isdigit())

    if len(digits) == 11 and digits.startswith("502"):
        digits = digits[3:]

    return digits


def _find_cliente_row(telefono):
    telefono = normalizar_telefono(telefono)
    worksheet = _clientes_ws()
    records = worksheet.get_all_records()

    for index, cliente in enumerate(records, start=2):
        if normalizar_telefono(cliente.get("telefono")) == telefono:
            return worksheet, index, cliente

    return worksheet, None, None


def _format_cliente(cliente):
    if not cliente:
        return None

    return {
        "telefono": normalizar_telefono(cliente.get("telefono")),
        "nombre": cliente.get("nombre", ""),
        "ciudad": cliente.get("ciudad", ""),
        "tipo_cliente": cliente.get("tipo_cliente", ""),
        "saldo": float(cliente.get("saldo") or 0),
        "fecha_registro": cliente.get("fecha_registro", ""),
    }


def cliente_existe(telefono):
    _, row_index, _ = _find_cliente_row(telefono)
    return row_index is not None


def crear_cliente(data):
    telefono = normalizar_telefono(data.get("telefono"))

    if cliente_existe(telefono):
        return obtener_cliente(telefono)

    cliente = {
        "telefono": telefono,
        "nombre": str(data.get("nombre", "")).strip(),
        "ciudad": str(data.get("ciudad", "")).strip(),
        "tipo_cliente": str(data.get("tipo_cliente", "")).strip(),
        "saldo": 0,
        "fecha_registro": _now(),
    }

    _clientes_ws().append_row(
        [cliente[key] for key in CLIENTES_HEADERS],
        value_input_option="USER_ENTERED",
    )

    return cliente


def obtener_cliente(telefono):
    _, _, cliente = _find_cliente_row(telefono)
    return _format_cliente(cliente)


def obtener_movimientos(telefono):
    telefono = normalizar_telefono(telefono)
    movimientos = []

    for movimiento in _movimientos_ws().get_all_records():
        if normalizar_telefono(movimiento.get("telefono")) == telefono:
            movimientos.append({
                "telefono": telefono,
                "fecha": movimiento.get("fecha", ""),
                "tipo": movimiento.get("tipo", ""),
                "monto_compra": float(movimiento.get("monto_compra") or 0),
                "saldo_ganado": float(movimiento.get("saldo_ganado") or 0),
                "producto": movimiento.get("producto", ""),
                "nota": movimiento.get("nota", ""),
            })

    return movimientos


def agregar_compra(telefono, monto_compra, producto, nota):
    telefono = normalizar_telefono(telefono)
    monto_compra = float(monto_compra)
    saldo_ganado = round(monto_compra * 0.01, 2)

    clientes_ws, row_index, cliente = _find_cliente_row(telefono)

    if not cliente:
        return None

    saldo_actual = float(cliente.get("saldo") or 0)
    nuevo_saldo = round(saldo_actual + saldo_ganado, 2)

    saldo_column = CLIENTES_HEADERS.index("saldo") + 1
    clientes_ws.update_cell(row_index, saldo_column, nuevo_saldo)

    _movimientos_ws().append_row(
        [
            telefono,
            _now(),
            "compra",
            monto_compra,
            saldo_ganado,
            str(producto or "").strip(),
            str(nota or "").strip(),
        ],
        value_input_option="USER_ENTERED",
    )

    return {
        "saldo_ganado": saldo_ganado,
        "nuevo_saldo": nuevo_saldo,
    }
