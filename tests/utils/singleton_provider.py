from dependency_injector.providers import Singleton


def singleton_provider(obj):
    def clb():
        return obj

    return Singleton(clb)
