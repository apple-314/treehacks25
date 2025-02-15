import iris
import time
import os

username = 'demo'
password = 'demo'
hostname = os.getenv('IRIS_HOSTNAME', 'localhost')
port = '1972' 
namespace = 'USER'
CONNECTION_STRING = f"{hostname}:{port}/{namespace}"
print(CONNECTION_STRING)

# Note: Ideally conn and cursor should be used with context manager or with try-execpt-finally 
conn = iris.connect(CONNECTION_STRING, username, password)
cursor = conn.cursor()

tableName = "SchemaName.TableName"
tableDefinition = "(name VARCHAR(255), category VARCHAR(255),review_point INT, price DOUBLE, description VARCHAR(2000))"

try:
    cursor.execute(f"DROP TABLE {tableName}")  
except:
    pass
cursor.execute(f"CREATE TABLE {tableName} {tableDefinition}")

## batch update
sql = f"Insert into {tableName} (name, category, review_point, price, description) values (?,?,?,?,?)"
params = [("FAKE BRAND","NOT A SCOTCH", "100", "100.00", "FAKE BRAND INSERTED TO TEST BATCH UPDATE"), ("FAKE BRAND 2","NOT A SCOTCH", "100", "100.00", "SECOND FAKE BRAND INSERTED TO TEST BATCH UPDATE"), ("FAKE BRAND 3","NOT A SCOTCH", "100", "100.00", "THIRD FAKE BRAND INSERTED TO TEST BATCH UPDATE")]
cursor.executemany(sql, params)

## Read only select columns
cursor.execute(f"select name, category, price from {tableName}")
fetched_data = cursor.fetchmany(3)
for row in fetched_data:
    print(row)


##fetching all columns from database
cursor.execute(f"select * from {tableName}")
fetched_data = cursor.fetchmany(1)
for row in fetched_data:
    print(row)