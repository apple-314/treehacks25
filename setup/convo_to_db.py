from datetime import datetime

def init_conversations_contacts(db):
    f = open("phone_numbers.txt", "r")
    x = f.readlines()
    f.close()

    contacts = {
        0 : {"fname": "James", "lname": "Chen", "id_name": "JamesChen", "phone": x[0], "conv_summary": "likes to play chess", "most_recent_conv_summary": "likes to drink soda"},
        1 : {"fname": "Sai", "lname": "Konkimalla", "id_name": "SaiKonkimalla", "phone": x[1], "conv_summary": "likes ee stuff", "most_recent_conv_summary": "Aarav is over 6 feet tall"},
        2 : {"fname": "Kaival", "lname": "Shah", "id_name": "KaivalShah", "phone": x[2], "conv_summary": "is a freshman", "most_recent_conv_summary": "VR is cool"}
    }

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