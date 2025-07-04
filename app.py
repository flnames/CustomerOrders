from flask import Flask, request, jsonify, abort, url_for
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
EXCEL_FILE = "CustomerOrders.xlsx"
PER_PAGE = 25

app = Flask(__name__)

# 🔐 Authorization check
def require_api_key():
    token = request.headers.get("Authorization")
    if token != f"Bearer {API_KEY}":
        abort(401, description="Unauthorized: Invalid API Key")

# 🟢 Health check endpoint for Render
@app.route("/")
def index():
    return "OK", 200

# 📦 Load Excel data once at startup
try:
    if not os.path.isfile(EXCEL_FILE):
        print(f"[ERROR] '{EXCEL_FILE}' not found.")
        data = []
    else:
        df = pd.read_excel(EXCEL_FILE)
        data = df.to_dict(orient="records")
        print(f"[INFO] Loaded {len(data)} records from '{EXCEL_FILE}'")
except Exception as e:
    print(f"[ERROR] Failed to read Excel file: {e}")
    data = []

# 📊 /data endpoint with pagination
@app.route("/CustomerOrders", strict_slashes=False)
def get_data():
    require_api_key()

    # Parse page number
    try:
        page = int(request.args.get("page", 1))
        if page <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid 'page' parameter"}), 400

    # Pagination logic
    total_rows = len(data)
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    paginated = data[start:end]
    has_more = end < total_rows

    return jsonify({
        "page": page,
        "per_page": PER_PAGE,
        "total_rows": total_rows,
        "has_more": has_more,
        "next_page": url_for('get_data', page=page + 1, _external=True) if has_more else None,
        "data": paginated
    })

# 🔐 Handle auth errors
@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": str(e)}), 401

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render compatibility
    app.run(host="0.0.0.0", port=port)
