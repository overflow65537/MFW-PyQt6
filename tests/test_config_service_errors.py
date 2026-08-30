import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.core.service.config_service import (
    ConfigLoadError,
    ConfigService,
    JsonConfigRepository,
)


class JsonConfigRepositoryErrorTests(unittest.TestCase):
    def test_invalid_json_is_wrapped_with_file_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "broken.json"
            path.write_text("{broken", encoding="utf-8")

            with self.assertRaises(ConfigLoadError) as raised:
                JsonConfigRepository._load_json(path)

        self.assertEqual(path, raised.exception.path)
        self.assertIsNotNone(raised.exception.__cause__)

    def test_missing_file_is_wrapped_with_file_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.json"

            with self.assertRaises(ConfigLoadError) as raised:
                JsonConfigRepository._load_json(path)

        self.assertEqual(path, raised.exception.path)
        self.assertIsInstance(raised.exception.cause, OSError)


class ConfigServiceErrorBoundaryTests(unittest.TestCase):
    def test_programming_error_from_repository_is_not_swallowed(self):
        repository = SimpleNamespace(
            interface={},
            load_main_config=lambda: (_ for _ in ()).throw(
                ValueError("invalid repository state")
            ),
        )

        with self.assertRaisesRegex(ValueError, "invalid repository state"):
            ConfigService(repository, SimpleNamespace())


if __name__ == "__main__":
    unittest.main()
