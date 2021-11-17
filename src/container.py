from typing import Optional, List

from dependency_injector import providers, containers

from src.services import DbEngine, DbSessionMaker, Crypto, Cached, LocalUploader, ImageProcessor, EmailSender, email_sender


def _choose_uploader(uploader_type: str, config: dict):
    if uploader_type.upper() == 'LOCAL':
        if 'base_path' not in config:
            raise KeyError('Uploader configuration does not contain "base_path"')

        return LocalUploader(config['base_path'])

    raise AttributeError(f'Unknown uploader type: {uploader_type}')


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

    uploader = providers.Singleton(
        _choose_uploader,
        uploader_type=config.uploader.type,
        config=config.uploader
    )

    image_processor = providers.Singleton(
        ImageProcessor,
        default_img_format=config.image_processor.def_img_format
    )

    email_sender = providers.Singleton(
        EmailSender,
        host=config.email.host, 
        port=config.email.port.as_int(), 
        username=config.email.username, 
        password=config.email.password, 
        from_addr=config.email.from_addr, 
        use_tls=config.email.use_tls.as_int(), 
        timeout=config.email.timeout.as_int()
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
