from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from typing import Callable, Generator

    from PIL.Image import Image as PIL_Image


@dataclass
class ImageDetails:
    path: Path
    image: PIL_Image
    similar: set[ImageDetails] = field(default_factory=set)
    difference: float = 0.0
    duplicate: bool = False

    def __hash__(self) -> int:
        return self.path.__hash__()

    def __eq__(self, value: object, /) -> bool:
        if isinstance(value, ImageDetails):
            return self.difference == value.difference

        return False

    def __lt__(self, value: object) -> bool:
        if isinstance(value, ImageDetails):
            return self.difference < value.difference

        return False

    def __gt__(self, value: object) -> bool:
        if isinstance(value, ImageDetails):
            return self.difference > value.difference

        return False

    @property
    def size(self) -> int:
        return self.path.stat().st_size // 1024

    @property
    def resolution(self) -> str:
        return f"{self.image.size[0]} x {self.image.size[0]}"

    def contains(self, other: ImageDetails) -> bool:
        for image in self.similar:
            if image.path == other.path:
                return True

        return False


def is_image(path: Path) -> bool:
    if not path.exists():
        return False
    if not path.is_file():
        return False

    return path.suffix in {".png", ".jpg", ".jpeg", ".gif"}


def image_paths(path: Path) -> Generator[Path, None, None]:
    for image_path in path.glob("*"):
        if not is_image(image_path):
            continue

        yield image_path


@cache
def open_image(path: Path) -> ImageDetails:
    return ImageDetails(path=path, image=Image.open(path))


def loader(path: Path, batch_size: int = 4) -> set[ImageDetails]:
    with ThreadPoolExecutor() as executor:
        return set(
            image
            for image in executor.map(
                open_image,
                image_paths(path),
                buffersize=batch_size,
            )
        )


def image_cache(
    func: Callable[[ImageDetails], PIL_Image],
) -> Callable[[ImageDetails], PIL_Image]:
    images: dict[Path, PIL_Image] = {}

    def wrapper(details: ImageDetails) -> PIL_Image:
        if details.path not in images:
            images[details.path] = func(details)

        return images[details.path]

    return wrapper


@image_cache
def resize(details: ImageDetails) -> PIL_Image:
    return details.image.resize((512, 512))


def comparable_geometry(left: PIL_Image, right: PIL_Image) -> bool:
    return len(set([left.width, right.width, left.height, right.height])) == 2


def difference(left: PIL_Image, right: PIL_Image) -> float:
    left_data: set[tuple[int, ...]] = set(left.getdata())  # type:ignore
    right_data: set[tuple[int, ...]] = set(right.getdata())  # type:ignore
    difference: int = len(left_data ^ right_data)
    return (difference / len(left_data) + difference / len(right_data)) / 2


def same(left: PIL_Image, right: PIL_Image) -> float:
    if left == right:
        return 0.0

    return difference(left, right)


def compare(threshhold: float = 0.02) -> Generator[ImageDetails, None, None]:
    images: set[ImageDetails] = loader(Path("./images"))
    done = set()
    for left in images:
        for right in images:
            if left.path == right.path:
                continue

            if right.path in done:
                continue

            if comparable_geometry(left.image, right.image):
                diff = same(left.image, right.image)
            else:
                diff = same(resize(left), resize(right))

            if diff <= threshhold:
                left.similar.add(
                    ImageDetails(
                        path=right.path,
                        image=right.image,
                        difference=diff,
                    )
                )

        if left.similar:
            yield left
        done.add(left.path)
    Path("./duplicates").mkdir(exist_ok=True)
