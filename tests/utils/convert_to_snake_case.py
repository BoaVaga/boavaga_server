import re

pattern = re.compile(r'(?<!^)(?=[A-Z])')


def convert_to_snake_case(s):
    return pattern.sub('_', s).lower()
