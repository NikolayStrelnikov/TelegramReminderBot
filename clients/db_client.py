import sqlite3


class SQLiteClient:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.conn = None

    def create_conn(self):
        self.conn = sqlite3.connect(self.filepath, check_same_thread=False)

    def close_conn(self):
        self.conn.close()

    def execute_command(self, command: str, params: tuple):
        if self.conn is not None:
            self.conn.execute(command, params)
            self.conn.commit()
        else:
            raise ConnectionError("You need to create connection to DB!")

    def execute_select_command(self, command: str, params: tuple):
        if self.conn is not None:
            cur = self.conn.cursor()
            cur.execute(command, params)
            return cur.fetchall()
        else:
            raise ConnectionError("You need to create connection to DB!")
