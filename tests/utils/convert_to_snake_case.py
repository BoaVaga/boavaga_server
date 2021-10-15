import re

pattern = re.compile(r'(?<!^)(?=[A-Z])')


def convert_to_snake_case(s):
    return pattern.sub('_', s).lower()


def convert_dct_snake_case(d):
    return {convert_to_snake_case(k): v for k, v in d.items()}
