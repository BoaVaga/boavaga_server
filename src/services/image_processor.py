from typing import Optional

from src.classes import FileStream


class ImageProcessor:
    def __init__(self, default_img_format: str):
        self.default_img_format = default_img_format

    def compress(self, file_stream: FileStream, img_format: Optional[str] = None) -> FileStream:
        pass
