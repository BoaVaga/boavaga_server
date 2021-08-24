from dependency_injector import providers, containers

from src.services import DbEngine, DbSessionMaker


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    db_engine = providers.Singleton(
        DbEngine,
        conn_string=config.db.conn_string
    )

    db_session_maker = providers.Singleton(
        DbSessionMaker,
        engine=db_engine
    )


def create_container(config_filepath: str):
    from src import resources, services

    container = Container()
    container.config.from_ini(config_filepath)

    container.wire(modules=[resources, services])

    return container
