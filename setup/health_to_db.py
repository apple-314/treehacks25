import os

def init_health(db):
    db.delete_schema("HealthcareAgent")
    
    # get list of all text articles with medical conditions
    dir = "health_articles/"
    fnames = [f for f in os.listdir(dir) if os.path.isfile(f"{dir}{f}")]

    for fname in fnames:
        f = open(f"{dir}{fname}", "r")
        s = "\n".join(f.readlines())
        f.close()

        d = {
            "title" : fname[:-4]
        }
        print(d)
        db.add_text_to_table("HealthcareAgent", "HealthArticles", s, 256, d)
