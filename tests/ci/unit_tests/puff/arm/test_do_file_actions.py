#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib

import pytest

from foodx_devops_tools.puff.arm import _do_file_actions


class TestDoFileActions:
    MOCK_PARAMETER_DATA = {
        "some-file": {
            "k1": "v1",
        }
    }

    @pytest.mark.asyncio
    async def test_delete_clean(self, mocker):
        mock_delete = mocker.patch(
            "foodx_devops_tools.puff.arm._delete_parameter_file"
        )
        mocker.patch("foodx_devops_tools.puff.arm._save_parameter_file")

        await _do_file_actions(
            True, pathlib.Path("some/path"), self.MOCK_PARAMETER_DATA, False
        )

        mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_clean(self, mocker):
        mocker.patch("foodx_devops_tools.puff.arm._delete_parameter_file")
        mock_save = mocker.patch(
            "foodx_devops_tools.puff.arm._save_parameter_file"
        )

        await _do_file_actions(
            False, pathlib.Path("some/path"), self.MOCK_PARAMETER_DATA, False
        )

        mock_save.assert_called_once()
