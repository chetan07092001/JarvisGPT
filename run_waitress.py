from waitress import serve
from app import app  # Ensure this matches the name of your Flask app module

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)