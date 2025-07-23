import os

try:
    from google.cloud import secretmanager
    SECRET_MANAGER = True
except ImportError:
    SECRET_MANAGER = False

def get_api_key():
    """
    Fetch the API key from Google Secret Manager if available,
    else fallback to environment variable (for local/dev).
    """
    if SECRET_MANAGER:
        secret_id = os.environ.get(
            "API_KEY_SECRET_ID",
            "projects/gcp-de-vaarahi-b38/secrets/hospital-api-key/versions/latest"
        )
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": secret_id})
        return response.payload.data.decode("UTF-8")
    else:
        return os.environ.get("API_KEY", "your-very-secure-api-key")
