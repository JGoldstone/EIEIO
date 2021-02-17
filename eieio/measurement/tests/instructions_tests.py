import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from eieio.measurement.instructions import Instructions


class InstructionsTest(unittest.TestCase):
    def test_overriding_sys_argv(self):
        slash_tmp = '/tmp/foo'
        overriding_args = ['--output_dir', slash_tmp]
        instructions = Instructions(__file__, 'unit test', args=overriding_args)
        self.assertEqual(instructions.args.output_dir, slash_tmp)

    def test_nonexistent_and_parent_exists(self):
        with TemporaryDirectory() as tmp_dir:
            output_dir = str(Path(tmp_dir, 'foo'))
            overriding_args = ['--output_dir', output_dir]
            instructions = Instructions(__file__, 'unit test', args=overriding_args)
            self.assertEqual(True, Path(output_dir).exists())

if __name__ == '__main__':
    unittest.main()
