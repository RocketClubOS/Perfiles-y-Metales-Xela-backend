from Data.empresa_info import INFO_EMPRESA, ALIAS_EMPRESA
from inventory import search_product


def responder_info_empresa(question):
    question = question.lower()

    if any(alias in question for alias in ALIAS_EMPRESA["direccion"]):
      return (
    f"Estamos ubicados en {INFO_EMPRESA['direccion']}.\n\n"
    f"📍 Google Maps:\n{INFO_EMPRESA['google_maps']}\n\n"
    f"Si necesitas ayuda para llegar, escríbenos al WhatsApp {INFO_EMPRESA['whatsapp']}."
)

    if any(alias in question for alias in ALIAS_EMPRESA["telefono"]):
        return f"Puedes comunicarte con nosotros al WhatsApp {INFO_EMPRESA['whatsapp']} o llamarnos al {INFO_EMPRESA['telefono']}."

    if any(alias in question for alias in ALIAS_EMPRESA["productos"]):
        productos = ", ".join(INFO_EMPRESA["productos"])
        return f"En {INFO_EMPRESA['nombre']} ofrecemos: {productos}."

    if any(alias in question for alias in ALIAS_EMPRESA["calidad"]):
        calidad = ", ".join(INFO_EMPRESA["calidad"])
        return f"Trabajamos con estándares de calidad como: {calidad}."

    if any(alias in question for alias in ALIAS_EMPRESA["empresa"]):
        return f"{INFO_EMPRESA['nombre']}. {INFO_EMPRESA['slogan_1']} {INFO_EMPRESA['slogan_2']}"

    if any(alias in question for alias in ALIAS_EMPRESA["envio"]):
       return (
        "Para consultar envíos y entregas, por favor comunícate con nosotros "
        "al WhatsApp 4864-9231. Con gusto revisaremos disponibilidad, ubicación y costo de entrega."
    )
    return None


def build_product_name(product):
    parts = [
        product.get("familia", ""),
        product.get("forma", ""),
        product.get("acabado", ""),
        product.get("medida_normalizada", ""),
        product.get("unidad", ""),
        product.get("grueso", "")
    ]

    return " ".join(part for part in parts if part).strip()


def answer_customer(question):
    respuesta_empresa = responder_info_empresa(question)

    if respuesta_empresa:
        return respuesta_empresa

    results = search_product(question)

    if not results:return (
        "No encontré ese producto en el inventario. "
        "Por favor comunícate con nosotros al WhatsApp 4864-9231 "
        "y con gusto te ayudaremos a encontrar el material adecuado."
    )
    product = results[0]

    stock = int(float(product.get("stock", 0)))
    precio = product.get("precio_venta", "N/D")

    if stock > 0:
        disponibilidad = (f"Sí, contamos con disponibilidad de este producto."
        "Para confirmar tu orden escríbenos al WhatsApp 4864-9231."
    )
    else:
        disponibilidad = (
        "Por el momento no tenemos disponibilidad de este producto. "
        "Por favor comunícate con nosotros al WhatsApp 4864-9231 "
        "y uno de nuestros asesores te ayudará a encontrar una solución."
    )

    product_name = build_product_name(product)

    response = f"""
Sí, encontré este producto:

{product_name}

Precio de venta: Q{precio}
{disponibilidad}
"""

    return response