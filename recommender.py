import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
from config import get_engine

# =========================
# CARGA DE DATOS
# =========================
def cargar_productos():
    engine = get_engine()
    query = """
    SELECT id, user_id, nombre, descripcion, precio, categoria_id, municipio_venta, tecnica_id, material_id, color
    FROM productos;
    """
    df = pd.read_sql_query(query, engine)

    # columnas que usamos para construir features
    cols = ['descripcion', 'categoria', 'municipio_venta', 'tecnica_artesanal', 'materia_prima', 'color']
    cols_existentes = [c for c in cols if c in df.columns]

    if not cols_existentes:
        df['features'] = ""
    else:
        df['features'] = df[cols_existentes].fillna("").astype(str).agg(' '.join, axis=1)

    return df


def cargar_tiendas():
    engine = get_engine()
    query = """
    SELECT id, user_id, nombre, barrio, municipio_venta, latitude, longitude
    FROM tiendas;
    """
    return pd.read_sql_query(query, engine)


def obtener_preferencias_usuario(user_id):
    engine = get_engine()
    query = f"SELECT selected_preferences FROM user_preferences WHERE user_id = {user_id}"
    df_pref = pd.read_sql_query(query, engine)

    if df_pref.empty:
        return []

    try:
        return json.loads(df_pref['selected_preferences'].iloc[0])
    except:
        return []


# =========================
# RECOMENDACIONES
# =========================
def recomendar_productos(user_id, limit=30):
    df = cargar_productos()
    productos_input = obtener_preferencias_usuario(user_id)

    if len(productos_input) == 0:
        return []

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['features'])

    ids_validos = [pid for pid in productos_input if pid in df['id'].values]

    if len(ids_validos) < 1:
        return []

    idxs = [df[df['id'] == pid].index[0] for pid in ids_validos]
    selected_vectors = tfidf_matrix[idxs]
    mean_vector = np.asarray(selected_vectors.mean(axis=0))

    similitudes = cosine_similarity(mean_vector, tfidf_matrix).flatten()
    df['similitud'] = similitudes
    recomendados = df[~df['id'].isin(ids_validos)].sort_values(by='similitud', ascending=False)

    recomendados = recomendados.head(limit)

    return recomendados[['id']].to_dict(orient="records")


def recomendar_tiendas(user_id, limit=15):
    df_productos = cargar_productos()
    df_tiendas = cargar_tiendas()
    productos_input = obtener_preferencias_usuario(user_id)

    if len(productos_input) == 0:
        return []

    # Paso 1: obtener recomendaciones de productos (para ampliar cobertura)
    productos_recomendados = recomendar_productos(user_id, limit=50)
    ids_recomendados = [p['id'] for p in productos_recomendados]

    # Paso 2: productos favoritos + recomendados
    df_seleccionados = df_productos[df_productos['id'].isin(productos_input + ids_recomendados)]

    # Paso 3: user_id de las tiendas que venden esos productos
    user_ids_tiendas = df_seleccionados['user_id'].unique()

    # Paso 4: filtrar tiendas
    tiendas_relacionadas = df_tiendas[df_tiendas['user_id'].isin(user_ids_tiendas)]

    # Paso 5: si hay menos de "limit", rellenar con tiendas aleatorias para completar
    if len(tiendas_relacionadas) < limit:
        restantes = limit - len(tiendas_relacionadas)
        otras = df_tiendas[~df_tiendas['user_id'].isin(user_ids_tiendas)]
        if len(otras) > 0:
            otras_sample = otras.sample(min(restantes, len(otras)), random_state=42)
            tiendas_relacionadas = pd.concat([tiendas_relacionadas, otras_sample])

    # Paso 6: limitar a "limit" final
    tiendas_relacionadas = tiendas_relacionadas.head(limit)

    return tiendas_relacionadas[['id']].to_dict(orient="records")