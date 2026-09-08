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
DOMINIO = "https://www.exito.com"

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
    ("mercado/panaderia-y-reposteria/ingredi
