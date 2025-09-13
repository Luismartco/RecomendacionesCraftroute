from flask import Flask, jsonify, request
from recommender import recomendar_productos

app = Flask(__name__)

@app.route("/api/recomendaciones/<int:user_id>", methods=["GET"])
def obtener_recomendaciones(user_id):
    try:
        limit = request.args.get("limit", default=None, type=int)
        recomendaciones = recomendar_productos(user_id, limit)
        if not recomendaciones:
            return jsonify({"mensaje": "No hay recomendaciones para este usuario"}), 404
        return jsonify(recomendaciones)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5055)
