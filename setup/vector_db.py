import os
import time
import re
import pandas as pd

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
            "Conversation" : "(text_id INT, index INT, time_stamp DATETIME, sentence VARCHAR(2000), sentence_vector VECTOR(DOUBLE, 384))",
            "ResearchPapers" : "(text_id INT, index INT, title VARCHAR(200), arxiv_id VARCHAR(200), sentence VARCHAR(2000), sentence_vector VECTOR(DOUBLE, 384))",
            "HealthArticles" : "(text_id INT, index INT, title VARCHAR(200), sentence VARCHAR(2000), sentence_vector VECTOR(DOUBLE, 384))",
            "Contacts" : "(fname VARCHAR(255), lname VARCHAR(255), id_name VARCHAR(255), phone VARCHAR(15), conv_summary VARCHAR(2000), most_recent_conv_summary VARCHAR(2000))"
        }

        self._table_entry_types = {
            "LinkedIn" : ["type", "description"],
            "Conversation" : ["text_id", "index", "time_stamp", "sentence", "sentence_vector"],
            "ResearchPapers" : ["text_id", "index", "title", "arxiv_id", "sentence", "sentence_vector"],
            "HealthArticles" : ["text_id", "index", "title", "sentence", "sentence_vector"],
            "Contacts" : ["fname", "lname", "id_name", "phone", "conv_summary", "most_recent_conv_summary"]
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
                self._cursor.execute(query, params)
            except:
                print(f"error in query {query} with params {params}")
    
    def _execute_many_query(self, query, params):
        # execute an SQL query safely
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
        
        query = f"""
            INSERT INTO {schema_name}.{table_name}
            ({columns})
            VALUES ({placeholders})
        """
        
        params_list = [data_dict[c] for c in self._table_entry_types[table_name]]
        params = [tuple(params_list)]

        self._execute_many_query(query, params)
    
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
        
        query = f"""
            INSERT INTO {schema_name}.{table_name}
            ({columns})
            VALUES ({placeholders})
        """
        
        data = []
        for index, row in df.iterrows():
            tmp = [row[x] for x in self._table_entry_types[table_name]]
            if vec:
                tmp[-1] = str(tmp[-1])
            data.append(tuple(tmp))
        
        self._execute_many_query(query, data)
    
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

    # get top k queries matching some search phrase
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
    
    # functions specific to tables storing text and vector embeddings
    def text_to_chunks(self, text, min_length):
        sentences = re.split(r'([.!?])', text)  # Keep punctuation with split
        chunks = []
        current_chunk = ""

        for i in range(0, len(sentences) - 1, 2):  # Process sentences in pairs (sentence + punctuation)
            sentence = sentences[i].strip() + sentences[i + 1]  # Reattach punctuation

            if len(current_chunk) + len(sentence) >= min_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())  # Store current chunk
                current_chunk = sentence  # Start new chunk
            else:
                current_chunk += " " + sentence  # Append sentence to current chunk

        if current_chunk:  # Add any remaining text as last chunk
            chunks.append(current_chunk.strip())

        return chunks
    
    def add_text_to_table(self, schema_name, table_name, text, min_length, def_params):
        self.create_schema(schema_name)
        self.create_table(schema_name, table_name)

        df = pd.DataFrame(columns=self._table_entry_types[table_name][:-1])
        chunks = self.text_to_chunks(text, min_length)
        
        query = f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
        self._execute_query(query)
        ret = self._cursor.fetchall()[0][0]

        text_id = 0
        if ret != 0:
            query = f"""
                SELECT TOP ? text_id
                FROM {schema_name}.{table_name}
                ORDER BY text_id DESC
            """
            self._execute_query(query, [1])
            text_id = self._cursor.fetchall()[0][0] + 1

        for chunk in chunks:
            tmp = []
            for x in self._table_entry_types[table_name][:-1]:
                if x == "text_id":
                    tmp.append(text_id)
                elif x == "index":
                    tmp.append(len(df))
                elif x == "sentence":
                    tmp.append(chunk)
                else:
                    tmp.append(def_params[x])

            df.loc[len(df)] = tmp
        
        embeddings = self._model.encode(df['sentence'].tolist(), normalize_embeddings=True)
        df['sentence_vector'] = embeddings.tolist()
        self.write_data_many_df(schema_name, table_name, df, True)
    
    # get entries in sorted order with indices in an interval
    def get_table_interval(self, schema_name, table_name, text_id, start_idx, end_idx):
        query = f"""
            SELECT *
            FROM {schema_name}.{table_name}
            WHERE index BETWEEN {start_idx} AND {end_idx}
                AND text_id = {text_id}
            ORDER BY index ASC;
        """
        self._execute_query(query)
        return self._cursor.fetchall()

    # extract column from table
    def get_column_from_table(self, schema_name, table_name, col_name):
        query = f"""
            SELECT {col_name}
            FROM {schema_name}.{table_name}
        """
        self._execute_query(query)
        return self._cursor.fetchall()

    # extract row from table
    def get_row_from_table(self, schema_name, table_name, col_name, value):
        query = f"""
            SELECT *
            FROM {schema_name}.{table_name}
            WHERE {col_name} = '{value}'
        """
        self._execute_query(query)
        return self._cursor.fetchall()
    
    # delete row from table
    def delete_row_from_table(self, schema_name, table_name, col_name, value):
        query = f"""
            DELETE FROM {schema_name}.{table_name}
            WHERE {col_name} = '{value}'
        """
        self._execute_query(query)
    
    # updated row in table
    def update_row_from_table(self, schema_name, table_name, col, value, new_col, new_value):
        query = f"""
            UPDATE {schema_name}.{table_name}
            SET {new_col} = {new_value}
            WHERE {col} = {value}
        """
        self._execute_query(query)