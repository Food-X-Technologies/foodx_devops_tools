#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy
import pathlib
import typing
import unittest.mock

import pydantic
import pytest
from asynctest import CoroutineMock

from foodx_devops_tools.pipeline_config import PipelineConfiguration
from foodx_devops_tools.pipeline_config.views import (
    DeploymentContext,
    ReleaseView,
)
from tests.ci.support.pipeline_config import MOCK_RESULTS, MOCK_TO


@pytest.fixture()
def mock_run_puff_check(mock_async_method):
    mock_async_method("foodx_devops_tools.pipeline_config._checks.run_puff")


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
    def _apply(mock_data=copy.deepcopy(MOCK_RESULTS)) -> PipelineConfiguration:
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
    mock_flattened = pipeline_state.flatten(MOCK_TO)

    return copy.deepcopy(mock_flattened)


@pytest.fixture()
def mock_async_method(mocker):
    def _apply(
        path_to_mock: str,
        return_value: typing.Optional[typing.Any] = None,
        side_effect: typing.Optional[typing.Any] = None,
    ):
        async_mock = unittest.mock.AsyncMock(
            return_value=return_value, side_effect=side_effect
        )
        this_mock = mocker.patch(path_to_mock, side_effect=async_mock)

        return this_mock

    return _apply


@pytest.fixture()
def mock_context(mocker):
    def _apply(path_to_mock: str):
        this_mock = mocker.patch(path_to_mock)
        this_mock.return_value.__aenter__.return_value.write = CoroutineMock()

        return this_mock

    return _apply
