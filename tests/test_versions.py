import unittest

from Automatische_bottles import is_newer_version


class VersionComparisonTests(unittest.TestCase):
    def test_new_patch_version_with_v_prefix(self) -> None:
        self.assertTrue(
            is_newer_version("1.0.0", "v1.0.1")
        )

    def test_same_version_with_v_prefix(self) -> None:
        self.assertFalse(
            is_newer_version("1.0.1", "v1.0.1")
        )

    def test_minor_versions_are_compared_numerically(self) -> None:
        self.assertTrue(
            is_newer_version("1.2.0", "v1.10.0")
        )

    def test_malformed_or_missing_latest_tag_is_ignored(self) -> None:
        invalid_values = (
            None,
            "",
            "nieuwste",
            "v1.0",
            "v1.0.01",
            {},
        )

        for value in invalid_values:
            with self.subTest(value=value):
                self.assertFalse(
                    is_newer_version("1.0.0", value)
                )

    def test_prerelease_has_lower_precedence_than_release(self) -> None:
        self.assertTrue(
            is_newer_version("1.1.0-rc.1", "v1.1.0")
        )
        self.assertFalse(
            is_newer_version("1.1.0", "v1.1.0-rc.1")
        )


if __name__ == "__main__":
    unittest.main()
