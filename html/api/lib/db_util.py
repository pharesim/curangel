import sqlite3
import os


class DBError(RuntimeError):
    pass


class NoSuchCuratorError(DBError):
    def __init__(self, curator):
        self.curator = curator

    def __str__(self):
        return "No such curator: '{}'".format(self.curator)


class NoManabarError(DBError):
    def __init__(self, curator):
        self.curator = curator

    def __str__(self):
        return "No manabar data for curator: '{}'".format(self.curator)


class ManaDBHelper:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        with self:
            self.cine_mana_table()

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        return self

    def __exit__(self, *args):
        self.conn.commit()
        self.conn.close()
        self.conn = None

    def _load(self, query_name):
        dirname, file = os.path.split(__file__)
        query_path = os.path.join(dirname, "sql", query_name)
        with open(query_path, "r") as f:
            return f.read()

    def query_user_id(self, curator):
        cursor = self.conn.cursor()
        query = self._load("query_user_id")
        row = cursor.execute(query, [curator]).fetchone()
        if row is None:
            raise NoSuchCuratorError(curator)
        else:
            return row["id"]

    def cine_mana_table(self):
        cursor = self.conn.cursor()
        query = self._load("cine_mana_table")
        cursor.execute(query)

    def query_manabar(self, curator):
        cursor = self.conn.cursor()
        query = self._load("query_manabar")
        curator_id = self.query_user_id(curator)
        cursor.execute(query, [curator_id])
        result = cursor.fetchone()
        if result is not None:
            block = int(result["last_curation_block"])
            sta_step = int(result["last_stamina_step"])
            sta_mag = float(result["last_stamina_magnitude"])
            mana = int(result["last_mana_magnitude"])
            return block, sta_step, sta_mag, mana
        else:
            raise NoManabarError(curator)

    def upsert_manabar(self, curator, block, sta_step, sta_mag, mana):
        cursor = self.conn.cursor()
        curator_id = self.query_user_id(curator)
        update = self._load("update_manabar")
        common_args = [block, sta_step, sta_mag, str(int(mana))]
        update_args = common_args + [curator_id]
        cursor.execute(update, update_args)
        if cursor.rowcount < 1:
            insert = self._load("insert_manabar")
            insert_args = [curator_id] + common_args
            cursor.execute(insert, insert_args)
