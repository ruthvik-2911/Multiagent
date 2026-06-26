from backend.services.metadata_generator import generate_summary

text = """
Company AI Usage Policy

All employees must use AI responsibly.

Confidential company information should never be uploaded to public AI services.

AI must comply with company privacy standards.

"""

summary = generate_summary(text)

print(summary)
