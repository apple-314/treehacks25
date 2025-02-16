import json
from vector_db import VectorDatabase
import time

db = VectorDatabase()
db.create_connection()

start_time = time.time()

names = ["SaiKonkimalla", "JamesChen", "KaivalShah"]

data = {}

for name in names:
    # Format name with space between first and last name
    formatted_name = "".join([c if c.islower() else " " + c for c in name]).strip()

    # Fetch LinkedIn data
    bio_result = db.get_entries_w_col_match(name, "LinkedIn", "type", "bio")
    bio = bio_result[0][1] if bio_result else ""

    exp_results = db.get_entries_w_col_match(name, "LinkedIn", "type", "exp")
    experiences = [entry[1] for entry in exp_results] if exp_results else []

    edu_results = db.get_entries_w_col_match(name, "LinkedIn", "type", "edu")
    education = [entry[1] for entry in edu_results] if edu_results else []

    # get image from "pfp" type under LinkedIn
    img_results = db.get_row_from_table(name, "LinkedIn", "type", "pfp")
    image = img_results[0][1] if img_results else ""

    # get interests from "interests" type under LinkedIn
    interests_results = db.get_row_from_table(name, "LinkedIn", "type", "interests")
    interests = interests_results[0][1] if interests_results else ""

    convos = []
    

    # Structure data
    data[formatted_name] = {
        "LinkedIn": {
            "bio": bio,
            "experiences": experiences,
            "education": education
        },
        "convos": [],
        "interests": interests,
        "img": image
    }

# Convert to JSON
json_output = json.dumps(data, indent=4)

# Save to a file
with open("people_data.json", "w") as f:
    f.write(json_output)

# Print result
print(json_output)

print(time.time() - start_time)

# get_profiles