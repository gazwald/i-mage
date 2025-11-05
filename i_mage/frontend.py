from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from nicegui import run, ui
from PIL import ImageOps

from i_mage.compare import compare

if TYPE_CHECKING:
    from typing import Callable

    from nicegui.elements.image import Image as UI_Image
    from nicegui.elements.row import Row
    from PIL.Image import Image as PIL_Image

    from i_mage.compare import ImageDetails


async def mark_duplicate(image: ImageDetails, card):
    image.duplicate = True
    card.visible = False
    image.path.move(Path("./duplicate"))


async def modify_image(func: Callable, image: PIL_Image, ui_image: UI_Image):
    result = await run.cpu_bound(func, image)
    ui_image.set_source(result)


def image_info(image: ImageDetails, primary: bool):
    with ui.card_section():
        ui.label(f"Path: {image.path}")
        ui.label(f"Size: {image.size}kb")
        ui.label(f"Reso: {image.resolution}")
        if not primary:
            ui.label(f"Diff: {image.difference:0.2f}")


def frontend_image(image: ImageDetails, primary: bool = False):
    pil_image = image.image
    classes = "bg-blue-500" if primary else ""

    with ui.card(align_items="center").classes(classes) as card:
        ui_image = ui.image(image.image)
        image_info(image, primary)
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
                ui.button("Delete", on_click=lambda: mark_duplicate(image, card))


def frontend_comparable(image: ImageDetails):
    frontend_image(image, True)


def frontend_similar(images: set[ImageDetails], row: Row):
    if all(image.duplicate for image in images):
        row.visible = False
    else:
        for image in sorted(images):
            frontend_image(image)


def frontend_images():
    for image in compare():
        with ui.row() as row:
            with ui.column():
                frontend_comparable(image)
            with ui.grid(columns=4):
                frontend_similar(image.similar, row)

        ui.separator()


def frontend():
    ui.button("Go", on_click=frontend_images)
