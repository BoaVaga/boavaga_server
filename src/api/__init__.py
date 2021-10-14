from src.api.admin_sistema_api import AdminSistemaApi
from src.api.auth_api import AuthApi
from src.api.pedido_cadastro_api import PedidoCadastroApi
from src.api.pedido_cadastro_aprovacao_api import PedidoCadastroAprovacaoApi

APIS = (
    AdminSistemaApi,
    AuthApi,
    PedidoCadastroApi,
    PedidoCadastroAprovacaoApi
)
