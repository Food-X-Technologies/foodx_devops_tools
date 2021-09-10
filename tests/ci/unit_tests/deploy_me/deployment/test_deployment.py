#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.
import pathlib

import pytest

from foodx_devops_tools.deploy_me._deployment import (
    ApplicationDeploymentDefinition,
    DeploymentState,
    _construct_arm_paths,
    _construct_fqdn,
    _construct_resource_group_name,
    assess_results,
)
from foodx_devops_tools.pipeline_config.frames import DeploymentMode


class TestConstructFqdn:
    def test_structured_subscription(self):
        result = _construct_fqdn(
            "api", "some.where", "client", "system_client_stub"
        )

        assert result == "api.stub.client.some.where"

    def test_unstructured_subscription(self):
        result = _construct_fqdn(
            "api", "some.where", "client", "system_client_stub"
        )

        assert result == "api.stub.client.some.where"


class TestConstructResourceGroupName:
    def test_clean(self):
        result = _construct_resource_group_name("app", "frame", "client")

        assert result == "app-frame-client"


class TestAssessResults:
    @pytest.mark.asyncio
    async def test_success(self):
        mock_results = [
            DeploymentState(code=DeploymentState.ResultType.success),
            DeploymentState(code=DeploymentState.ResultType.success),
        ]

        result = await assess_results(mock_results)

        assert result.code == DeploymentState.ResultType.success

    @pytest.mark.asyncio
    async def test_fail(self):
        mock_results = [
            DeploymentState(code=DeploymentState.ResultType.success),
            DeploymentState(code=DeploymentState.ResultType.failed),
        ]

        result = await assess_results(mock_results)

        assert result.code == DeploymentState.ResultType.failed


class TestConstructArmPaths:
    def test_none_arm_file_puff_file(self):
        mock_app_name = "this_app"
        mock_puff_parameter_name = "some.puff.file.json"
        mock_frame_folder = pathlib.Path("some/path")
        mock_step = ApplicationDeploymentDefinition(
            mode=DeploymentMode.incremental,
            name="somename",
            arm_file=None,
            puff_file=None,
        )

        result_template, result_puff, result_parameters = _construct_arm_paths(
            mock_step,
            mock_puff_parameter_name,
            mock_app_name,
            mock_frame_folder,
        )

        assert result_template == pathlib.Path("some/path/this_app.json")
        assert result_puff == pathlib.Path("some/path/this_app.yml")

    def test_parameter_file(self):
        mock_app_name = "this_app"
        mock_puff_parameter_name = "some.puff.file.json"
        mock_frame_folder = pathlib.Path("some/path")
        mock_step = ApplicationDeploymentDefinition(
            mode=DeploymentMode.incremental,
            name="somename",
        )

        result_template, result_puff, result_parameters = _construct_arm_paths(
            mock_step,
            mock_puff_parameter_name,
            mock_app_name,
            mock_frame_folder,
        )

        assert result_parameters == pathlib.Path(
            "some/path/some.puff.file.json"
        )

    def test_arm_file_none_puff_file(self):
        mock_app_name = "this_app"
        mock_puff_parameter_name = "some.puff.file.json"
        mock_frame_folder = pathlib.Path("some/path")
        mock_step = ApplicationDeploymentDefinition(
            mode=DeploymentMode.incremental,
            name="somename",
            arm_file=pathlib.Path("arm_file.json"),
            puff_file=None,
        )

        result_template, result_puff, result_parameters = _construct_arm_paths(
            mock_step,
            mock_puff_parameter_name,
            mock_app_name,
            mock_frame_folder,
        )

        assert result_template == pathlib.Path("some/path/arm_file.json")
        assert result_puff == pathlib.Path("some/path/arm_file.yml")

    def test_independent_arm_file_puff_file(self):
        mock_app_name = "this_app"
        mock_puff_parameter_name = "some.puff.file.json"
        mock_frame_folder = pathlib.Path("some/path")
        mock_step = ApplicationDeploymentDefinition(
            mode=DeploymentMode.incremental,
            name="somename",
            arm_file=pathlib.Path("arm_file.json"),
            puff_file=pathlib.Path("puff_file.yml"),
        )

        result_template, result_puff, result_parameters = _construct_arm_paths(
            mock_step,
            mock_puff_parameter_name,
            mock_app_name,
            mock_frame_folder,
        )

        assert result_template == pathlib.Path("some/path/arm_file.json")
        assert result_puff == pathlib.Path("some/path/puff_file.yml")
