#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import enum
import logging

import pytest

from foodx_devops_tools.deploy_me import ExitState
from foodx_devops_tools.deploy_me._main import (
    DeploymentConfigurationError,
    _acquire_configuration_paths,
    _get_sha,
)
from foodx_devops_tools.deploy_me_entry import deploy_me
from foodx_devops_tools.pipeline_config import PipelineConfigurationPaths
from tests.ci.support.click_runner import click_runner  # noqa: F401
from tests.ci.support.pipeline_config import CLEAN_SPLIT, split_directories


class TestAcquireConfigurationPaths:
    def test_clean(self):
        with split_directories(CLEAN_SPLIT.copy()) as (
            client_config,
            system_config,
        ):
            result = _acquire_configuration_paths(client_config, system_config)

            assert result == PipelineConfigurationPaths(
                clients=client_config / "clients.yml",
                deployments=client_config / "deployments.yml",
                frames=client_config / "frames.yml",
                release_states=system_config / "release_states.yml",
                subscriptions=system_config / "subscriptions.yml",
                systems=system_config / "systems.yml",
                tenants=system_config / "tenants.yml",
            )

    def test_duplicates_raises(self):
        split = {
            # duplicates between client and system dirs
            "client": {
                "clients",
                "deployments",
                "frames",
                "release_states",
            },
            "system": {
                "release_states",
                "subscriptions",
                "systems",
                "tenants",
            },
        }
        with split_directories(split) as (
            client_config,
            system_config,
        ), pytest.raises(
            DeploymentConfigurationError,
            match=r"^Duplicate files between directories",
        ):
            _acquire_configuration_paths(client_config, system_config)


@pytest.fixture()
def mock_gitsha_result(mocker):
    def _apply(returncode: int, output: str = ""):
        mock_result = mocker.MagicMock()
        mock_result.returncode = returncode
        mock_result.stdout = output
        this_mock = mocker.patch(
            "foodx_devops_tools.deploy_me._main.run_command",
            return_value=mock_result,
        )
        return this_mock

    return _apply


class TestGetSha:
    def test_clean(self, mock_gitsha_result):
        mock_gitsha_result(0, output="abc123")
        result = _get_sha()

        assert result == "abc123"

    def test_error_raises(self, mock_gitsha_result):
        mock_gitsha_result(1)
        with pytest.raises(RuntimeError):
            _get_sha()


class TestDeployMe:
    class MockReleaseState(enum.Enum):
        r1 = enum.auto()

    def test_default(self, click_runner, caplog, mock_gitsha_result, mocker):
        mock_gitsha_result(0)
        mocker.patch(
            "foodx_devops_tools.deploy_me._main" ".identify_release_state",
            return_value=TestDeployMe.MockReleaseState.r1,
        )
        with caplog.at_level(logging.DEBUG):
            with split_directories(CLEAN_SPLIT.copy()) as (
                client_config,
                system_config,
            ):
                mock_input = [
                    str(client_config),
                    str(system_config),
                    "--git-ref",
                    "refs/heads/main",
                ]

                result = click_runner.invoke(deploy_me, mock_input)

                assert result.exit_code == 0
