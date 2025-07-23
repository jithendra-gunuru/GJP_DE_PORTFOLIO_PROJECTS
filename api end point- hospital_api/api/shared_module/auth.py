import os
from functools import wraps
from flask import request, jsonify, current_app

# Try importing Google Secret Manager
try:
    from google.cloud import secretmanager
    SECRET_MANAGER = True
except ImportError:
    SECRET_MANAGER = False

def fetch_api_key():
    """
    Fetch the API key from Google Secret Manager if available,
    else fallback to environment variable (for local/dev).
    """
    if SECRET_MANAGER:
        secret_id = os.environ.get(
            "API_KEY_SECRET_ID",
            "projects/<YOUR_PROJECT_ID>/secrets/hospital-api-key/versions/latest"
        )
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": secret_id})
        api_key = response.payload.data.decode("UTF-8")
        print(f"API_KEY Loaded from GSM: '{api_key}'")
        return api_key
    else:
        api_key = os.environ.get("API_KEY", "your-very-secure-api-key")
        print(f"API_KEY Loaded from ENV: '{api_key}'")
        return api_key

API_KEY = fetch_api_key()

def require_api_key(func):
    """Flask decorator to enforce x-api-key auth on protected routes."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Support header: x-api-key
        api_key_header = request.headers.get("x-api-key")
        if not api_key_header or api_key_header.strip() != API_KEY.strip():
            # Optional: Log unauthorized attempt
            if current_app and hasattr(current_app, "logger"):
                current_app.logger.warning("Unauthorized access attempt.")
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

