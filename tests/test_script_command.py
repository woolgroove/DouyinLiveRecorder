import os
import tempfile
import unittest
from pathlib import Path

from src.script_utils import build_script_command, has_recording_output


class BuildScriptCommandTests(unittest.TestCase):
    def test_direct_shell_command_does_not_receive_recording_parameters(self):
        command = build_script_command(
            "shutdown /s /t 600",
            python_params=['--record_name "主播"'],
            positional_params=['"主播"', '"N/A"'],
        )

        self.assertEqual(command, "shutdown /s /t 600")

    def test_python_script_receives_named_parameters(self):
        command = build_script_command(
            "python notify.py",
            python_params=['--record_name "主播"', '--save_file_path "record.ts"'],
            positional_params=['"主播"', '"record.ts"'],
        )

        self.assertEqual(
            command,
            'python notify.py --record_name "主播" --save_file_path "record.ts"',
        )

    def test_script_file_receives_positional_parameters(self):
        command = build_script_command(
            '"C:\\Scripts\\notify.bat"',
            python_params=['--record_name "主播"'],
            positional_params=['"主播"', '"record.ts"'],
        )

        self.assertEqual(
            command,
            '"C:\\Scripts\\notify.bat" "主播" "record.ts"',
        )

    def test_python_named_directory_does_not_change_batch_parameter_style(self):
        command = build_script_command(
            '"C:\\python-tools\\notify.bat"',
            python_params=['--record_name "主播"'],
            positional_params=['"主播"', '"record.ts"'],
        )

        self.assertEqual(
            command,
            '"C:\\python-tools\\notify.bat" "主播" "record.ts"',
        )

    def test_direct_python_file_receives_named_parameters(self):
        command = build_script_command(
            '"C:\\Scripts\\notify.py"',
            python_params=['--record_name "主播"'],
            positional_params=['"主播"', '"record.ts"'],
        )

        self.assertEqual(
            command,
            '"C:\\Scripts\\notify.py" --record_name "主播"',
        )


class HasRecordingOutputTests(unittest.TestCase):
    def test_non_split_file_exists_and_nonempty(self):
        self.assertTrue(has_recording_output(__file__, split=False))
        self.assertFalse(
            has_recording_output(str(Path(__file__).with_name('missing.ts')), split=False)
        )

    def test_split_detects_prefix_match_with_nonzero_size(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            segment = os.path.join(temp_dir, '主播_title_2026-07-16_00-00-00_000.ts')
            with open(segment, 'wb') as handle:
                handle.write(b'x')
            save_path = os.path.join(temp_dir, '主播_title_2026-07-16_00-00-00_%03d.ts')
            self.assertTrue(has_recording_output(save_path, split=True))


if __name__ == "__main__":
    unittest.main()
