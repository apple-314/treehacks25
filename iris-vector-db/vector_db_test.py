from vector_db import VectorDatabase

db = VectorDatabase()
db.create_connection()

# name identifiers for schema
first_name = "James"
last_name = "Chen"

schema_name = f"{first_name}{last_name}"
table_name = "LinkedIn"

# Delete schema
db.delete_table(schema_name, table_name)

# Create schema and table
db.create_schema(schema_name)
db.create_table(schema_name, table_name)
db.create_table(schema_name, table_name)

# Insert data
data = {
    "type" : "Experience",
    "description" : "Engineer\nbuilt cool stuff",
}
db.write_data_dict(schema_name, table_name, data)

data = {
    "type" : "Bio",
    "description" : "love to build cool stuff",
}
db.write_data_dict(schema_name, table_name, data)

# Read data
results = db.read_data(schema_name, table_name)
for row in results:
    print(row)

# Close connection
db.close_connection()

