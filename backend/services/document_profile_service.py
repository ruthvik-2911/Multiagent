import json
import os

PROFILE_FILE = "backend/storage/document_profiles.json"


def load_profiles():

    if not os.path.exists(PROFILE_FILE):
        return []

    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profiles(profiles):

    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            profiles,
            f,
            indent=4
        )

def add_profile(profile):

    profiles = load_profiles()

    profiles = [
        p
        for p in profiles
        if p["file_name"] != profile["file_name"]
    ]

    profiles.append(profile)

    save_profiles(profiles)

def get_profile(file_name):
    profiles = load_profiles()
    for profile in profiles:
        if profile["file_name"] == file_name:
            return profile
    return None
