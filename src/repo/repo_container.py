from typing import Optional, List

from dependency_injector import containers, providers

from src.repo.admin_sistema_repo import AdminSistemaRepo
from src.repo.auth_repo import AuthRepo


class RepoContainer(containers.DeclarativeContainer):
    config = providers.Configuration(strict=True)

    auth_repo = providers.Factory(AuthRepo)
    admin_sistema_repo = providers.Factory(AdminSistemaRepo)


def create_repo_container(config_filepath: str, extra_modules: Optional[List] = None):
    from src import api

    container = RepoContainer()
    container.config.from_ini(config_filepath)

    modules = [api]
    if extra_modules is not None:
        modules.extend(extra_modules)

    container.wire(modules=modules)

    return container