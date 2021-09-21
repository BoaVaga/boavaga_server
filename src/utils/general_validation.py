import re

_REGEX_VALIDATE_TEL = re.compile(r'^\+?[0-9]{1,19}$')


def validate_telefone(tel: str) -> bool:
    return _REGEX_VALIDATE_TEL.match(tel) is not None
