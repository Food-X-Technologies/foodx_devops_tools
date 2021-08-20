#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.


import pytest

from foodx_devops_tools.utilities import get_sha


@pytest.fixture()
def mock_gitsha_result(mocker):
    def _apply(returncode: int, output: str = ""):
        mock_result = mocker.MagicMock()
        mock_result.returncode = returncode
        mock_result.stdout = output
        this_mock = mocker.patch(
            "foodx_devops_tools.utilities.git.run_command",
            return_value=mock_result,
        )
        return this_mock

    return _apply


class TestGetSha:
    def test_clean(self, mock_gitsha_result):
        mock_gitsha_result(0, output="abc123")
        result = get_sha()

        assert result == "abc123"

    def test_error_raises(self, mock_gitsha_result):
        mock_gitsha_result(1)
        with pytest.raises(RuntimeError):
            get_sha()
