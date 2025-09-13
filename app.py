from flask import Flask, jsonify, request
from recommender import recomendar_productos, recomendar_tiendas

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

if __name__ == "__main__":
    app.run(debug=True, port=5055)
