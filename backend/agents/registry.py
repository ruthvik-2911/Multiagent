AGENTS = {}

def register(name, handler):
    AGENTS[name] = handler

def get_agent(name):
    return AGENTS.get(name)
