from backend.services.router_service import choose_agent

questions = [
    "Explain AI policy",
    "Show sales revenue",
    "Which documents are related?",
    "Tell me more"
]

for q in questions:
    print(q)
    print(choose_agent(q))
    print("-----------------")
