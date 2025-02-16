from vector_db import VectorDatabase
from datetime import datetime
from jarvis import get_summary, update_summary

db = VectorDatabase()
db.create_connection()

fn =  "James"
ln =  "Chen"
id_name = fn+ln

transcript = "summary update!! add the word 'Hi!' to the end"

ts = {
    "time_stamp" : str(datetime.now().replace(microsecond=0))
}

cur_contact = db.get_entries_w_col_match("General", "Contacts", "id_name", id_name)
cur_summary = cur_contact[0][4]

print(cur_contact)

summary = get_summary(transcript)

if cur_summary:
    db.update_row_from_table("General", "Contacts", "id_name", id_name, "conv_summary", summary)
    db.update_row_from_table("General", "Contacts", "id_name", id_name, "most_recent_conv_summary", summary)
else:
    db.update_row_from_table("General", "Contacts", "id_name", id_name, "conv_summary", update_summary(cur_summary, transcript))
    db.update_row_from_table("General", "Contacts", "id_name", id_name, "most_recent_conv_summary", summary)

db.add_text_to_table(id_name, "Conversation", transcript, 256, ts)

# if (): # no current summaries
#     db.update_row_from_table(self, schema_name, table_name, col, value, new_col, new_value)
# else:
#     None # update current and replace latest

# db.add_text_to_table(id_name, "Conversation", transcript, 256, ts)

