CONNECTORS = {}

def register(name, connector):
    CONNECTORS[name] = connector

def get(name):
    return CONNECTORS.get(name)
