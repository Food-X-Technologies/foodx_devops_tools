#  Copyright (c) 2020 Russell Smiley
#  Copyright (c) 2021 Food-X Technologies
#
#  You should have received a copy of the MIT License along with build_harness.
#  If not, see <https://opensource.org/licenses/MIT>.
#
# https://gitlab.com/ci-cd-devops/build_harness/-/blob/main/tests/ci/unit_tests/test_utility.py

import asyncio
from unittest.mock import AsyncMock

import pytest

from foodx_devops_tools.utilities import (
    CapturedStreams,
    run_async_command,
    run_command,
)


class TestRunCommand:
    def test_simple(self, mocker):
        mock_run = mocker.patch(
            "foodx_devops_tools.utilities.command.subprocess.run"
        )
        command = ["something", "--option"]

        result = run_command(command)

        mock_run.assert_called_once_with(command)
        assert result == mock_run.return_value


class TestRunAsyncCommand:
    @pytest.mark.asyncio
    async def test_simple(self, mocker):
        expected_output = CapturedStreams(out="123", error="no errors")
        async_mock = AsyncMock()
        async_mock.return_value.returncode = 0
        async_mock.return_value.communicate.return_value = (
            expected_output.out.encode(),
            expected_output.error.encode(),
        )
        mock_run = mocker.patch(
            "foodx_devops_tools.utilities.command.asyncio"
            ".create_subprocess_exec",
            side_effect=async_mock,
        )
        command = ["something", "--option"]

        result = await run_async_command(command)

        mock_run.assert_called_once_with(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        assert result == expected_output
