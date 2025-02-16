from vector_db import VectorDatabase
import time

db = VectorDatabase()
db.create_connection()

start = time.time()
results = db.vector_search("JamesChen", "Conversation", "chatbot", 1)
print(f"time: {time.time() - start}")

for row in results:
    print(row[0])
    print(row[1])
    print(row[2])
    print(row[3])
    print()