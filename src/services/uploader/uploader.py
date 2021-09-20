from abc import ABC, abstractmethod
from typing import Tuple, Union

from src.classes import FileStream
from src.models import Upload


class Uploader(ABC):
    @abstractmethod
    def upload(self, fstream: FileStream, sub_group: str, name: str) -> Tuple[bool, Union[str, Upload]]:
        pass
