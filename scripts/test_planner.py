from backend.services.planner_service import create_plan

question = "Compare sales report with AI policy"
print("Question:", question)
print("Plan:", create_plan(question))
