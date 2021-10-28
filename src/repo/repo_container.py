from typing import Optional, List

from dependency_injector import containers, providers

from src.repo.buscar_estacio_repo import BuscarEstacioRepo
from src.repo.estacionamento_others_repo import EstacionamentoOthersRepo
from src.repo.estacionamento_crud_repo import EstacionamentoCrudRepo
from src.repo.pedido_cadastro_aprovacao_repo import PedidoCadastroAprovacaoRepo
from src.repo.pedido_cadastro_repo import PedidoCadastroCrudRepo
from src.repo.admin_sistema_repo import AdminSistemaRepo
from src.repo.auth_repo import AuthRepo


class RepoContainer(containers.DeclarativeContainer):
    config = providers.Configuration(strict=True)

    auth_repo = providers.Factory(AuthRepo)
    admin_sistema_repo = providers.Factory(AdminSistemaRepo)
    pedido_cadastro_crud_repo = providers.Factory(
        PedidoCadastroCrudRepo,
        width_foto=config.pedido_cadastro.width_foto.as_int(),
        height_foto=config.pedido_cadastro.height_foto.as_int(),
        limite_tentativas=config.pedido_cadastro.limite_tentativas.as_int()
    )
    pedido_cadastro_aprovacao_repo = providers.Factory(PedidoCadastroAprovacaoRepo)
    estacionamento_crud_repo = providers.Factory(EstacionamentoCrudRepo)
    estacionamento_others_repo = providers.Factory(EstacionamentoOthersRepo)
    buscar_estacio_repo = providers.Factory(
        BuscarEstacioRepo,
        distancia=config.busca_estacio.distancia.as_int()
    )


def create_repo_container(config_filepath: str, extra_modules: Optional[List] = None):
    from src import api

    container = RepoContainer()
    container.config.from_ini(config_filepath)

    modules = [api]
    if extra_modules is not None:
        modules.extend(extra_modules)

    container.wire(modules=modules)

    return container
