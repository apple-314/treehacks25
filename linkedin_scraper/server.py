from fastapi import FastAPI
from linkedin import scrape, format_info

app = FastAPI()

@app.get("/get_context/")
async def get_context(first_name: str, last_name: str):
    img, link, about, experiences, education = scrape("Kaival", "Shah")
    context = format_info(about, experiences, education)

    return {"context": context}