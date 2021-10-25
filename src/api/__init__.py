from src.api.admin_sistema_api import AdminSistemaApi
from src.api.auth_api import AuthApi
from src.api.buscar_estacio_api import BuscarEstacioApi
from src.api.estacionamento_crud_api import EstacionamentoCrudApi
from src.api.estacionamento_others_api import EstacionamentoOthersApi
from src.api.pedido_cadastro_api import PedidoCadastroApi
from src.api.pedido_cadastro_aprovacao_api import PedidoCadastroAprovacaoApi

APIS = (
    AdminSistemaApi,
    AuthApi,
    PedidoCadastroApi,
    PedidoCadastroAprovacaoApi,
    EstacionamentoCrudApi,
    EstacionamentoOthersApi,
    BuscarEstacioApi
)
