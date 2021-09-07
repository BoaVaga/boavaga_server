from uuid import uuid1

from dependency_injector.providers import Singleton

from src.services import Cached


class MockedCached(Cached):
    def __init__(self, container, prefix: str = None):
        self.prefix = prefix or (str(uuid1()) + ';')
        self._keys_created = set()

        cfg = container.config.get('memcached')
        super().__init__(cfg['host'], cfg['port'])

    def get(self, group: str, key: str):
        return super().get(self.prefix + group, key)

    def contains(self, group: str, key: str):
        return super().contains(self.prefix + group, key)

    def set(self, group: str, key: str, value):
        group = self.prefix + group

        super().set(group, key, value)
        self._keys_created.add(self._gen_key_name(group, key))

    def remove(self, group: str, key: str):
        group = self.prefix + group

        super().remove(group, key)
        self._keys_created.remove(self._gen_key_name(group, key))

    def clear_all(self):
        for k in self._keys_created:
            self.client.delete(k)
        self._keys_created.clear()


def make_mocked_cached_provider(container, prefix: str = None):
    def fac():
        return MockedCached(container, prefix)

    return Singleton(fac)
