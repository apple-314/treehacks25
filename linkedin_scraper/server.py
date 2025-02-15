from fastapi import FastAPI
from linkedin import scrape, format_info

from vector_db import VectorDatabase

db = VectorDatabase()
db.create_connection()

app = FastAPI()

@app.get("/get_context/")
async def get_context(first_name: str, last_name: str):
    db.delete_table(f"{first_name}{last_name}", "LinkedIn")

    img, link, about, experiences, education = scrape(first_name, last_name)
    about_s, experiences_s, educaiton_s = format_info(about, experiences, education)

    for item in about:
        data_dict = {"type": "bio", "description": "\n".join(item)}
        db.write_data_dict(f"{first_name}{last_name}", "LinkedIn", data_dict)

    for item in experiences:
        data_dict = {"type": "exp", "description": "\n".join(item)}
        db.write_data_dict(f"{first_name}{last_name}", "LinkedIn", data_dict)

    for item in education:
        data_dict = {"type": "edu", "description": "\n".join(item)}
        db.write_data_dict(f"{first_name}{last_name}", "LinkedIn", data_dict)

    return {"about": about_s, "experiences": experiences_s, "education": educaiton_s}