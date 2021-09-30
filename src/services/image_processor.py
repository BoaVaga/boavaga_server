from typing import Optional
from PIL import Image

from src.classes import FileStream
from src.classes.file_stream import MemoryFileStream


class ImageProcessor:
    def __init__(self, default_img_format: str):
        self.default_img_format = default_img_format

    def compress(self, file_stream: FileStream, width: int, height: int, img_format: Optional[str] = None) \
            -> FileStream:
        img_format = img_format or self.default_img_format

        image = Image.open(file_stream)
        resized = image.resize((width, height))

        out_stream = MemoryFileStream()
        resized.save(out_stream, format=img_format)

        out_stream.seek(0)
        return out_stream
