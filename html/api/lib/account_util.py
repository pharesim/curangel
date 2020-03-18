from .config import config
from .db_util import AccountDBHelper
from .errors import CurangelError
from .hive_util import Hive
from .rate_limit import Enforcer


class AccountError(CurangelError):
    pass


class BadPasswordError(AccountError):
    def __init__(self, username):
        self.username = username

    def _fmt(self):
        return "bad password for account '{username}'"


class RoleError(AccountError):
    def __init__(self, username, role):
        self.username = username
        self.role = role

    def _fmt(self):
        return "user '{username}' did not have required role '{role}'"


class Role:
    def __init__(self, name, user):
        self.name = name
        self.user = user
        self.granted = False

    def __bool__(self):
        return self.granted

    def __enter__(self):
        if not self.granted:
            raise RoleError(self.user, self.name)

    def __exit__(self, typ, val, tb):
        pass

    def grant(self):
        self.granted = True


class Account:
    def __init__(self, username):
        self.adbh = AccountDBHelper(config.db.file)
        with self.adbh:
            self.adbh.query_user_id(username)
        self.name = username
        self.admin = Role("admin", self.name)
        self.curator = Role("curator", self.name)
        self._last_block = -1

    def login(self, user_hash):
        with self.adbh:
            real_hash = self.adbh.query_hash(self.name)
            if real_hash.lower() != user_hash.lower():
                raise BadPasswordError(self.name)
            is_admin, is_curator = self.adbh.query_permissions(self.name)
            if is_admin:
                self.admin.grant()
            if is_curator:
                self.curator.grant()

    def _get_hive(self):
        try:
            return self.__hive
        except AttributeError:
            self.__hive = Hive()
            return self.__hive

    def _update_bars(self):
        head_block = self._get_hive().head_block_number
        if self._last_block < head_block:
            enforcer = Enforcer.from_database_user(config.db.file,
                                                   self.name,
                                                   head_block)
            self._stamina = enforcer.stamina
            self._mana = enforcer.mana
            self._last_block = head_block

    @property
    def mana(self):
        self._update_bars()
        return self._mana

    @property
    def stamina(self):
        self._update_bars()
        return self._stamina
