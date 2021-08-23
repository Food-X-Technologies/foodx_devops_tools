#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import logging
import pathlib
import tempfile

import pytest

from foodx_devops_tools.pipeline_config import PipelineConfiguration
from foodx_devops_tools.pipeline_config._checks import (
    _file_exists,
    do_path_check,
)
from tests.ci.support.pipeline_config import MOCK_PATHS

log = logging.getLogger(__name__)


class TestFileExists:
    @pytest.mark.asyncio
    async def test_true(self):
        with tempfile.TemporaryDirectory() as dir:
            this_dir = pathlib.Path(dir)
            this_file = this_dir / "exists"
            with this_file.open(mode="w") as f:
                f.write("")

            assert await _file_exists(this_file)

    @pytest.mark.asyncio
    async def test_false(self):
        with tempfile.TemporaryDirectory() as dir:
            this_dir = pathlib.Path(dir)
            this_file = this_dir / "notexists"

            assert not this_file.is_file()

            assert not await _file_exists(this_file)


class TestDoPathCheck:
    @pytest.mark.asyncio
    async def test_clean(self, mock_loads, mock_results, mock_async_method):
        mock_async_method(
            "foodx_devops_tools.pipeline_config._checks._file_exists",
            return_value=True,
        )
        mock_loads(mock_results)
        mock_config = PipelineConfiguration.from_files(MOCK_PATHS)

        await do_path_check(mock_config)

    @pytest.mark.asyncio
    async def test_missing_file(
        self, mock_loads, mock_results, mock_async_method
    ):
        mock_async_method(
            "foodx_devops_tools.pipeline_config._checks._file_exists",
            side_effect=[True, False],
        )
        mock_loads(mock_results)
        mock_config = PipelineConfiguration.from_files(MOCK_PATHS)

        with pytest.raises(
            FileNotFoundError, match=r"files missing from " r"deployment"
        ):
            await do_path_check(mock_config)

    @pytest.mark.asyncio
    async def test_multiple_missing_files(
        self, mock_loads, mock_results, mock_async_method
    ):
        mock_async_method(
            "foodx_devops_tools.pipeline_config._checks" "._file_exists",
            side_effect=[False, False],
        )
        mock_loads(mock_results)
        mock_config = PipelineConfiguration.from_files(MOCK_PATHS)

        with pytest.raises(
            FileNotFoundError, match=r"files missing from " r"deployment"
        ):
            await do_path_check(mock_config)

    @pytest.mark.asyncio
    async def test_failed_check(
        self, mock_loads, mock_results, mock_async_method, mocker
    ):
        mocker.patch(
            "foodx_devops_tools.pipeline_config._checks._check_arm_files",
            side_effect=RuntimeError(),
        )
        mock_async_method(
            "foodx_devops_tools.pipeline_config._checks._file_exists",
            return_value=True,
        )
        mock_loads(mock_results)
        mock_config = PipelineConfiguration.from_files(MOCK_PATHS)

        with pytest.raises(RuntimeError):
            await do_path_check(mock_config)
