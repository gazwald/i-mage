from __future__ import annotations

from pathlib import Path
from pprint import pprint
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from typing import Callable

    from PIL.Image import Image as ImageType


class ImageDetails:
    path: Path
    image: ImageType
    difference: float
    size: int
    resolution: tuple[int, int]

    def __hash__(self) -> int:
        return self.path.__hash__()


def is_image(path: Path) -> bool:
    if not path.exists():
        return False
    if not path.is_file():
        return False

    return path.suffix in {".png", ".jpg", ".jpeg", ".gif"}


def open_image(path: Path) -> ImageType:
    return Image.open(path)


def load(path: Path) -> dict[Path, ImageType]:
    return {
        image_path: open_image(image_path) for image_path in path.glob("*") if is_image(image_path)
    }


def image_cache(
    func: Callable[[Path, ImageType], ImageType],
) -> Callable[[Path, ImageType], ImageType]:
    images: dict[Path, ImageType] = {}

    def wrapper(path: Path, image: ImageType) -> ImageType:
        if path not in images:
            images[path] = func(path, image)

        return images[path]

    return wrapper


@image_cache
def resize(
    path: Path,
    image: ImageType,
) -> ImageType:
    """
    PIL Images aren't hashable so we're using the Path in the cache
    """
    return image.resize((512, 512))


def comparable_geometry(left: ImageType, right: ImageType) -> bool:
    return len(set([left.width, right.width, left.height, right.height])) == 2


def difference(left: ImageType, right: ImageType) -> float:
    left_data: set[tuple[int, ...]] = set(left.getdata())  # type:ignore
    right_data: set[tuple[int, ...]] = set(right.getdata())  # type:ignore
    difference: int = len(left_data ^ right_data)
    return (difference / len(left_data) + difference / len(right_data)) / 2


def same(
    left: ImageType,
    right: ImageType,
    threshhold: float = 0.02,
) -> bool:
    if left == right:
        return True

    return difference(left, right) <= threshhold


def compare() -> dict[Path, set[Path]]:
    images = load(Path("./images"))
    comparison: dict[Path, set[Path]] = {}
    for left_path, left_image in images.items():
        comparison[left_path] = set()
        for right_path, right_image in images.items():
            if left_path == right_path:
                continue

            if right_path in comparison.keys():
                continue

            if comparable_geometry(left_image, right_image):
                left = left_image
                right = right_image
            else:
                left = resize(left_path, left_image)
                right = resize(right_path, right_image)

            if same(left, right):
                comparison[left_path].add(right_path)

    pprint(comparison)
    return comparison
