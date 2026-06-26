from backend.services.keyword_generator import generate_keywords

text = """
Company AI Usage Policy

All employees must use AI responsibly.

Confidential company information must never be uploaded to public AI services.

Privacy and security standards must always be followed.
"""

keywords = generate_keywords(text)

print(keywords)
