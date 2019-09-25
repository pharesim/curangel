from . import db_util
from . import errors


BLOCKS_PER_HOUR = 1200
MANA_FULL_RECHARGE_HOURS = 36
MANA_PER_BLOCK = 1000000
TARGET_DAILY_VOTES = 12
TARGET_QUEUE_LENGTH = 20
PENALTY_SOFTNESS = 60

STAMINA_BURST_TARGET = 3
STAMINA_MANA_RATIO = 12
STAMINA_BACKOFF_FACTOR = .20

MANA_RECHARGE_BLOCKS = BLOCKS_PER_HOUR * MANA_FULL_RECHARGE_HOURS
MAX_MANA = MANA_PER_BLOCK * MANA_RECHARGE_BLOCKS
DAILY_MANA = MANA_PER_BLOCK * BLOCKS_PER_HOUR * 24

TARGET_MANA_COST = DAILY_MANA / TARGET_DAILY_VOTES


def calculate_penalty(queue_length):
    if queue_length < TARGET_QUEUE_LENGTH or True:
        return 1
    return ((queue_length - (TARGET_QUEUE_LENGTH - 1))
            **
            (queue_length / PENALTY_SOFTNESS))


class RateLimitError(errors.CurangelError):
    pass


class ManaError(RateLimitError):
    def __init__(self, had, needed):
        self.had = had
        self.needed = needed
        self._fmt = "{user} had {had} mana, but needed {needed}."


class StaminaError(RateLimitError):
    def __init__(self):
        self._fmt = "{user} has voted too much too recently."


class NoSuchCuratorError(RateLimitError):
    def __init__(self):
        self._fmt = "{user} does not exist or is not a curator."


class Stamina:
    def __init__(self, value=1, step=0):
        self.value = value
        self.step = step

    def burn(self, queue_length, strength=1):
        current_target = STAMINA_BURST_TARGET - self.step
        if current_target > 0:
            value_cost = strength / current_target
        else:
            value_cost = strength * abs(current_target - 2)

        value_cost *= calculate_penalty(queue_length)
        step_value = self.step

        max_vote_strength = 1 - (STAMINA_BACKOFF_FACTOR * step_value)
        vote_strength = min(strength, max_vote_strength)
        if vote_strength < 0:
            raise StaminaError()

        self.value -= value_cost
        if self.value < 0:
            self.value += (self.value // -1) + 1
            self.step += 1
        return vote_strength, self.step, self.value

    def add_blocks(self, blocks):
        self.value += STAMINA_MANA_RATIO * (MANA_PER_BLOCK / MAX_MANA) * blocks
        while self.value >= 1:
            if self.step > 0:
                self.step -= 1
                self.value -= 1
            else:
                self.value = 1
                break


class Mana:
    def __init__(self, value=MAX_MANA):
        self.value = value

    def copy(self):
        return Mana(self.value)

    def burn(self, queue_length, strength=1):
        penalty = calculate_penalty(queue_length)
        cost = TARGET_MANA_COST * penalty
        if self.value >= cost:
            self.value -= cost * strength
            return self.value
        else:
            raise ManaError(self.value, TARGET_MANA_COST)

    def add_blocks(self, blocks):
        self.value += MANA_PER_BLOCK * blocks
        self.value = min(self.value, MAX_MANA)


class Enforcer:
    def __init__(self, stamina, mana):
        self.stamina = stamina
        self.mana = mana

    @classmethod
    def from_database_user(cls, db_file, username, current_block):
        with db_util.ManaDBHelper(db_file) as db:
            try:
                result = db.query_manabar(username)
                block, sta_step, sta_mag, mana = result
                sta_obj = Stamina(sta_mag, sta_step)
                mana_obj = Mana(mana)
            except db_util.NoManabarError:
                block = current_block
                sta_obj = Stamina()
                mana_obj = Mana()
            except db_util.NoSuchCuratorError:
                raise NoSuchCuratorError()

            block_diff = current_block - block
            sta_obj.add_blocks(block_diff)
            mana_obj.add_blocks(block_diff)
            return cls(sta_obj, mana_obj)

    def write_to_database(self, db_file, username, current_block):
        with db_util.ManaDBHelper(db_file, read_only=False) as db:
            db.upsert_manabar(username,
                              current_block,
                              self.stamina.step,
                              self.stamina.value,
                              self.mana.value)

    def curate(self, queue_length, strength=1):
        strength, sta_step, sta_value = self.stamina.burn(queue_length,
                                                          strength)
        mana_value = self.mana.burn(queue_length, strength)
        return strength, sta_step, sta_value, mana_value
