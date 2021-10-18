class ValidationError(Exception):
    def __init__(self, attr, desc, code=None):
        self.attr = attr
        self.code = code
        self.desc = desc

        code_str = f' ({code})' if code else ''
        super().__init__(f'Validation error on {attr}{code_str}: {desc}')
