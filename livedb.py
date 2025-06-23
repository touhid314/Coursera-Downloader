import os
import uuid
import requests
import json
from datetime import datetime, timezone
import platform
from packaging import version

from localdb import SimpleDB
from maingui import __version__

API_KEY, PROJECT_ID = SimpleDB().get_remote_config()

# === Authentication ===
def authenticate_anonymously():
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
    try:
        res = requests.post(url, json={"returnSecureToken": True}, timeout=5)
        return res.json().get("idToken")
    except:
        return None

# === check for update ===
def get_latest_version(id_token):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/maindb/app_info"
    headers = {"Authorization": f"Bearer {id_token}"}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        doc = res.json()
        version_field = doc.get("fields", {}).get("latest_version", {})
        latest_version_build_url = doc.get("fields", {}).get("latest_version_build_url", {})
        update_msg = doc.get("fields", {}).get("update_msg", {})
        return version_field.get("stringValue"), latest_version_build_url.get("stringValue"), update_msg.get("stringValue")
    except:
        return None, None, None

def check_for_update(id_token):
    latest_version, latest_version_build_url, update_msg = get_latest_version(id_token)
    current_version =  __version__

    if latest_version and current_version:
        try:
            if version.parse(latest_version) > version.parse(current_version):
                return True, latest_version, latest_version_build_url, update_msg
            else:
                return False, current_version, latest_version_build_url, update_msg
        except:
            return None, current_version, None, None
    else:
        return None, current_version, None, None

# === get notification ===
def get_notification(id_token):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/maindb/push_notification"
    headers = {"Authorization": f"Bearer {id_token}"}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        doc = res.json()
        return doc.get("fields", {}).get("markup_text", {}).get("stringValue")
    except:
        return None

# === log_usage_info ===
def log_usage_info(id_token):
    doc_id = make_doc_id()
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/usage_info/{doc_id}"

    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }

    firestore_data = {
        "fields": {
            "user_id": {"stringValue": get_set_user_id()},
            "country": {"stringValue": get_country()},
            "app_version": {"stringValue": __version__},
            "time": {"timestampValue": datetime.now(timezone.utc).isoformat()},
            "platform": {"stringValue": platform.system()}
        }
    }

    try:
        requests.patch(url, headers=headers, data=json.dumps(firestore_data), timeout=5)
    except:
        pass

def get_set_user_id():
    try:
        db = SimpleDB()
        user_id = db.read('user_id')
        if user_id is None:
            user_id = str(uuid.uuid4())
            db.create('user_id', user_id)
        return user_id
    except:
        return str(uuid.uuid4())

def get_country():
    try:
        res = requests.get("https://ipinfo.io/json", timeout=5)
        data = res.json()
        return data.get("country", "Unknown")
    except:
        return "Unknown"

def make_doc_id():
    try:
        return f"{get_set_user_id()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    except:
        return str(uuid.uuid4())

# === Main ===
if __name__ == "__main__":
    id_token = authenticate_anonymously()
    log_usage_info(id_token)
    check_for_update(id_token)
    get_notification(id_token)
    