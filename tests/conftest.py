#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy
import pathlib
import typing

import pydantic
import pytest

from foodx_devops_tools.pipeline_config import PipelineConfiguration
from foodx_devops_tools.pipeline_config.views import (
    DeploymentContext,
    ReleaseView,
)
from tests.ci.support.pipeline_config import MOCK_RESULTS


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


@pytest.fixture
def mock_pipeline_config():
    def _apply(mock_data=MOCK_RESULTS.copy()) -> PipelineConfiguration:
        return PipelineConfiguration.parse_obj(mock_data)

    return _apply


@pytest.fixture()
def mock_flattened_deployment(mock_pipeline_config):
    base_context = DeploymentContext(
        commit_sha="abc123",
        pipeline_id="123456",
        release_id="3.1.4+local",
        release_state="r1",
    )
    pipeline_state = ReleaseView(mock_pipeline_config(), base_context)
    mock_flattened = pipeline_state.flatten()

    return copy.deepcopy(mock_flattened)
