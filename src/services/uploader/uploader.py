from abc import ABC, abstractmethod

from src.classes import FileStream
from src.models import Upload


class Uploader(ABC):
    @abstractmethod
    def upload(self, fstream: FileStream, sub_group: str, name: str) -> Upload:
        pass

    @abstractmethod
    def delete(self, upload: Upload):
        pass
