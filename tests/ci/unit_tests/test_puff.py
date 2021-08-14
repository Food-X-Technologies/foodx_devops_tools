#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import logging
import pathlib
import typing

from foodx_devops_tools.puff_utility import ExitState, PuffError, _main
from tests.ci.support.click_runner import (  # noqa: F401
    click_runner,
    isolated_filesystem,
)


@contextlib.contextmanager
def multifile_fs(
    expected_dir: str, this_runner
) -> typing.Generator[pathlib.Path, None, None]:
    with isolated_filesystem(expected_dir, this_runner) as temp_dir:
        with (temp_dir / "y1.yml").open(mode="w") as f:
            f.write(
                """---
name: some-y1
environments: {}
"""
            )

        with (temp_dir / "y2.yml").open(mode="w") as f:
            f.write(
                """---
name: some-y2
environments: {}
"""
            )
        yield temp_dir


@contextlib.contextmanager
def singlefile_fs(
    expected_dir: str, this_runner
) -> typing.Generator[pathlib.Path, None, None]:
    with isolated_filesystem(expected_dir, this_runner) as temp_dir:
        filename = temp_dir / "y1.yml"
        with filename.open(mode="w") as f:
            f.write(
                """---
name: some-y1
environments: {}
"""
            )
        yield filename


class TestMain:
    def test_single_file(self, caplog, click_runner, mocker):
        expected_dir = "some_path"
        caplog.set_level(logging.WARN)

        mocker.patch(
            "foodx_devops_tools.puff.run.load_puffignore",
            return_value=list(),
        )

        with singlefile_fs(expected_dir, click_runner) as puff_file:
            result = click_runner.invoke(_main, [str(puff_file)])

            message = "No puff parameter files found in directory"
            assert message not in caplog.text
            assert result.exit_code == 0

    def test_multifile(self, caplog, click_runner, mocker):
        expected_dir = "some_path"
        caplog.set_level(logging.WARN)

        mocker.patch(
            "foodx_devops_tools.puff.run.load_puffignore",
            return_value=list(),
        )

        with multifile_fs(expected_dir, click_runner) as temp_dir:
            result = click_runner.invoke(_main, [str(temp_dir)])

            assert result.exit_code == 0
            message = "No puff parameter files found in directory"
            assert message not in caplog.text

    def test_delete(self, caplog, click_runner, mocker):
        expected_dir = "some_path"

        mocker.patch(
            "foodx_devops_tools.puff.run.load_puffignore",
            return_value=list(),
        )

        for arg_form in ["-d", "--delete"]:
            with multifile_fs(expected_dir, click_runner) as temp_dir:
                result = click_runner.invoke(_main, [str(temp_dir), arg_form])

            assert result.exit_code == 0
            message = "No puff parameter files found in directory"
            assert message not in caplog.text

    def test_puff_error_exits_dirty(self, click_runner, mocker):
        expected_dir = "some_path"
        error_message = "some puff error"

        mocker.patch(
            "foodx_devops_tools.puff.run.load_puffignore",
            side_effect=PuffError(error_message),
        )

        with isolated_filesystem(expected_dir, click_runner) as temp_dir:
            result = click_runner.invoke(_main, [str(temp_dir)])

            assert result.exit_code == ExitState.PUFF_FAILED.value
            assert error_message in result.output

    def test_unknown_error_exits_dirty(self, click_runner, mocker):
        expected_dir = "some_path"
        error_message = "some unknown  error"

        mocker.patch(
            "foodx_devops_tools.puff.run.load_puffignore",
            side_effect=RuntimeError(error_message),
        )

        with isolated_filesystem(expected_dir, click_runner) as temp_dir:
            result = click_runner.invoke(_main, [str(temp_dir)])

            assert result.exit_code == ExitState.UNKNOWN.value
            assert "Puff failed with unexpected error" in result.output
            assert error_message in result.output
