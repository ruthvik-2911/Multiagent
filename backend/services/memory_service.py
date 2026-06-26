conversation_memory = {}

def get_memory(session_id):
    return conversation_memory.get(session_id)

def set_memory(session_id, data):
    conversation_memory[session_id] = data

def clear_memory(session_id):
    if session_id in conversation_memory:
        del conversation_memory[session_id]
