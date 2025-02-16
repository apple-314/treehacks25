from datetime import datetime
from vector_db import VectorDatabase

ppl = ["JamesChen", "AaravWattal", "KaivalShah"]

db = VectorDatabase()
db.create_connection()

for p in ppl:
    db.delete_schema(p)

dir = "example_convos/"
for i in range(1, 11):
    f = open(f"{dir}convo{i}.txt", "r")
    l = f.readlines()
    s = "\n".join(l)
    f.close()

    data = {
        "time_stamp" : str(datetime.now().replace(microsecond=0))
    }

    db.add_text_to_table(ppl[i % 3], "Conversation", s, 256, data)