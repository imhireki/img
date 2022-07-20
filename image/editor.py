from abc import ABC, abstractmethod
from typing import Union, Generator
from dataclasses import dataclass
import tempfile

import PIL.Image, PIL.ImageSequence


def get_named_temporary_file() -> tempfile.NamedTemporaryFile:
    temporary_file = tempfile.NamedTemporaryFile(delete=False)
    temporary_file.close()
    return temporary_file


@dataclass
class EditorOptions:
    size: tuple[int, int]
    resample: int
    reducing_gap: int

    quality: int
    format: str

    @property
    def resize_options(self) -> dict[str, Union[tuple, int, int]]:
        return {
            "size": self.size,
            "resample": self.resample,
            "reducing_gap": self.reducing_gap
        }

    @property
    def save_options(self) -> dict[str, Union[int, str]]:
        return {
            "quality": self.quality,
            "format": self.format
        }


class IImageEditor(ABC):
    @property
    @abstractmethod
    def result(self) -> tempfile.NamedTemporaryFile: pass

    @abstractmethod
    def resize_image(self) -> None: pass

    @abstractmethod
    def save_resized_image(self) -> None: pass


class StaticImageEditor(IImageEditor):
    def __init__(self, image: PIL.Image.Image, editor_options: EditorOptions) -> None:
        self._image: PIL.Image.Image = image
        self._editor_options: EditorOptions = editor_options
        self._result: tempfile.NamedTemporaryFile = get_named_temporary_file()

    @property
    def result(self) -> tempfile.NamedTemporaryFile:
        return self._result

    def resize_image(self) -> None:
        self._image = self._image.resize(**self._editor_options.resize_options)

    def save_resized_image(self) -> None:
        with open(self._result.name, 'wb') as temporary_file:
            self._image.save(temporary_file, **self._editor_options.save_options)


class AnimatedImageEditor(IImageEditor):
    _frames: Generator[PIL.Image.Image, None, None]

    def __init__(self, image: PIL.Image.Image, editor_options: EditorOptions) -> None:
        self._image: PIL.Image.Image = image
        self._editor_options: EditorOptions = editor_options
        self._result: tempfile.NamedTemporaryFile = get_named_temporary_file()

    @property
    def result(self) -> tempfile.NamedTemporaryFile:
        return self._result

    def resize_image(self) -> None:
        self._frames = (frame.resize(**self._editor_options.resize_options)
                        for frame in PIL.ImageSequence.Iterator(self._image))
        self._image = next(self._frames)

    def save_resized_image(self) -> None:
        with open(self._result.name, 'wb') as temporary_file:
            self._image.save(
                temporary_file, **self._editor_options.save_options,
                loop=0, save_all=True, append_images=self._frames
            )


class BulkImageEditor(IImageEditor):
    _image_editor_generator: Generator[IImageEditor, None, None]
    _current_image_editor: IImageEditor

    def __init__(self, image_editor_generator: Generator[IImageEditor, None, None]) -> None:
        self._image_editor_generator = image_editor_generator

    def __next__(self) -> tempfile.NamedTemporaryFile:
        self._current_image_editor = next(self._image_editor_generator)
        self.resize_image()
        self.save_resized_image()
        return self.result

    @property
    def result(self) -> tempfile.NamedTemporaryFile:
        return self._current_image_editor.result

    def resize_image(self) -> None:
        self._current_image_editor.resize_image()

    def save_resized_image(self) -> None:
        self._current_image_editor.save_resized_image()
