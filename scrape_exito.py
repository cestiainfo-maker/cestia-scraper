"""
Cestia — scraper de Éxito (categorías completas) que guarda directo en
Supabase. Pensado para correr como un robot programado en GitHub
Actions, sin límite de 6 minutos.

Cómo funciona, en simple:
  1. Recorre cada categoría de comida de Éxito (la lista CATEGORIAS).
  2. Por cada una, va pidiendo páginas de 50 productos hasta que no
     queden más (igual que hacía el script de Apps Script).
  3. En vez de escribir en una hoja de Sheets, manda los datos por
     internet a Supabase usando su API — Supabase se encarga de
     guardarlo en la base de datos real.

Este script NO guarda contraseñas ni claves adentro: las lee de
variables de entorno (SUPABASE_URL y SUPABASE_KEY), que en GitHub
Actions se configuran como "secrets" — así la clave nunca queda
visible en el código ni en el repositorio.
"""

from __future__ import annotations
import os
import time
import requests

TIENDA = "exito"
DOMINIO = "https://tienda.exito.com"

SUPABASE_URL = os.environ["SUPABASE_URL"]   # ej. https://xxxxx.supabase.co
SUPABASE_KEY = os.environ["SUPABASE_KEY"]   # la "service_role key" de Supabase

TAMANO_PAGINA = 50

# Mismas categorías que identificamos del árbol real de Éxito
CATEGORIAS = [
    (34185216, "Pollo"), (34185217, "Carne de res"), (34185218, "Carne de cerdo"),
    (34185219, "Pescados y mariscos"), (34185220, "Otras especies"),
    (34185230, "Quesos especiales"), (34185231, "Carnes especiales (delicatessen)"),
    (34185234, "Encurtidos, conservas, patés"), (34185235, "Frutas"),
    (34185236, "Verduras y hortalizas"), (34185237, "Hierbas y aromáticas"),
    (34693894, "Pulpa y fruta congelada"), (34185240, "Panadería y pastelería empacada"),
    (34185245, "Ingredientes para repostería"), (34185247, "Postres y tortas frescas"),
    (34185250, "Panadería fresca y artesanal"), (34185251, "Cereales y granolas"),
    (34185252, "Granos y arroz"), (34185253, "Aceites y vinagres"),
    (34185254, "Azúcar, panela y endulzante"), (34185255, "Harinas y mezclas para preparar"),
    (34185256, "Pastas"), (34185257, "Salsas, especias y condimentos"),
    (34185258, "Enlatados y conservas"), (34185259, "Tortillas y tacos"),
    (34185260, "Sopas y cremas"), (34185261, "Avena en hojuelas y en polvo"),
    (34185263, "Quinua, chía y otras semillas"), (34185264, "Aromáticas y té"),
    (34185268, "Café, chocolate y cremas no lácteas"), (34185270, "Sal"),
    (34185276, "Mermeladas, dips y untables"), (34185277, "Gelatinas en polvo"),
    (34185278, "Galletas"), (346085358, "Bebidas en polvo"),
    (34185228, "Mantequilla y margarina"), (34185229, "Carnes frías y embutidos"),
    (34185291, "Leche"), (34185292, "Leches saborizadas"), (34185293, "Leches en polvo"),
    (34185294, "Huevos"), (34185296, "Yogurt y bebidas lácteas"),
    (34185297, "Quesos, quesitos y cuajadas"), (34185298, "Postres refrigerados"),
    (34185300, "Cremas de leche, queso crema y sueros"), (34185301, "Arepas"),
    (34185302, "Comidas congeladas"), (34185305, "Helados"),
    (34185308, "Papas, yucas y verduras congeladas"), (34185309, "Pasabocas y panadería congelados"),
    (34185311, "Pasabocas para preparar"), (34185312, "Nueces, pistachos y frutos secos"),
    (34185313, "Papas fritas y paquetes"), (346084842, "Agua y té"),
    (346084843, "Bebidas de cereal"), (346084844, "Gaseosas y sodas"),
    (346084845, "Hidratantes y energizantes"), (346084846, "Jugos"),
    (346098538, "Otras bebidas"), (347532250, "Arequipe y leche condensada"),
    (347532251, "Chocolatería"), (347532252, "Confitería"), (347532253, "Dulces típicos"),
    (348959798, "Arroces preparados"), (348959801, "Ensaladas preparadas"),
]


def guardar_en_supabase(filas: list[dict]) -> None:
    """Manda un lote de filas a la tabla price_snapshots de Supabase."""
    if not filas:
        return
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/price_snapshots",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json=filas,
        timeout=30,
    )
    if resp.status_code >= 300:
        print("Error guardando en Supabase:", resp.status_code, resp.text[:300])


def scrapear_categoria(cat_id: int, cat_nombre: str) -> int:
    total_guardados = 0
    offset = 0
    while True:
        url = (
            f"{DOMINIO}/api/catalog_system/pub/products/search"
            f"?fq=C:{cat_id}&_from={offset}&_to={offset + TAMANO_PAGINA - 1}"
        )
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=20,
        )
        if resp.status_code == 429:
            time.sleep(3)
            continue
        if resp.status_code not in (200, 206):
            print(f"  [{cat_nombre}] error HTTP {resp.status_code}, se salta")
            break

        datos = resp.json()
        if not datos:
            break

        filas = []
        for producto in datos:
            for item in producto.get("items", []):
                for vendedor in item.get("sellers", []):
                    oferta = vendedor.get("commertialOffer", {}) or {}
                    if oferta.get("Price"):
                        filas.append({
                            "store_code": TIENDA,
                            "category": cat_nombre,
                            "product_name": producto.get("productName"),
                            "price": oferta["Price"],
                            "regular_price": oferta.get("ListPrice"),
                            "in_stock": (oferta.get("AvailableQuantity", 0) or 0) > 0,
                        })

        guardar_en_supabase(filas)
        total_guardados += len(filas)

        if len(datos) < TAMANO_PAGINA:
            break
        offset += TAMANO_PAGINA
        time.sleep(0.5)  # ser buen ciudadano con el servidor de Éxito

    return total_guardados


def main():
    gran_total = 0
    for cat_id, cat_nombre in CATEGORIAS:
        guardados = scrapear_categoria(cat_id, cat_nombre)
        gran_total += guardados
        print(f"{cat_nombre}: {guardados} precios guardados")
    print(f"\nTOTAL: {gran_total} precios guardados en Supabase.")


if __name__ == "__main__":
    main()
