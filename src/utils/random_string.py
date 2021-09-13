import string
import random


def random_string(size: int, chars=string.ascii_letters + string.digits) -> str:
    return ''.join(random.choice(chars) for _ in range(size))
