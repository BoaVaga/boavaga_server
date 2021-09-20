from abc import ABC, abstractmethod

from werkzeug.datastructures import FileStorage


class FileStream(ABC):
    @abstractmethod
    def read(self, n: int = -1):
        pass


class FlaskFileStream(FileStream):
    def __init__(self, file: FileStorage):
        self.file_stream = file.stream

    def read(self, n: int = -1):
        return self.file_stream.read(n)


class MemoryFileStream(FileStream):
    def __init__(self, data: bytes):
        self.data = data

        self._pointer = 0

    def read(self, n: int = -1):
        if self._pointer == len(self.data):
            raise EOFError

        base = self._pointer
        if n >= 0:
            self._pointer += n
            return self.data[base:self._pointer+1]
        else:
            self._pointer = len(self.data)
            return self.data[self._pointer:]
