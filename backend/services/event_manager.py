import os
import queue
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from backend.connectors.connector_manager import get as get_connector
from backend.services.indexer import index_enterprise_document, delete_enterprise_document

# Import to trigger registration
import backend.connectors.outlook_connector
import backend.connectors.sharepoint_connector
import backend.connectors.powerbi_connector
import backend.connectors.onedrive_connector

task_queue = queue.Queue()
_events = []

def push_sse_event(msg):
    _events.append({"timestamp": time.time(), "message": msg})

def get_new_events(last_timestamp):
    return [e for e in _events if e["timestamp"] > last_timestamp]

class EnterpriseFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filepath = event.src_path
            task_queue.put(("created", filepath))
            
    def on_deleted(self, event):
        if not event.is_directory:
            filepath = event.src_path
            task_queue.put(("deleted", filepath))

def worker_loop():
    while True:
        task = task_queue.get()
        if task is None:
            break
            
        action, filepath = task
        
        try:
            if action == "deleted":
                filename = os.path.basename(filepath)
                delete_enterprise_document(filename)
                push_sse_event(f"🔴 Document Deleted: {filename}")
                continue
                
            print(f"\n[Event Manager] Detected new file: {filepath}")
            folder = os.path.basename(os.path.dirname(filepath))
            
            mapping = {
                "emails": "outlook",
                "sharepoint": "sharepoint",
                "powerbi": "powerbi",
                "onedrive": "onedrive",
                "contracts": "contracts"
            }
            
            connector_name = mapping.get(folder)
            connector = get_connector(connector_name)
            
            if connector:
                print(f"[Event Manager] Routing to {connector_name} connector...")
                
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                item = {"filename": os.path.basename(filepath), "content": content}
                doc = connector.transform(item)
                
                index_enterprise_document(doc)
                
                push_sse_event(f"🟢 New {connector_name.title()} Document Indexed: {doc.title}")
            else:
                print(f"[Event Manager] No connector registered for folder: {folder}")
                push_sse_event(f"🟡 Ignored file in {folder}: {os.path.basename(filepath)}")
                
        except Exception as e:
            print(f"[Event Manager] Error processing {filepath}: {e}")
            push_sse_event(f"🔴 Error indexing {os.path.basename(filepath)}: {str(e)}")
        finally:
            task_queue.task_done()

def start_watching(base_dir="."):
    folders = ["emails", "sharepoint", "powerbi", "onedrive", "contracts"]
    
    thread = threading.Thread(target=worker_loop, daemon=True)
    thread.start()
    
    observer = Observer()
    handler = EnterpriseFileHandler()
    
    for folder in folders:
        path = os.path.join(base_dir, folder)
        if not os.path.exists(path):
            os.makedirs(path)
        observer.schedule(handler, path, recursive=False)
        print(f"[Event Manager] Watching {folder}/...")
        
    observer.start()
    return observer
