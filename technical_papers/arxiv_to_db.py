import json
from vector_db import VectorDatabase

def main():
    db = VectorDatabase()
    db.create_connection()

    db.delete_schema("TechnicalAgent")
    
    # get json of all arxiv papers already parsed
    with open("arxiv_metadata.json", "r", encoding="utf-8") as f:
        arxiv_metadata = json.load(f)
    
    id_title = {}
    for x in arxiv_metadata:
        id_title[x["arxiv_id"]] = x["title"]
    
    for x in id_title:
        print(f"{x}: {id_title[x]}")

    for id in id_title:
        f = open(f"arxiv_tex_text/{id}.txt", "r", encoding="utf-8")
        l = f.readlines()
        s = "\n".join(l)
        f.close()

        d = {"title": id_title[id], "arxiv_id": id}
        print(d)

        db.add_text_to_table("TechnicalAgent", "Documents", s, 512, d)
    
main()