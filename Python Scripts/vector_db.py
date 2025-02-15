import os
import time

import iris
from sentence_transformers import SentenceTransformer


"""
# gives datetime in the SQL DATETIME type format

from datetime import datetime

# Get the current time (including microseconds)
current_time = datetime.now()

# Truncate the microseconds by setting them to 0
current_time_truncated = current_time.replace(microsecond=0)

print(current_time_truncated)  # Example: 2025-02-15 14:35:45
"""

class VectorDatabase:
    def __init__(self, username='demo', password='demo', hostname=None, port=1972, namespace='USER'):
        # parameters to initialize server connection
        self._uname = username
        self._passwd = password
        self._hostname = hostname or os.getenv('IRIS_HOSTNAME', 'localhost')
        self._port = port
        self._namespace = namespace
        self._connection_string = f"{self._hostname}:{self._port}/{self._namespace}"

        # private variables to maintain server connection
        self._conn = None
        self._cursor = None

        # private variable for sentence transformer model (embeddings)
        self._model = SentenceTransformer('all-MiniLM-L6-v2')

        # private dictionary with SQL table format for different table types
        self._table_defs = {
            "LinkedIn" : "(type VARCHAR(255), description VARCHAR(2000))",
            "Conversation" : "(conv_id INT, index_in_conv INT, time_stamp DATETIME, sentence VARCHAR(2000), sentence_vector VECTOR(DOUBLE, 384))"
        }

        self._table_entry_types = {
            "LinkedIn" : ["type", "description"],
            "Conversation" : ["conv_id", "index_in_conv", "time_stamp", "sentence", "sentence_vector"]
        }

    def _execute_query(self, query, params=None):
        # execute an SQL query safely
        if params is None:
            # execute only query
            try:
                self._cursor.execute(query)
            except:
                print(f"error in query {query}")
        else:
            # execute query with parameters
            try:
                self._cursor.executemany(query, params)
            except:
                print(f"error in query {query} with params {params}")
       
    # create and remove schemas and tables
    def create_schema(self, schema_name):
        # create a schema if it doesn’t exist
        query = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"
        self._execute_query(query)
    
    def create_table(self, schema_name, table_name):
        # create a vector table if it doesn’t exist
        query = f"CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} {self._table_defs[table_name]}"
        self._execute_query(query)
    
    def delete_schema(self, schema_name):
        # delete schema if it exists
        query = f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"
        try:
            self._execute_query(query)
        except:
            pass

    def delete_table(self, schema_name, table_name):
        # delete schema if it exists
        query = f"DROP TABLE IF EXISTS {schema_name}.{table_name}"
        try:
            self._execute_query(query)
        except:
            pass

    # read and write operations to tables
    def write_data_dict(self, schema_name, table_name, data_dict):
        self.create_schema(schema_name)
        self.create_table(schema_name, table_name)

        # insert data into the vector database
        columns = ", ".join(self._table_entry_types[table_name])
        placeholders = ",".join(["?"] * len(self._table_entry_types[table_name]))
        
        query = f"Insert into {schema_name}.{table_name} ({columns}) values ({placeholders})"
        params_list = [data_dict[c] for c in self._table_entry_types[table_name]]
        params = [tuple(params_list)]

        self._execute_query(query, params)
    
    def write_data_many_df(self, schema_name, table_name, df, vec=False):
        self.create_schema(schema_name)
        self.create_table(schema_name, table_name)

        # insert data into the vector database
        columns = ", ".join(self._table_entry_types[table_name])
        placeholders = ""
        if vec:
            placeholders = ",".join(["?"] * (len(self._table_entry_types[table_name])-1)) + ",TO_VECTOR(?)"
        else:
            placeholders = ",".join(["?"] * (len(self._table_entry_types[table_name])))
        
        query = f"Insert into {schema_name}.{table_name} ({columns}) values ({placeholders})"
        
        data = []
        for index, row in df.iterrows():
            tmp = [row[x] for x in self._table_entry_types[table_name]]
            if vec:
                tmp[-1] = str(tmp[-1])
            data.append(tuple(tmp))
        
        self._execute_query(query, data)
    
    def read_data(self, schema_name, table_name, condition="TRUE"):
        # read data from the vector database based on a condition
        query = f"SELECT * FROM {schema_name}.{table_name}"
        self._execute_query(query)
        return self._cursor.fetchmany(1)
    
    # create and close connection to database
    def create_connection(self):
        # Establish the database connection
        self._conn = iris.connect(self._connection_string, self._uname, self._passwd)
        self._cursor = self._conn.cursor()
    
    def close_connection(self):
        # close the database connection
        self._cursor.close()
        self._conn.close()

    # get top k entries matching some search phrase
    def vector_search(self, schema_name, table_name, search_phrase, k):
        search_vec = self._model.encode(search_phrase, normalize_embeddings=True).tolist()
        query = f"""
            SELECT TOP ? *
            FROM {schema_name}.{table_name}
            ORDER BY VECTOR_DOT_PRODUCT(sentence_vector, TO_VECTOR(?)) DESC
        """

        self._cursor.execute(query, [k, str(search_vec)])
        return self._cursor.fetchall()
    
    # get entries which match a particular column
    def get_entries_w_col_match(self, schema_name, table_name, col_name, val):
        query = f"""
            SELECT * FROM {schema_name}.{table_name}
            WHERE {col_name} = '{val}'
        """
        self._cursor.execute(query)
        return self._cursor.fetchall()