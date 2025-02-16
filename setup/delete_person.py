from vector_db import VectorDatabase

db = VectorDatabase()
db.create_connection()

def del_person(p):
    db.delete_schema(p)
    db.delete_row_from_table("General", "Contacts", "id_name", p)

person_to_delete = "AaravWattal"

del_person(person_to_delete)
