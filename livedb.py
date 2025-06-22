import os
import uuid
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import pickle

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")

# === Firebase Authentication ===
def authenticate_anonymously():
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
    res = requests.post(url, json={"returnSecureToken": True})
    res.raise_for_status()
    id_token = res.json()["idToken"]
    return id_token

# === Store JSON in Firestore ===
def log_usage_info(id_token):
    doc_id = make_doc_id()
    usage_data = get_session_info()

    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/usage_info/{doc_id}"

    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }

    # Convert Python dict to Firestore format
    firestore_data = {
        "fields": {
            "user_id": {"stringValue": usage_data["user_id"]},
            "country": {"stringValue": usage_data["country"]},
            "app_version": {"stringValue": usage_data["app_version"]},
            "time": {"timestampValue": usage_data["time"]}
        }
    }

    res = requests.patch(url, headers=headers, data=json.dumps(firestore_data))
    res.raise_for_status()

# === get_usage_info ===
from datetime import datetime, timezone

def get_set_user_id():
    try:
        with open('data.bin', 'rb') as f:
            data = pickle.load(f)
    except (EOFError, pickle.UnpicklingError, FileNotFoundError):
        return "-1"

    if 'user_id' in data:
        return data['user_id']
    else:
        user_id = str(uuid.uuid4())
        data['user_id'] = user_id
        with open('data.bin', 'wb') as f:
            pickle.dump(data, f)
        return user_id
    
def get_country():
    try:
        # Get public IP-based country location info from a free API
        res = requests.get("https://ipinfo.io/json")
        res.raise_for_status()
        data = res.json()
        country = data.get("country", "Unknown")
    except Exception:
        country = "Unknown"
    return country

def make_doc_id():
    # Generate a document ID based on user ID and current timestamp
    return f"{get_set_user_id()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def get_session_info():
    # Get session information
    return {
        "user_id": get_set_user_id(),
        "app_version": os.getenv("VERSION"),  
        "country": get_country(),
        "time": datetime.now(timezone.utc).isoformat()
    }
    

# === Main ===
if __name__ == "__main__":
    id_token = authenticate_anonymously()
    log_usage_info(id_token)

