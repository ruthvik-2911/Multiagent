from backend.services.document_profile_service import load_profiles
from backend.services.graph_service import (
    create_document,
    create_keyword,
    create_relationship
)

profiles = load_profiles()

for profile in profiles:
    create_document(profile)

    for keyword in profile.get("keywords", []):
        create_keyword(keyword)
        create_relationship(
            profile["file_name"],
            keyword
        )

print("Graph Built Successfully!")
