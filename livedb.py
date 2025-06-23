import os
import uuid
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import pickle
import platform
from packaging import version


# Load environment variables
load_dotenv()

import localdb
API_KEY, PROJECT_ID = localdb.SimpleDB().get_remote_config()

# === Authentication ===
def authenticate_anonymously():
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
    res = requests.post(url, json={"returnSecureToken": True})
    res.raise_for_status()
    id_token = res.json()["idToken"]
    return id_token



# === check for update ===
def get_latest_version(id_token):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/maindb/app_info"
    headers = {"Authorization": f"Bearer {id_token}"}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    doc = res.json()

    # Extract the version from Firestore document fields
    version_field = doc.get("fields", {}).get("latest_version", {})
    latest_version_build_url = doc.get("fields", {}).get("latest_version_build_url", {})
    update_msg = doc.get("fields", {}).get("update_msg", {})

    return version_field.get("stringValue"), latest_version_build_url.get("stringValue"), update_msg.get("stringValue")


def check_for_update(id_token):
    """ Check if the current app version is up-to-date with the latest version.
        returns - 
            True, latest_version, latest_version_build_url if an update is available; False, current version otherwise.
            If the latest version cannot be determined, it returns None, current version.
    """
    latest_version, latest_version_build_url, update_msg = get_latest_version(id_token)
    current_version = os.getenv("VERSION")

    if latest_version and current_version:
        if version.parse(latest_version) > version.parse(current_version):
            return True, latest_version, latest_version_build_url, update_msg
        else:
            return False, current_version, latest_version_build_url, update_msg
    else:
        return None, current_version, None, None
    

# === push notification ===
def get_notification(id_token):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/maindb/push_notification"
    headers = {"Authorization": f"Bearer {id_token}"}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    doc = res.json()
    return doc.get("fields", {}).get("markup_text", {}).get("stringValue")


# === Store JSON in Firestore ===
def log_usage_info(id_token):
    doc_id = make_doc_id()

    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/usage_info/{doc_id}"

    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }

    # Convert Python dict to Firestore format
    firestore_data = {
        "fields": {
            "user_id": {"stringValue": get_set_user_id()},
            "country": {"stringValue": get_country()},
            "app_version": {"stringValue": os.getenv("VERSION")},
            "time": {"timestampValue": datetime.now(timezone.utc).isoformat()},
            "platform": {"stringValue": platform.system()}
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

    

# === Main ===
if __name__ == "__main__":
    id_token = authenticate_anonymously()
    # log_usage_info(id_token)
    # has_update, latest_version = check_for_update(id_token)
    # print(f"Update available: {has_update}, Latest version: {latest_version}")

    print(get_notification(id_token))

