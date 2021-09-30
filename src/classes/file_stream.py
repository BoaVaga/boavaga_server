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

    @abstractmethod
    def seek(self, offset, whence=0):
        pass

    @abstractmethod
    def tell(self) -> int:
        pass


class FlaskFileStream(FileStream):
    def __init__(self, file: FileStorage):
        self.file_stream = file.stream

    def read(self, n: int = -1) -> bytes:
        return self.file_stream.read(n)

    def write(self, buffer: bytes):
        raise NotImplementedError

    def seek(self, offset, whence=0):
        self.file_stream.seek(offset, whence)

    def tell(self) -> int:
        return self.file_stream.tell()


class MemoryFileStream(FileStream):
    def __init__(self, data: bytes = b''):
        self._stream = BytesIO(data)

    def read(self, n: int = -1) -> bytes:
        return self._stream.read(n)

    def write(self, buffer: bytes) -> int:
        return self._stream.write(buffer)

    def seek(self, offset, whence=0):
        self._stream.seek(offset, whence)

    def tell(self) -> int:
        return self._stream.tell()
