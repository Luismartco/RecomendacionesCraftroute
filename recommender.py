import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
from config import get_engine

def cargar_productos():
    engine = get_engine()
    query = """
    SELECT id, user_id, nombre, descripcion, precio, categoria, municipio_venta, tecnica_artesanal, materia_prima, color
    FROM productos;
    """
    df = pd.read_sql_query(query, engine)

    print("Columnas encontradas:", df.columns.tolist())

    # columnas que quieres usar
    cols = ['categoria', 'municipio_venta', 'tecnica_artesanal', 'materia_prima', 'color']
    cols_existentes = [c for c in cols if c in df.columns]

    if not cols_existentes:
        print("⚠️ No se encontraron columnas de características para generar features.")
        df['features'] = ""
    else:
        df['features'] = df[cols_existentes].astype(str).agg(' '.join, axis=1)

    return df

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

def recomendar_productos(user_id, limit=None):
    df = cargar_productos()
    print("\n=== Productos cargados ===")
    print(df[['id', 'nombre']].head())

    productos_input = obtener_preferencias_usuario(user_id)
    print(f"Preferencias usuario {user_id}:", productos_input)

    if len(productos_input) == 0:
        print("No hay preferencias.")
        return []

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['features'])

    ids_validos = [pid for pid in productos_input if pid in df['id'].values]
    print("IDs válidos encontrados en productos:", ids_validos)

    if len(ids_validos) < 1:
        print("Ningún ID de preferencia coincide con productos.id")
        return []

    idxs = [df[df['id'] == pid].index[0] for pid in ids_validos]
    selected_vectors = tfidf_matrix[idxs]
    mean_vector = np.asarray(selected_vectors.mean(axis=0))

    similitudes = cosine_similarity(mean_vector, tfidf_matrix).flatten()
    df['similitud'] = similitudes
    recomendados = df[~df['id'].isin(ids_validos)].sort_values(by='similitud', ascending=False)

    print("Productos recomendados encontrados:", len(recomendados))

    if limit:
        recomendados = recomendados.head(limit)

    return recomendados[['id', 'nombre', 'categoria', 'precio', 'municipio_venta', 'similitud']].to_dict(orient="records")
