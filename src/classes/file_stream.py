from abc import ABC, abstractmethod
from io import BytesIO
from typing import Union

from werkzeug.datastructures import FileStorage


class FileStream(ABC):
    @abstractmethod
    def read(self, n: int = -1) -> Union[bytes, str]:
        pass

    @abstractmethod
    def write(self, buffer: Union[bytes, str]):
        pass


class FlaskFileStream(FileStream):
    def __init__(self, file: FileStorage):
        self.file_stream = file.stream

    def read(self, n: int = -1) -> bytes:
        return self.file_stream.read(n)

    def write(self, buffer: bytes):
        raise NotImplementedError


class MemoryFileStream(FileStream):
    def __init__(self, data: bytes = b''):
        self._stream = BytesIO(data)

    def read(self, n: int = -1) -> bytes:
        return self._stream.read(n)

    def write(self, buffer: bytes) -> int:
        return self._stream.write(buffer)
