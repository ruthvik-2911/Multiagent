from backend.connectors.connector_manager import get

# Import to register the connector
import backend.connectors.outlook_connector

outlook = get("outlook")
if outlook:
    outlook.authenticate()
    emails = outlook.fetch()
    for email in emails:
        doc = outlook.transform(email)
        outlook.index(doc)
else:
    print("Outlook connector not found in registry.")
