#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import pytest

from foodx_devops_tools.file_maintainer_entry import (
    RunMonitor,
    _clean_filesystem,
    _do_delete,
    _get_filesystem_capacity_used,
    _run_maintainer,
)

MOCK_PATH = pathlib.Path("some/path")
MOCK_THRESHOLD = 80


@pytest.fixture()
def mock_fs_actions(mock_async_method, mocker):
    def _apply(expected_capacity):
        mock_clean = mock_async_method(
            "foodx_devops_tools.file_maintainer_entry" "._clean_filesystem"
        )
        mocker.patch(
            "foodx_devops_tools.file_maintainer_entry"
            "._get_filesystem_capacity_used",
            return_value=expected_capacity,
        )

        return mock_clean

    return _apply


class TestRunMonitor:
    def test_keep_running_persistence(self):
        under_test = RunMonitor(10)
        # should always be true, but we cannot test "infinity"
        assert under_test.keep_running()
        assert under_test.keep_running()
        assert under_test.keep_running()

    def test_not_keep_running_no_persistence(self):
        under_test = RunMonitor(None)

        assert under_test.keep_running()
        assert not under_test.keep_running()
        assert not under_test.keep_running()

    @pytest.mark.asyncio
    async def test_sleep_persistence(self, mock_async_method):
        mock_sleep = mock_async_method(
            "foodx_devops_tools.file_maintainer_entry" ".asyncio.sleep"
        )
        under_test = RunMonitor(10)

        await under_test.sleep()

        mock_sleep.assert_called_once_with(600)

    @pytest.mark.asyncio
    async def test_no_sleep_no_persistence(self, mock_async_method):
        mock_sleep = mock_async_method(
            "foodx_devops_tools.file_maintainer_entry" ".asyncio.sleep"
        )
        under_test = RunMonitor(None)

        await under_test.sleep()

        mock_sleep.assert_not_called()


class TestRunMaintainer:
    @pytest.mark.asyncio
    async def test_below_threshold_no_clean(self, mock_fs_actions):
        mock_clean = mock_fs_actions(MOCK_THRESHOLD - 1)

        await _run_maintainer(MOCK_PATH, None, MOCK_THRESHOLD)

        mock_clean.assert_not_called()

    @pytest.mark.asyncio
    async def test_equal_threshold_clean(self, mock_fs_actions):
        mock_clean = mock_fs_actions(MOCK_THRESHOLD)

        await _run_maintainer(MOCK_PATH, None, MOCK_THRESHOLD)

        mock_clean.assert_called_once()

    @pytest.mark.asyncio
    async def test_above_threshold_clean(self, mock_fs_actions):
        mock_clean = mock_fs_actions(MOCK_THRESHOLD + 1)

        await _run_maintainer(MOCK_PATH, None, MOCK_THRESHOLD)

        mock_clean.assert_called_once()
