from flask import Flask, jsonify, request
from recommender import recomendar_productos, recomendar_tiendas, obtener_preferencias_usuario, obtener_historial_cliente, cargar_productos, cargar_tiendas

app = Flask(__name__)

@app.route("/recomendar_productos", methods=["GET"])
def api_recomendar_productos():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "Falta user_id"}), 400

    productos = recomendar_productos(user_id=user_id, limit=30)
    return jsonify(productos)

@app.route("/recomendar_tiendas", methods=["GET"])
def api_recomendar_tiendas():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "Falta user_id"}), 400

    tiendas = recomendar_tiendas(user_id=user_id, limit=15)
    return jsonify(tiendas)

@app.route("/ver_datos_usuario", methods=["GET"])
def ver_datos_usuario():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "Falta user_id"}), 400

    try:
        productos_df = cargar_productos()
        tiendas_df = cargar_tiendas()

        preferencias = obtener_preferencias_usuario(user_id)
        historial = obtener_historial_cliente(user_id)

        # Productos y tiendas completas para preferencias
        productos_pref_df = productos_df[productos_df["id"].isin(preferencias)]
        tiendas_pref_df = tiendas_df[tiendas_df["user_id"].isin(productos_pref_df["user_id"].unique())]

        # Productos y tiendas completas para historial
        productos_hist_df = productos_df[productos_df["id"].isin(historial.get("productos", []))]
        tiendas_hist_df = tiendas_df[tiendas_df["id"].isin(historial.get("tiendas", []))]

        respuesta = {
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
