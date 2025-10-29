from flask import Flask, jsonify, request
from recommender import (
    recomendar_productos,
    recomendar_tiendas,
    obtener_preferencias_usuario,
    obtener_historial_cliente,
    cargar_productos,
    cargar_tiendas
)
import time  # ⏱️ Para medir rendimiento

app = Flask(__name__)

@app.route("/recomendar_productos", methods=["GET"])
def api_recomendar_productos():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "Falta user_id"}), 400

    inicio = time.time()  # ⏱️ Inicio de medición
    productos = recomendar_productos(user_id=user_id, limit=30)
    fin = time.time()  # ⏱️ Fin de medición
    tiempo_total = round(fin - inicio, 4)

    # 🧩 Colocamos el tiempo primero
    respuesta = {
        "tiempo_respuesta_segundos": tiempo_total,
        "user_id": user_id,
        "productos_recomendados": productos
    }

    return jsonify(respuesta)


@app.route("/recomendar_tiendas", methods=["GET"])
def api_recomendar_tiendas():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "Falta user_id"}), 400

    inicio = time.time()
    tiendas = recomendar_tiendas(user_id=user_id, limit=15)
    fin = time.time()
    tiempo_total = round(fin - inicio, 4)

    respuesta = {
        "tiempo_respuesta_segundos": tiempo_total,
        "user_id": user_id,
        "tiendas_recomendadas": tiendas
    }

    return jsonify(respuesta)


@app.route("/ver_datos_usuario", methods=["GET"])
def ver_datos_usuario():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "Falta user_id"}), 400

    inicio = time.time()  # ⏱️ Inicio de medición

    try:
        productos_df = cargar_productos()
        tiendas_df = cargar_tiendas()

        preferencias = obtener_preferencias_usuario(user_id)
        historial = obtener_historial_cliente(user_id)

        productos_pref_df = productos_df[productos_df["id"].isin(preferencias)]
        tiendas_pref_df = tiendas_df[tiendas_df["user_id"].isin(productos_pref_df["user_id"].unique())]

        productos_hist_df = productos_df[productos_df["id"].isin(historial.get("productos", []))]
        tiendas_hist_df = tiendas_df[tiendas_df["id"].isin(historial.get("tiendas", []))]

        fin = time.time()  # ⏱️ Fin de medición
        tiempo_total = round(fin - inicio, 4)

        # 🔝 Tiempo de respuesta arriba
        respuesta = {
            "tiempo_respuesta_segundos": tiempo_total,
            "user_id": user_id,
            "preferencias": {
                "productos": productos_pref_df.to_dict(orient="records"),
                "tiendas": tiendas_pref_df.to_dict(orient="records")
            },
            "historial": {
                "productos": productos_hist_df.to_dict(orient="records"),
                "tiendas": tiendas_hist_df.to_dict(orient="records")
            }
        }

        return jsonify(respuesta), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5055)
