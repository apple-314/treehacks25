from datetime import datetime
from vector_db import VectorDatabase

contacts = {
    0 : {"fname": "James", "lname": "Chen", "id_name": "JamesChen", "phone": "1234567890", "conv_summary": "likes to play chess"},
    1 : {"fname": "Aarav", "lname": "Wattal", "id_name": "AaravWattal", "phone": "0987654321", "conv_summary": "likes ee stuff"},
    2 : {"fname": "Kaival", "lname": "Shah", "id_name": "KaivalShah", "phone": "7125364908", "conv_summary": "is a freshman"}
}

db = VectorDatabase()
db.create_connection()

# adding text to conversation tables for each person schema
for i in contacts.keys():
    db.delete_table(contacts[i]["id_name"], "Conversation")

dir = "example_convos/"
for i in range(1, 11):
    f = open(f"{dir}convo{i}.txt", "r")
    l = f.readlines()
    s = "\n".join(l)
    f.close()

    data = {
        "time_stamp" : str(datetime.now().replace(microsecond=0))
    }

    db.add_text_to_table(contacts[i % 3]["id_name"], "Conversation", s, 256, data)

# adding people to contacts 
db.delete_schema("General")

for i in contacts.keys():
    db.write_data_dict("General", "Contacts", contacts[i])