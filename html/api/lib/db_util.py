import sqlite3
import os

from . import errors


class DBError(errors.CurangelError):
    pass


class NoSuchCuratorError(DBError):
    def __init__(self, curator):
        self.curator = curator

    def _fmt(self):
        return "no such curator: '{curator}'"


class NoManabarError(DBError):
    def __init__(self, curator):
        self.curator = curator

    def _fmt(self):
        return "no manabar data for curator: '{curator}'"


class NoVoteStrengthError(DBError):
    def __init__(self, vote_id):
        self.vote_id = vote_id

    def _fmt(self):
        return "no strength was specified for vote '{vote_id}'"


class DBHelper:
    def __init__(self, db_filepath, *, read_only=True):
        mode_qs = "?mode=ro" if read_only else ""
        self.uri = "file:{db_filepath}{mode_qs}".format(**locals())
        self.conn = None
        with self:
            self._setup()

    def __enter__(self):
        self.conn = sqlite3.connect(self.uri, uri=True)
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


class ManaDBHelper(DBHelper):
    def _setup(self):
        self.cine_mana_table()

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


class QueueDBHelper(DBHelper):
    def _setup(self):
        self.cine_upvote_strength()

    def cine_upvote_strength(self):
        cursor = self.conn.cursor()
        query = self._load("cine_upvote_strength")
        cursor.execute(query)

    def query_upvote_strength(self, upvote_id):
        cursor = self.conn.cursor()
        query = self._load("query_upvote_strength")
        cursor.execute(query, [upvote_id])
        row = cursor.fetchone()
        if row is None:
            raise NoVoteStrengthError(upvote_id)
        else:
            return float(row["strength"])

    def upsert_upvote_strength(self, upvote_id, strength):
        cursor = self.conn.cursor()
        update = self._load("update_upvote_strength")
        insert = self._load("insert_upvote_strength")
        cursor.execute(update, [strength, upvote_id])
        if cursor.rowcount < 1:
            cursor.execute(insert, [upvote_id, strength])

    def query_queue_length(self):
        cursor = self.conn.cursor()
        query = self._load("query_queue_length")
        cursor.execute(query)
        row = cursor.fetchone()
        return row[0]


class AccountDBHelper(DBHelper):
    def _setup(self):
        pass

    def query_permissions(self, username):
        user_id = self.query_user_id(username)
        cursor = self.conn.cursor()
        query = self._load("query_permissions")
        cursor.execute(query, [user_id])
        row = cursor.fetchone()
        if row is not None:
            return row["admin"], row["curator"]

    def query_hash(self, username):
        user_id = self.query_user_id(username)
        cursor = self.conn.cursor()
        query = self._load("query_hash")
        cursor.execute(query, [user_id])
        row = cursor.fetchone()
        if row is not None:
            return row["hash"]
