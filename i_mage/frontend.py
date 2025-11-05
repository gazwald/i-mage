from __future__ import annotations

from pathlib import Path

from nicegui import run, ui
from PIL import ImageOps

from i_mage.compare import compare, open_image


async def modify_image(func, image, ui_image):
    result = await run.cpu_bound(func, image)
    ui_image.set_source(result)


def frontend_image(path: Path, primary: bool = False):
    pil_image = open_image(path)
    classes = "bg-blue-500" if primary else ""

    with ui.card(align_items="center").classes(classes):
        ui_image = ui.image(path)

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


def frontend():
    images = compare()
    for image, similar in images.items():
        if not similar:
            continue

        with ui.row():
            with ui.column():
                frontend_comparable(image)
            with ui.grid(columns=4):
                frontend_similar(similar)

        ui.separator()
