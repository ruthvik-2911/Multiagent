import os
import json
import datetime
from threading import Lock

LOG_FILE = "backend/storage/activity_log.json"
_lock = Lock()

def _ensure_file():
    if not os.path.exists("backend/storage"):
        os.makedirs("backend/storage")
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def log_activity(event: str, source: str, status: str = "Success", timestamp: str = None):
    _ensure_file()
    if not timestamp:
        timestamp = datetime.datetime.now().isoformat()
        
    activity = {
        "timestamp": timestamp,
        "event": event,
        "source": source,
        "status": status
    }
    
    with _lock:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
                
        logs.insert(0, activity) # Prepend
        
        # Limit to 1000 to prevent bloat
        if len(logs) > 1000:
            logs = logs[:1000]
            
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)

def get_activities(limit=50):
    _ensure_file()
    with _lock:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
                return logs[:limit]
            except json.JSONDecodeError:
                return []
