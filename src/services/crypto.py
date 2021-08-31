from bcrypt import gensalt, hashpw, checkpw


class Crypto:
    def __init__(self, is_testing, salt_rounds):
        self.is_testing = is_testing
        self.salt_rounds = salt_rounds

    def hash_password(self, password: bytes) -> bytes:
        if self.is_testing:
            return self._dev_hash(password)
        else:
            salt = gensalt(rounds=self.salt_rounds)
            return hashpw(password, salt)

    def check_password(self, password: bytes, hashed: bytes) -> bool:
        if self.is_testing:
            return self._dev_hash(password) == hashed
        else:
            return checkpw(password, hashed)

    @staticmethod
    def _dev_hash(password: bytes) -> bytes:
        if len(password) > 60:
            return password[:60]
        else:
            return password + b'0' * (60 - len(password))
