from typing import Dict, Callable


class BaseApi:
    def __init__(self, queries: Dict[str, Callable], mutations: Dict[str, Callable]):
        self.queries = queries
        self.mutations = mutations
