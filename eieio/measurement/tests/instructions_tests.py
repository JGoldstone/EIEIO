import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from eieio.measurement.instructions import Instructions


class InstructionsTest(unittest.TestCase):
    def test_overriding_sys_argv(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_dir_foo_subdir = str(Path(tmp_dir, 'foo'))
            overriding_args = ['--output_dir', tmp_dir_foo_subdir]
            instructions = Instructions(__file__, 'unit test', args=overriding_args)
            self.assertEqual(instructions.args.output_dir, tmp_dir_foo_subdir)

    def test_nonexistent_and_parent_exists(self):
        with TemporaryDirectory() as tmp_dir:
            output_dir = str(Path(tmp_dir, 'foo'))
            overriding_args = ['--output_dir', output_dir]
            Instructions(__file__, 'unit test', args=overriding_args)
            self.assertTrue(Path(output_dir).exists())

    def test_missing_parent_raises(self):
        with TemporaryDirectory() as tmp_dir:
            output_dir = str(Path(tmp_dir, 'foo', 'bar'))
            overriding_args = ['--output_dir', output_dir]
            with self.assertRaises(FileNotFoundError):
                Instructions(__file__, 'unit test', args=overriding_args)

    def test_missing_parent_handled(self):
        with TemporaryDirectory() as tmp_dir:
            output_dir = str(Path(tmp_dir, 'foo', 'bar'))
            overriding_args = ['--output_dir', output_dir, '--create_parent_dirs']
            Instructions(__file__, 'unit test', args=overriding_args)
            self.assertTrue(Path(output_dir).exists())


if __name__ == '__main__':
    unittest.main()
