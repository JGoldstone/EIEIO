import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
import os
import stat

from eieio.measurement.instructions import Instructions

REQUIRED_ARGS = ['--device_type', 'i1Pro', '--base_measurement_name', 'foo', '--sequence_file', 'bar']

class InstructionsTest(unittest.TestCase):
    def test_overriding_sys_argv(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_dir_foo_subdir = str(Path(tmp_dir, 'foo'))
            overriding_args = ['--output_dir', tmp_dir_foo_subdir]
            overriding_args.extend(REQUIRED_ARGS)
            instructions = Instructions(__file__, 'unit test', args=overriding_args)
            self.assertEqual(instructions.args.output_dir, tmp_dir_foo_subdir)

    def test_nonexistent_and_parent_exists(self):
        with TemporaryDirectory() as tmp_dir:
            output_dir = str(Path(tmp_dir, 'foo'))
            overriding_args = ['--output_dir', output_dir]
            overriding_args.extend(REQUIRED_ARGS)
            Instructions(__file__, 'unit test', args=overriding_args)
            self.assertTrue(Path(output_dir).exists())

    def test_missing_parent_raises(self):
        with TemporaryDirectory() as tmp_dir:
            output_dir = str(Path(tmp_dir, 'foo', 'bar'))
            overriding_args = ['--output_dir', output_dir]
            overriding_args.extend(REQUIRED_ARGS)
            with self.assertRaises(FileNotFoundError):
                Instructions(__file__, 'unit test', args=overriding_args)

    def test_missing_parent_handled(self):
        with TemporaryDirectory() as tmp_dir:
            output_dir = str(Path(tmp_dir, 'foo', 'bar'))
            overriding_args = ['--output_dir', output_dir, '--create_parent_dirs']
            overriding_args.extend(REQUIRED_ARGS)
            Instructions(__file__, 'unit test', args=overriding_args)
            self.assertTrue(Path(output_dir).exists())

    def test_exists_raises(self):
        with TemporaryDirectory() as tmp_dir:
            output_dir = str(Path(tmp_dir))
            overriding_args = ['--output_dir', output_dir]
            overriding_args.extend(REQUIRED_ARGS)
            with self.assertRaises(FileExistsError):
                Instructions(__file__, 'unit test', args=overriding_args)

    def test_exists_handled(self):
        with TemporaryDirectory() as tmp_dir:
            output_dir = str(Path(tmp_dir))
            overriding_args = ['--output_dir', output_dir, '--exists_ok']
            overriding_args.extend(REQUIRED_ARGS)
            Instructions(__file__, 'unit test', args=overriding_args)
            self.assertTrue(Path(output_dir).exists())

    def test_exists_but_unwritable_handled(self):
        with TemporaryDirectory() as tmp_dir:
            output_dir = str(Path(tmp_dir))
            overriding_args = ['--output_dir', output_dir, '--exists_ok']
            overriding_args.extend(REQUIRED_ARGS)
            with self.assertRaises(PermissionError):
                os.chmod(output_dir, stat.S_IRUSR)
                Instructions(__file__, 'unit test', args=overriding_args)

if __name__ == '__main__':
    unittest.main()
