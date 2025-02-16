from convo_to_db import init_conversations_contacts
from arxiv_to_db import init_tech
from health_to_db import init_health
from vector_db import VectorDatabase

db = VectorDatabase()
db.create_connection()

init_conversations_contacts(db)
init_tech(db)
init_health(db)