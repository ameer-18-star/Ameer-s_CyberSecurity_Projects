"""Tests for CommandRunner. run() is called directly (rather than via
.start()) so these don't need a live Qt event loop — Qt signals fire
synchronously either way when there's no event loop pumping them."""

from core.command_runner import CommandRunner


def test_emits_error_for_missing_binary():
    runner = CommandRunner(["definitely-not-a-real-binary-xyz"])
    errors = []
    runner.error.connect(lambda msg: errors.append(msg))
    runner.run()
    assert errors and "not found" in errors[0]


def test_successful_command_emits_finished_ok():
    runner = CommandRunner(["echo", "hello"])
    lines = []
    codes = []
    runner.log_line.connect(lambda line: lines.append(line))
    runner.finished_ok.connect(lambda code: codes.append(code))
    runner.run()
    assert lines == ["hello"]
    assert codes == [0]


def test_nonzero_exit_code_reported():
    runner = CommandRunner(["sh", "-c", "exit 3"])
    codes = []
    runner.finished_ok.connect(lambda code: codes.append(code))
    runner.run()
    assert codes == [3]


def test_stop_before_start_is_safe():
    runner = CommandRunner(["echo", "hi"])
    runner.stop()  # should not raise even though nothing was launched


def test_stop_sets_flag_and_does_not_raise_with_no_process():
    runner = CommandRunner(["echo", "hi"])
    runner.stop()
    assert runner._stop_requested is True