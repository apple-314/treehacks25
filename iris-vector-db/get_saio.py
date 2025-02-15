from vector_db import VectorDatabase
import time

db = VectorDatabase()
db.create_connection()

start = time.time()
print(db.get_entries_w_col_match("SaiKonkimalla", "LinkedIn", "type", "bio")[0][1])
print(f"time: {time.time() - start}")