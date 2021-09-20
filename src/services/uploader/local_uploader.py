from pathlib import Path
from typing import Tuple, Union

from src.classes import FileStream
from src.enums import UploadStatus
from src.services.uploader.uploader import Uploader


class LocalUploader(Uploader):
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def upload(self, fstream: FileStream, sub_group: str, name: str) -> Tuple[bool, Union[str, UploadStatus]]:
        if fstream is None:
            raise AttributeError('fstream can not be None')
        if not sub_group:
            raise AttributeError('sub_group can not be an empty string or None')
        if not name:
            raise AttributeError('name can not be an empty string or None')

        try:
            final_path = self.base_path / sub_group / name

            with open(final_path, mode='wb') as f:
                f.write(fstream.read())

            return True, UploadStatus.CONCLUIDO
        except IOError:
            return False, 'write_file_error'
