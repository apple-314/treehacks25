from fastapi import FastAPI
from linkedin import scrape, format_info

app = FastAPI()

@app.get("/get_context/")
async def get_context(first_name: str, last_name: str):
    img, link, about, experiences, education = scrape(first_name, last_name)
    about_s, experiences_s, educaiton_s = format_info(about, experiences, education)

    return {"about": about_s, "experiences": experiences_s, "education": educaiton_s}