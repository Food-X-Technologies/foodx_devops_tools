#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib
import typing

import pydantic
import pytest


@pytest.fixture
def apply_pipeline_config_test(mocker):
    def _apply(
        mock_content: str,
        method_under_test: typing.Callable[[pathlib.Path], pydantic.BaseModel],
    ):
        mock_path = mocker.create_autospec(pathlib.Path)("some/path")
        mock_path.open = mocker.mock_open(read_data=mock_content)

        result = method_under_test(mock_path)

        return result

    return _apply
