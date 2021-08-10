#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import os
import pathlib
import re
import typing
from unittest.mock import AsyncMock

import pytest

from foodx_devops_tools.puff import run_puff
from foodx_devops_tools.puff.run import (
    DELETING_MESSAGE,
    GENERATING_MESSAGE,
    _acquire_yaml_filenames,
)
from tests.ci.support.capture import capture_stdout_stderr
from tests.ci.support.isolation import simple_isolated_filesystem


@contextlib.contextmanager
def mock_yaml_files(expected_files: typing.List[pathlib.Path]):
    with simple_isolated_filesystem() as dir:
        for this_file in [dir / x for x in expected_files]:
            os.makedirs(this_file.parent, exist_ok=True)
            with this_file.open(mode="w") as f:
                f.write("---")

        yield dir


class TestAcquireYamlFilenames:
    def test_no_files_found(self):
        with simple_isolated_filesystem() as dir:
            result = _acquire_yaml_filenames(dir, list())

        assert result == set()

    def test_yml(self):
        relative_files = [
            pathlib.Path("some/dir/a.yml"),
        ]
        with mock_yaml_files(relative_files) as dir:
            result = _acquire_yaml_filenames(dir, list())

        assert result == {dir / x for x in relative_files}

    def test_yaml(self):
        relative_files = [
            pathlib.Path("some/dir/a.yaml"),
        ]
        with mock_yaml_files(relative_files) as dir:
            result = _acquire_yaml_filenames(dir, list())

        assert result == {dir / x for x in relative_files}

    def test_no_ignore_patterns(self):
        relative_files = [
            pathlib.Path("some/dir/a.yml"),
            pathlib.Path("some/b.yaml"),
        ]
        with mock_yaml_files(relative_files) as dir:
            result = _acquire_yaml_filenames(dir, list())

        assert result == {dir / x for x in relative_files}

    def test_ignore_pattern1(self):
        relative_files = [
            pathlib.Path("some/dir/a.yml"),
            pathlib.Path("some/b.yaml"),
        ]
        ignore_pattern = ["some/dir/*"]
        with mock_yaml_files(relative_files) as dir:
            result = _acquire_yaml_filenames(dir, ignore_pattern)

        assert result == {dir / x for x in relative_files[1::]}

    def test_ignore_pattern2(self):
        relative_files = [
            pathlib.Path("some/dir/a.yml"),
            pathlib.Path("some/b.yaml"),
        ]
        ignore_pattern = ["**/dir/*"]
        with mock_yaml_files(relative_files) as dir:
            result = _acquire_yaml_filenames(dir, ignore_pattern)

        assert result == {dir / x for x in relative_files[1::]}

    def test_ignore_pattern3(self):
        relative_files = [
            pathlib.Path("some/dir/a.yml"),
            pathlib.Path("some/dir/b.yaml"),
            pathlib.Path("some/b.yaml"),
        ]
        ignore_pattern = ["**/b.yaml"]
        with mock_yaml_files(relative_files) as dir:
            result = _acquire_yaml_filenames(dir, ignore_pattern)

        assert result == {dir / x for x in relative_files[0:1]}

    def test_ignore_pattern4(self):
        relative_files = [
            pathlib.Path("some/a.yml"),
            pathlib.Path("some/dir/b.yaml"),
            pathlib.Path("some/deep/dir/b.yaml"),
            pathlib.Path("other/b.yaml"),
        ]
        ignore_pattern = ["some/**/*"]
        with mock_yaml_files(relative_files) as dir:
            result = _acquire_yaml_filenames(dir, ignore_pattern)

        assert result == {dir / x for x in relative_files[3:4]}


class TestRunPuff:
    @pytest.mark.asyncio
    async def test_generate_clean(self, capsys, mocker, mock_async_method):
        """Empty ignore patterns run acquires all YAML files."""
        mock_path = mocker.create_autospec(pathlib.Path)
        mock_path.is_dir.return_value = False
        mock_path.is_file.return_value = True
        mock_path.stem.return_value = "this_file"
        mocker.patch(
            "foodx_devops_tools.puff.run.load_puffignore",
            side_effect=AsyncMock(return_value=list()),
        )
        mock_async_method(
            "foodx_devops_tools.puff.arm.load_yaml",
            return_value={"environments": dict()},
        )
        mock_async_method("foodx_devops_tools.puff.arm._save_parameter_file")

        await run_puff(mock_path, False, False)

        result = capsys.readouterr().out
        assert GENERATING_MESSAGE in result

    @pytest.mark.asyncio
    async def test_delete_clean(self, capsys, mocker, mock_async_method):
        """Empty ignore patterns run acquires all YAML files."""
        mock_path = mocker.create_autospec(pathlib.Path)
        mock_path.is_dir.return_value = False
        mock_path.is_file.return_value = True
        mock_path.stem.return_value = "this_file"
        mocker.patch(
            "foodx_devops_tools.puff.run.load_puffignore",
            side_effect=AsyncMock(return_value=list()),
        )
        mock_async_method(
            "foodx_devops_tools.puff.arm.load_yaml",
            return_value={"environments": dict()},
        )
        mock_async_method("foodx_devops_tools.puff.arm._delete_parameter_file")

        await run_puff(mock_path, True, False)

        result = capsys.readouterr().out
        assert DELETING_MESSAGE in result
