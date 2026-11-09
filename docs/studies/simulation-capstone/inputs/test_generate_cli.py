"""Exercise output protections through the generator command."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GENERATOR = Path(__file__).with_name("generate.py").resolve()


class GeneratorCliTests(unittest.TestCase):
    """Command-line failures preserve existing files and report the failed stage."""

    def run_generator(self, case, path, cwd):
        """Invoke the generator as an isolated Python process."""
        return subprocess.run(
            [sys.executable, "-B", str(GENERATOR), case, str(path)],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    def test_existing_output(self):
        """Protect existing directory contents, including a named array."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            payload = b"existing specimen bytes"
            specimen = output / "specimen.npy"
            specimen.write_bytes(payload)
            result = self.run_generator("clean", output, directory)
            self.assertEqual(result.returncode, 1)
            self.assertIn("failed at create output directory: FileExistsError", result.stderr)
            self.assertEqual(specimen.read_bytes(), payload)
            self.assertEqual(list(output.iterdir()), [specimen])

    def test_existing_symlink(self):
        """Protect the symlink and its target directory."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            output = Path(directory) / "output"
            output.symlink_to(target, target_is_directory=True)
            result = self.run_generator("clean", output, directory)
            self.assertEqual(result.returncode, 1)
            self.assertIn("failed at create output directory: FileExistsError", result.stderr)
            self.assertTrue(output.is_symlink())
            self.assertEqual(output.readlink(), target)
            self.assertEqual(list(target.iterdir()), [])

    def test_unknown_case(self):
        """Reject unrecognized cases without creating an output."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "new"
            result = self.run_generator("unknown", output, directory)
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid choice", result.stderr)
            self.assertFalse(output.exists())

    def test_missing_parent(self):
        """Report a missing parent at the output creation stage."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "missing" / "new"
            result = self.run_generator("clean", output, directory)
            self.assertEqual(result.returncode, 1)
            self.assertIn("failed at create output directory: FileNotFoundError", result.stderr)
            self.assertFalse(output.parent.exists())


if __name__ == "__main__":
    unittest.main()
