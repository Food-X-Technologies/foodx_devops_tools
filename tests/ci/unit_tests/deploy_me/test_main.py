#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import enum
import logging

import pytest

from foodx_devops_tools.deploy_me._deployment import DeploymentState
from foodx_devops_tools.deploy_me._main import (
    ConfigurationPathsError,
    _get_sha,
    acquire_configuration_paths,
    do_deploy,
)
from foodx_devops_tools.deploy_me_entry import deploy_me
from foodx_devops_tools.pipeline_config import PipelineConfigurationPaths
from tests.ci.support.asyncio import mock_async_method  # noqa: F401
from tests.ci.support.click_runner import click_runner  # noqa: F401
from tests.ci.support.pipeline_config import CLEAN_SPLIT, split_directories


class TestAcquireConfigurationPaths:
    def test_clean(self):
        with split_directories(CLEAN_SPLIT.copy()) as (
            client_config,
            system_config,
        ):
            result = acquire_configuration_paths(client_config, system_config)

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
            ConfigurationPathsError,
            match=r"^Duplicate files between directories",
        ):
            acquire_configuration_paths(client_config, system_config)


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


@pytest.fixture()
def mock_getsha(mocker):
    def _apply(output: str = ""):
        mocker.patch(
            "foodx_devops_tools.deploy_me._main._get_sha",
            return_value=output,
        )

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

    def test_default(
        self,
        click_runner,
        caplog,
        mock_async_method,
        mock_getsha,
        mocker,
    ):
        mock_input = list()

        result, mock_deploy = self._run_test(
            mock_input,
            caplog,
            click_runner,
            mock_async_method,
            mock_getsha,
            mocker,
        )

        assert result.exit_code == 0
        mock_deploy.assert_has_calls(
            [
                mocker.call(mocker.ANY, mocker.ANY, False),
                mocker.call(mocker.ANY, mocker.ANY, False),
            ]
        )

    def test_pipeline_id(
        self,
        click_runner,
        caplog,
        mock_async_method,
        mock_getsha,
        mocker,
    ):
        mock_input = [
            "--pipeline-id",
            "refs/heads/main",
        ]

        result, mock_deploy = self._run_test(
            mock_input,
            caplog,
            click_runner,
            mock_async_method,
            mock_getsha,
            mocker,
        )

        assert result.exit_code == 0
        mock_deploy.assert_has_calls(
            [
                mocker.call(mocker.ANY, mocker.ANY, False),
                mocker.call(mocker.ANY, mocker.ANY, False),
            ]
        )

    def _run_test(
        self,
        mock_input,
        caplog,
        click_runner,
        mock_async_method,
        mock_getsha,
        mocker,
    ):
        mock_getsha()
        mocker.patch(
            "foodx_devops_tools.deploy_me._main.identify_release_state",
            return_value=TestDeployMe.MockReleaseState.r1,
        )
        mock_deploy = mock_async_method(
            "foodx_devops_tools.deploy_me._main.do_deploy",
            return_value=DeploymentState(
                code=DeploymentState.ResultType.success
            ),
        )
        # mock_deploy = mocker.patch(
        #     "foodx_devops_tools.deploy_me._main.asyncio.run"
        # )
        # mock_deploy = mock_async_method(
        #     "foodx_devops_tools.deploy_me._main.asyncio.run"
        # )
        with split_directories(CLEAN_SPLIT.copy()) as (
            client_config,
            system_config,
        ):
            mock_input += [
                str(client_config),
                str(system_config),
                # --git-ref is mandatory, for now
                "--git-ref",
                "refs/heads/main",
            ]
            with caplog.at_level(logging.DEBUG):
                result = click_runner.invoke(deploy_me, mock_input)

        return result, mock_deploy

    def test_validation(
        self,
        caplog,
        click_runner,
        mock_async_method,
        mock_getsha,
        mocker,
    ):
        mock_input = [
            "--validation",
        ]

        result, mock_deploy = self._run_test(
            mock_input,
            caplog,
            click_runner,
            mock_async_method,
            mock_getsha,
            mocker,
        )

        assert result.exit_code == 0
        mock_deploy.assert_has_calls(
            [
                mocker.call(mocker.ANY, mocker.ANY, True),
                mocker.call(mocker.ANY, mocker.ANY, True),
            ]
        )
