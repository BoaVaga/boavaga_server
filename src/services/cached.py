from pymemcache import serde, PooledClient


class Cached:
    def __init__(self, host: str, port: int):
        self.client = PooledClient((host, port), serde=serde.pickle_serde)

    def get(self, group: str, key: str):
        return self.client.get(self._gen_key_name(group, key))

    def contains(self, group: str, key: str):
        return self.client.get(self._gen_key_name(group, key)) is not None

    def set(self, group: str, key: str, value):
        self.client.set(self._gen_key_name(group, key), value)

    def remove(self, group: str, key: str):
        self.client.delete(self._gen_key_name(group, key))

    @staticmethod
    def _gen_key_name(group: str, key: str) -> str:
        return group + ':' + key

    def close(self):
        self.client.close()
