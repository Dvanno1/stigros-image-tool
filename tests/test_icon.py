import unittest
from pathlib import Path

from PIL import Image


class WindowsIconTests(unittest.TestCase):
    def test_ico_contains_required_resolutions(self) -> None:
        icon_path = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "stigros_logo.ico"
        )
        required_sizes = {
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        }

        with Image.open(icon_path) as icon:
            self.assertEqual(icon.format, "ICO")
            self.assertTrue(
                required_sizes.issubset(icon.ico.sizes())
            )


if __name__ == "__main__":
    unittest.main()
