import os
from backend.connectors.base_connector import BaseConnector
from backend.models.document import EnterpriseDocument
from backend.connectors.connector_manager import register
from backend.services.indexer import index_enterprise_document

class OutlookConnector(BaseConnector):
    def __init__(self, folder_path="emails"):
        self.folder_path = folder_path

    def authenticate(self):
        print("[OutlookConnector] Mock Authentication successful.")

    def fetch(self):
        print(f"[OutlookConnector] Fetching mock emails from {self.folder_path}...")
        emails = []
        if not os.path.exists(self.folder_path):
            return emails
            
        for filename in os.listdir(self.folder_path):
            if filename.endswith(".txt") or filename.endswith(".eml"):
                filepath = os.path.join(self.folder_path, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                emails.append({"filename": filename, "content": content})
        return emails

    def transform(self, item):
        filename = item["filename"]
        content = item["content"]
        title = filename.replace(".txt", "").replace(".eml", "").replace("_", " ").title()
        
        return EnterpriseDocument(
            source="outlook",
            title=title,
            content=content,
            metadata={"file_name": filename, "folder": "Inbox", "file_type": "eml"}
        )

    def index(self, doc: EnterpriseDocument):
        print(f"[OutlookConnector] Indexing {doc.title}...")
        index_enterprise_document(doc)

register("outlook", OutlookConnector())
