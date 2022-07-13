from contextlib import closing, contextmanager
import sqlite3

@contextmanager
def get_connection():
    with closing(sqlite3.connect("data/data.sqlite")) as connection:
        yield connection
        connection.commit()
