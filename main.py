from __future__ import annotations

from pathlib import Path
from pprint import pprint
from typing import TYPE_CHECKING

from nicegui import run, ui
from PIL import Image, ImageOps

if TYPE_CHECKING:
    from typing import Callable

    from PIL.Image import Image as ImageType


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


async def modify_image(func, image, ui_image):
    result = await run.cpu_bound(func, image)
    ui_image.set_source(result)


def frontend_image(path: Path, primary: bool = False):
    pil_image = open_image(path)
    classes = "bg-blue-500" if primary else ""

    with ui.card(align_items="center").classes(classes):
        ui_image = ui.image(pil_image)

        with ui.card_section():
            ui.label(str(path))

        with ui.card_actions():
            with ui.row(wrap=False):
                ui.button(
                    "Mirror",
                    on_click=lambda: modify_image(ImageOps.mirror, pil_image, ui_image),
                )
                ui.button(
                    "Flip",
                    on_click=lambda: modify_image(ImageOps.flip, pil_image, ui_image),
                )


def frontend_comparable(image: Path):
    frontend_image(image, True)


def frontend_similar(images: set[Path]):
    for image in images:
        frontend_image(image)


def frontend(images: dict[Path, set[Path]]):
    for image, similar in images.items():
        if not similar:
            continue

        with ui.row():
            with ui.column():
                frontend_comparable(image)
            with ui.grid(columns=4):
                frontend_similar(similar)

        ui.separator()


frontend(compare())
ui.run(dark=True)
