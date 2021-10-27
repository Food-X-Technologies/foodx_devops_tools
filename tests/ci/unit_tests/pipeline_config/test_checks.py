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
from tests.ci.support.pipeline_config import MOCK_PATHS, MOCK_SECRET

log = logging.getLogger(__name__)


@pytest.fixture()
def mock_file_exists(mock_async_method, mock_verify_puff_target):
    def _apply(return_value=None, side_effect=None):
        mock_async_method(
            "foodx_devops_tools.pipeline_config._checks._file_exists",
            return_value=return_value,
            side_effect=side_effect,
        )

    return _apply


@pytest.fixture()
def path_check_mocks(
    mock_apply_template,
    mock_loads,
    mock_results,
    mock_run_puff_check,
    mock_file_exists,
):
    def _apply(return_value=None, side_effect=None):
        mock_file_exists(return_value=return_value, side_effect=side_effect)
        mock_loads(mock_results)

        mock_config = PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

        return mock_config

    return _apply


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
    async def test_clean(self, path_check_mocks):
        mock_config = path_check_mocks(return_value=True)

        await do_path_check(mock_config)

    @pytest.mark.asyncio
    async def test_missing_file(self, path_check_mocks):
        mock_config = path_check_mocks(
            side_effect=[True, False, True, True, True]
        )

        with pytest.raises(
            FileNotFoundError, match=r"files missing from deployment"
        ):
            await do_path_check(mock_config)

    @pytest.mark.asyncio
    async def test_multiple_missing_files(self, path_check_mocks):
        mock_config = path_check_mocks(
            side_effect=[False, False, False, False, False]
        )

        with pytest.raises(
            FileNotFoundError, match=r"files missing from deployment"
        ):
            await do_path_check(mock_config)

    @pytest.mark.asyncio
    async def test_failed_check(
        self,
        path_check_mocks,
        mocker,
    ):
        mocker.patch(
            "foodx_devops_tools.pipeline_config._checks._check_arm_files",
            side_effect=RuntimeError(),
        )
        mock_config = path_check_mocks(return_value=True)

        with pytest.raises(RuntimeError):
            await do_path_check(mock_config)
