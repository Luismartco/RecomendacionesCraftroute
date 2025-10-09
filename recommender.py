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

    # Obtener user_ids de los productos seleccionados
    df_seleccionados = df_productos[df_productos['id'].isin(productos_input)]
    if df_seleccionados.empty:
        return []

    user_ids_tiendas_base = df_seleccionados['user_id'].unique()

    # Tiendas base (donde se crearon esos productos)
    tiendas_base = df_tiendas[df_tiendas['user_id'].isin(user_ids_tiendas_base)]
    if tiendas_base.empty:
        return []

    # Construir features de tiendas (puedes ajustar columnas)
    cols_tiendas = ['nombre', 'barrio', 'municipio_venta']
    df_tiendas['features'] = df_tiendas[cols_tiendas].fillna("").astype(str).agg(' '.join, axis=1)
    tiendas_base['features'] = tiendas_base[cols_tiendas].fillna("").astype(str).agg(' '.join, axis=1)

    # Vectorizar y calcular similitudes
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df_tiendas['features'])

    idxs_base = df_tiendas[df_tiendas['id'].isin(tiendas_base['id'])].index
    selected_vectors = tfidf_matrix[idxs_base]

    mean_vector = np.asarray(selected_vectors.mean(axis=0))
    similitudes = cosine_similarity(mean_vector, tfidf_matrix).flatten()

    df_tiendas['similitud'] = similitudes

    # Filtrar y ordenar
    recomendadas = df_tiendas[~df_tiendas['id'].isin(tiendas_base['id'])]
    recomendadas = recomendadas.sort_values(by='similitud', ascending=False).head(limit)

    return recomendadas[['id']].to_dict(orient="records")
