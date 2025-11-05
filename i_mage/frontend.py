from __future__ import annotations

from nicegui import run, ui
from PIL import ImageOps

from i_mage.compare import ImageDetails, compare


async def modify_image(func, image, ui_image):
    result = await run.cpu_bound(func, image)
    ui_image.set_source(result)


def frontend_image(image: ImageDetails, primary: bool = False):
    pil_image = image.image
    classes = "bg-blue-500" if primary else ""

    with ui.card(align_items="center").classes(classes):
        ui_image = ui.image(image.image)

        with ui.card_section():
            ui.label(f"Path: {image.path}")
            ui.label(f"Size: {image.size}kb")
            ui.label(f"Res: {image.resolution}")
            if not primary:
                ui.label(f"Diff: {image.difference:0.2f}")

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


def frontend_comparable(image: ImageDetails):
    frontend_image(image, True)


def frontend_similar(images: set[ImageDetails]):
    for image in sorted(images):
        frontend_image(image)


@ui.refreshable
def frontend_images():
    for image in compare():
        with ui.row():
            with ui.column():
                frontend_comparable(image)
            with ui.grid(columns=4):
                frontend_similar(image.similar)

        ui.separator()


def get_images():
    frontend_images()


def frontend():
    ui.button("Go", on_click=get_images)
