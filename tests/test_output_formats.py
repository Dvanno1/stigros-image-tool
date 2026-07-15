import tempfile
import unittest
from pathlib import Path

from PIL import Image

from Automatische_bottles import (
    FORMATS,
    OUTPUT_FORMATS,
    TARGET_FILL,
    WHITE,
    fit_on_white_canvas,
    is_supported_image,
    output_filename,
    output_suffix,
    save_output_image,
)


class OutputFormatTests(unittest.TestCase):
    def test_jfif_is_supported_as_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_folder:
            source = Path(temporary_folder) / "product.JFIF"
            Image.new("RGB", (10, 10), WHITE).save(
                source,
                format="JPEG",
            )

            self.assertTrue(is_supported_image(source))

    def test_output_filename_extensions(self) -> None:
        source = Path("product.avif")

        self.assertEqual(
            output_filename(
                source,
                output_suffix("wine", "png"),
            ),
            "product_115x180.png",
        )
        self.assertEqual(
            output_filename(
                source,
                output_suffix("wine", "jpg"),
            ),
            "product_115x180.jpg",
        )
        self.assertEqual(
            output_filename(
                source,
                output_suffix("beer", "png"),
            ),
            "product_115x180.png",
        )

    def test_product_uses_configured_canvas_fill(self) -> None:
        source = Image.new("RGB", (100, 200), (0, 0, 0))

        for product_key, product_settings in FORMATS.items():
            with self.subTest(product=product_key):
                width = int(product_settings["width"])
                height = int(product_settings["height"])
                processed = fit_on_white_canvas(
                    source,
                    width,
                    height,
                )
                foreground = processed.point(
                    lambda value: 255 if value < 243 else 0
                ).getbbox()

                self.assertIsNotNone(foreground)
                assert foreground is not None
                product_width = foreground[2] - foreground[0]
                product_height = foreground[3] - foreground[1]

                self.assertTrue(
                    abs(product_width - round(width * TARGET_FILL)) <= 1
                    or abs(
                        product_height
                        - round(height * TARGET_FILL)
                    ) <= 1
                )

    def test_saving_all_size_and_output_combinations(self) -> None:
        source = Image.new(
            "RGBA",
            (100, 200),
            (120, 30, 20, 255),
        )

        with tempfile.TemporaryDirectory() as temporary_folder:
            folder = Path(temporary_folder)

            for product_key, product_settings in FORMATS.items():
                for output_key, output_settings in OUTPUT_FORMATS.items():
                    with self.subTest(
                        product=product_key,
                        output=output_key,
                    ):
                        processed = fit_on_white_canvas(
                            source,
                            int(product_settings["width"]),
                            int(product_settings["height"]),
                        )
                        destination = folder / (
                            "product"
                            + output_suffix(product_key, output_key)
                        )

                        save_output_image(
                            processed,
                            destination,
                            output_key,
                        )

                        self.assertTrue(destination.exists())
                        self.assertEqual(
                            destination.suffix,
                            output_settings["extension"],
                        )

                        with Image.open(destination) as saved:
                            self.assertEqual(
                                saved.size,
                                (
                                    product_settings["width"],
                                    product_settings["height"],
                                ),
                            )
                            self.assertEqual(saved.mode, "RGB")
                            self.assertEqual(
                                saved.format,
                                output_settings["pillow_format"],
                            )
                            if output_key == "png":
                                self.assertEqual(
                                    saved.getpixel((0, 0)),
                                    WHITE,
                                )
                            else:
                                corner = saved.getpixel((0, 0))
                                self.assertTrue(
                                    all(channel >= 250 for channel in corner)
                                )


if __name__ == "__main__":
    unittest.main()
