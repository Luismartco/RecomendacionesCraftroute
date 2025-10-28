from flask import Flask, jsonify, request
from recommender import recomendar_productos, recomendar_tiendas, obtener_preferencias_usuario, obtener_historial_cliente, cargar_productos

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
        # Cargar los datos base
        productos_df = cargar_productos()

        # Obtener preferencias y historial
        preferencias = obtener_preferencias_usuario(user_id)
        historial = obtener_historial_cliente(user_id)

        # ====== Preferencias ======
        if len(preferencias) > 0:
            tiendas_pref = (
                productos_df[productos_df["id"].isin(preferencias)]["user_id"]
                .dropna()
                .unique()
                .tolist()
            )
        else:
            tiendas_pref = []

        # ====== Historial ======
        productos_hist = historial.get("productos", [])
        tiendas_hist = historial.get("tiendas", [])

        # Si los productos del historial no tienen tiendas explícitas, se buscan
        if len(tiendas_hist) == 0 and len(productos_hist) > 0:
            tiendas_hist = (
                productos_df[productos_df["id"].isin(productos_hist)]["user_id"]
                .dropna()
                .unique()
                .tolist()
            )

        respuesta = {
            "user_id": user_id,
            "preferencias": {
                "id_productos": preferencias,
                "id_tiendas": tiendas_pref
            },
            "historial": {
                "id_productos": productos_hist,
                "id_tiendas": tiendas_hist
            }
        }

        return jsonify(respuesta), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5055)
