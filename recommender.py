import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
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

    # Campos para construir las features
    cols = ['nombre', 'descripcion', 'categoria_id', 'material_id', 'tecnica_id', 'municipio_venta', 'color']
    cols_existentes = [c for c in cols if c in df.columns]

    # Combinar todo en una sola cadena de texto
    df['features'] = df[cols_existentes].fillna("").astype(str).agg(' '.join, axis=1)
    return df


def cargar_tiendas():
    engine = get_engine()
    query = """
    SELECT id, user_id, nombre, barrio, municipio_venta, latitude, longitude
    FROM tiendas;
    """
    return pd.read_sql_query(query, engine)


# =========================
# PREFERENCIAS / HISTORIAL
# =========================
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


def obtener_historial_cliente(user_id):
    engine = get_engine()
    query = f"""
    SELECT dt.id_producto, dt.id_tienda
    FROM transacciones t
    JOIN detalles_transaccion dt ON t.id_transaccion = dt.id_transaccion
    WHERE t.id_cliente = {user_id};
    """
    df_historial = pd.read_sql_query(query, engine)

    productos = df_historial['id_producto'].dropna().unique().tolist()
    tiendas = df_historial['id_tienda'].dropna().unique().tolist()

    return {"productos": productos, "tiendas": tiendas}


# =========================
# RECOMENDADOR DE PRODUCTOS (TF-IDF + Cosine + KNN)
# =========================
def recomendar_productos(user_id, limit=30, k=10):
    df = cargar_productos()

    # Preferencias o historial
    productos_input = obtener_preferencias_usuario(user_id)
    if len(productos_input) == 0:
        historial = obtener_historial_cliente(user_id)
        productos_input = historial["productos"]
    if len(productos_input) == 0:
        return []

    # Vectorización TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['features'])

    # Filtrar productos válidos
    ids_validos = [pid for pid in productos_input if pid in df['id'].values]
    if len(ids_validos) < 1:
        return []

    # Índices de los productos de referencia
    idxs = [df[df['id'] == pid].index[0] for pid in ids_validos]
    selected_vectors = tfidf_matrix[idxs]

    # Modelo KNN (cosine similarity)
    knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=min(k, len(df)))
    knn.fit(tfidf_matrix)

    # Vecinos más cercanos
    distances, indices = knn.kneighbors(selected_vectors, n_neighbors=limit)

    # Aplanar y limpiar duplicados
    indices_flat = np.unique(indices.flatten())

    # Calcular similitud promedio (invirtiendo distancia)
    mean_distances = []
    for idx in indices_flat:
        # Tomar todas las distancias donde aparece ese índice
        dists = distances[:, np.where(indices == idx)[1]]
        if len(dists.flatten()) > 0:
            mean_distances.append(1 - np.mean(dists))
        else:
            mean_distances.append(0)

    # Crear dataframe de recomendados con similitudes alineadas
    recomendados = df.iloc[indices_flat].copy()
    recomendados['similitud'] = mean_distances

    # Excluir productos ya vistos
    recomendados = recomendados[~recomendados['id'].isin(ids_validos)]
    recomendados = recomendados.sort_values(by='similitud', ascending=False).head(limit)

    return recomendados[['id']].to_dict(orient="records")


# =========================
# RECOMENDADOR DE TIENDAS (TF-IDF + Cosine + KNN)
# =========================
def recomendar_tiendas(user_id, limit=15, k=10):
    df_productos = cargar_productos()
    df_tiendas = cargar_tiendas()

    # Preferencias o historial
    productos_input = obtener_preferencias_usuario(user_id)
    if len(productos_input) == 0:
        historial = obtener_historial_cliente(user_id)
        productos_input = historial["productos"]
    if len(productos_input) == 0:
        return []

    df_seleccionados = df_productos[df_productos['id'].isin(productos_input)]
    if df_seleccionados.empty:
        return []

    user_ids_tiendas_base = df_seleccionados['user_id'].unique()
    tiendas_base = df_tiendas[df_tiendas['user_id'].isin(user_ids_tiendas_base)]
    if tiendas_base.empty:
        return []

    # Features de tiendas
    cols_tiendas = ['nombre', 'barrio', 'municipio_venta']
    df_tiendas['features'] = df_tiendas[cols_tiendas].fillna("").astype(str).agg(' '.join, axis=1)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df_tiendas['features'])

    # Índices base
    idxs_base = df_tiendas[df_tiendas['id'].isin(tiendas_base['id'])].index
    selected_vectors = tfidf_matrix[idxs_base]

    # Modelo KNN
    knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=min(k, len(df_tiendas)))
    knn.fit(tfidf_matrix)

    distances, indices = knn.kneighbors(selected_vectors, n_neighbors=limit)
    indices_flat = np.unique(indices.flatten())

    # Calcular similitud promedio
    mean_distances = []
    for idx in indices_flat:
        dists = distances[:, np.where(indices == idx)[1]]
        if len(dists.flatten()) > 0:
            mean_distances.append(1 - np.mean(dists))
        else:
            mean_distances.append(0)

    recomendadas = df_tiendas.iloc[indices_flat].copy()
    recomendadas['similitud'] = mean_distances

    recomendadas = recomendadas[~recomendadas['id'].isin(tiendas_base['id'])]
    recomendadas = recomendadas.sort_values(by='similitud', ascending=False).head(limit)

    return recomendadas[['id']].to_dict(orient="records")