from typing import Optional, List

from dependency_injector import providers, containers

from src.services import DbEngine, DbSessionMaker, Crypto, Cached


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(strict=True)

    db_engine = providers.Singleton(
        DbEngine,
        conn_string=config.db.conn_string
    )

    db_session_maker = providers.Singleton(
        DbSessionMaker,
        engine=db_engine
    )

    crypto = providers.Factory(
        Crypto,
        is_testing=config.crypto.is_testing.as_int(),
        salt_rounds=config.crypto.salt_rounds.as_int()
    )

    cached = providers.Singleton(
        Cached,
        host=config.memcached.host,
        port=config.memcached.port.as_int()
    )


def create_container(config_filepath: str, extra_modules: Optional[List] = None):
    from src import services, api, repo

    container = Container()
    container.config.from_ini(config_filepath)

    modules = [services, api, repo]
    if extra_modules is not None:
        modules.extend(extra_modules)

    container.wire(modules=modules)

    return container