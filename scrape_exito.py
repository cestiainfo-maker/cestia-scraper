"""
Cestia — scraper de Éxito (categorías completas) que guarda directo en
Supabase. Pensado para correr como un robot programado en GitHub
Actions, sin límite de 6 minutos.

Cómo funciona, en simple:
  1. Recorre cada categoría de comida de Éxito, usando la MISMA ruta
     de texto que usa el propio sitio (ej.
     'mercado/lacteos-huevos-y-refrigerados/leche') — es el mismo
     mecanismo que ya usamos con éxito para palabras sueltas como
     'arroz', solo que aquí es la ruta completa de una categoría.
  2. Por cada una, va pidiendo páginas de 50 productos hasta que no
     queden más.
  3. Manda los datos a Supabase por su API.
"""

from __future__ import annotations
import os
import time
import requests

TIENDA = "exito"
DOMINIO = "https://tienda.exito.com"

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

TAMANO_PAGINA = 50

# (ruta de la categoría tal como la usa el sitio, nombre legible)
CATEGORIAS = [
    ("mercado/pollo-carne-y-pescado/pollo", "Pollo"),
    ("mercado/pollo-carne-y-pescado/carne-de-res", "Carne de res"),
    ("mercado/pollo-carne-y-pescado/carne-de-cerdo", "Carne de cerdo"),
    ("mercado/pollo-carne-y-pescado/pescados-y-mariscos", "Pescados y mariscos"),
    ("mercado/pollo-carne-y-pescado/otras-especies", "Otras especies"),
    ("mercado/charcuteria-y-delicatessen/quesos-especiales", "Quesos especiales"),
    ("mercado/charcuteria-y-delicatessen/carnes-especiales", "Carnes especiales (delicatessen)"),
    ("mercado/charcuteria-y-delicatessen/encurtidos-conservas-pates", "Encurtidos, conservas, patés"),
    ("mercado/frutas-y-verduras/frutas", "Frutas"),
    ("mercado/frutas-y-verduras/verduras-y-hortalizas", "Verduras y hortalizas"),
    ("mercado/frutas-y-verduras/hierbas-y-aromaticas", "Hierbas y aromáticas"),
    ("mercado/frutas-y-verduras/pulpa-y-fruta-congelada", "Pulpa y fruta congelada"),
    ("mercado/panaderia-y-reposteria/panaderia-y-pasteleria-empacada", "Panadería y pastelería empacada"),
    ("mercado/panaderia-y-reposteria/ingredientes-para-reposteria", "Ingredientes para repostería"),
    ("mercado/panaderia-y-reposteria/postres-y-tortas-frescas", "Postres y tortas frescas"),
    ("mercado/panaderia-y-reposteria/panaderia-fresca-y-artesanal", "Panadería fresca y artesanal"),
    ("mercado/despensa/cereales-y-granolas", "Cereales y granolas"),
    ("mercado/despensa/granos-y-arroz", "Granos y arroz"),
    ("mercado/despensa/aceites-y-vinagres", "Aceites y vinagres"),
    ("mercado/despensa/azucar-panela-y-endulzante", "Azúcar, panela y endulzante"),
    ("mercado/despensa/harinas-y-mezclas-para-preparar", "Harinas y mezclas para preparar"),
    ("mercado/despensa/pastas", "Pastas"),
    ("mercado/despensa/salsas-especias-y-condimentos", "Salsas, especias y condimentos"),
    ("mercado/despensa/enlatados-y-conservas", "Enlatados y conservas"),
    ("mercado/despensa/tortillas-y-tacos", "Tortillas y tacos"),
    ("mercado/despensa/sopas-y-cremas", "Sopas y cremas"),
    ("mercado/despensa/avena-en-hojuelas-y-en-polvo", "Avena en hojuelas y en polvo"),
    ("mercado/despensa/quinua-chia-y-otras-semillas", "Quinua, chía y otras semillas"),
    ("mercado/despensa/aromaticas-y-te", "Aromáticas y té"),
    ("mercado/despensa/cafe-chocolate-y-cremas-no-lacteas", "Café, chocolate y cremas no lácteas"),
    ("mercado/despensa/sal", "Sal"),
    ("mercado/despensa/mermeladas-dips-y-untables", "Mermeladas, dips y untables"),
    ("mercado/despensa/gelatinas-en-polvo", "Gelatinas en polvo"),
    ("mercado/despensa/galletas", "Galletas"),
    ("mercado/despensa/bebidas-en-polvo", "Bebidas en polvo"),
    ("mercado/lacteos-huevos-y-refrigerados/mantequilla-y-margarina", "Mantequilla y margarina"),
    ("mercado/lacteos-huevos-y-refrigerados/carnes-frias-y-embutidos", "Carnes frías y embutidos"),
    ("mercado/lacteos-huevos-y-refrigerados/leche", "Leche"),
    ("mercado/lacteos-huevos-y-refrigerados/leches-saborizadas", "Leches saborizadas"),
    ("mercado/lacteos-huevos-y-refrigerados/leches-en-polvo", "Leches en polvo"),
    ("mercado/lacteos-huevos-y-refrigerados/huevos", "Huevos"),
    ("mercado/lacteos-huevos-y-refrigerados/yogurt-y-bebidas-lacteas", "Yogurt y bebidas lácteas"),
    ("mercado/lacteos-huevos-y-refrigerados/quesos-quesitos-y-cuajadas", "Quesos, quesitos y cuajadas"),
    ("mercado/lacteos-huevos-y-refrigerados/postres-refrigerados", "Postres refrigerados"),
    ("mercado/lacteos-huevos-y-refrigerados/cremas-de-leche-queso-cremas-y-sueros", "Cremas de leche, queso crema y sueros"),
    ("mercado/lacteos-huevos-y-refrigerados/arepas", "Arepas"),
    ("mercado/congelados/comidas-congeladas", "Comidas congeladas"),
    ("mercado/congelados/helados", "Helados"),
    ("mercado/congelados/papas-yucas-y-verduras-congeladas", "Papas, yucas y verduras congeladas"),
    ("mercado/congelados/pasabocas-y-panaderia-congelados", "Pasabocas y panadería congelados"),
    ("mercado/pasabocas-y-snacks/pasabocas-para-preparar", "Pasabocas para preparar"),
    ("mercado/pasabocas-y-snacks/nueces-pistachos-y-frutos-secos", "Nueces, pistachos y frutos secos"),
    ("mercado/pasabocas-y-snacks/papas-fritas-y-paquetes", "Papas fritas y paquetes"),
    ("mercado/bebidas/agua-y-te", "Agua y té"),
    ("mercado/bebidas/bebidas-de-cereal", "Bebidas de cereal"),
    ("mercado/bebidas/gaseosas-y-sodas", "Gaseosas y sodas"),
    ("mercado/bebidas/hidratantes-y-energizantes", "Hidratantes y energizantes"),
    ("mercado/bebidas/jugos", "Jugos"),
    ("mercado/bebidas/otras-bebidas", "Otras bebidas"),
    ("mercado/dulces-y-chocolateria/arequipe-y-leche-condensada", "Arequipe y leche condensada"),
    ("mercado/dulces-y-chocolateria/chocolateria", "Chocolatería"),
    ("mercado/dulces-y-chocolateria/confiteria", "Confitería"),
    ("mercado/dulces-y-chocolateria/dulces-tipicos", "Dulces típicos"),
    ("mercado/comidas-preparadas/arroces", "Arroces preparados"),
    ("mercado/comidas-preparadas/ensaladas", "Ensaladas preparadas"),
]


def guardar_en_supabase(filas: list[dict]) -> None:
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


def scrapear_categoria(ruta: str, nombre: str) -> int:
    total_guardados = 0
    offset = 0
    while True:
        url = f"{DOMINIO}/api/catalog_system/pub/products/search/{ruta}?_from={offset}&_to={offset + TAMANO_PAGINA - 1}"
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
                "Referer": f"{DOMINIO}/",
            },
            timeout=20,
        )
        if resp.status_code == 429:
            time.sleep(3)
            continue
        if resp.status_code not in (200, 206):
            print(f"  [{nombre}] error HTTP {resp.status_code}, se salta")
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
                            "category": nombre,
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
        time.sleep(0.5)

    return total_guardados


def main():
    gran_total = 0
    for ruta, nombre in CATEGORIAS:
        guardados = scrapear_categoria(ruta, nombre)
        gran_total += guardados
        print(f"{nombre}: {guardados} precios guardados")
    print(f"\nTOTAL: {gran_total} precios guardados en Supabase.")


if __name__ == "__main__":
    main()
