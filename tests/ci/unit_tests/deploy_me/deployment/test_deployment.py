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
    _construct_deployment_paths,
    _construct_resource_group_name,
    assess_results,
    prepare_deployment_files,
)
from foodx_devops_tools.pipeline_config.frames import DeploymentMode


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
    MOCK_CONTEXT = "some_context"

    def test_none_arm_file_puff_file(self):
        mock_app_name = "this_app"
        mock_puff_parameter_name = pathlib.Path("some.puff.file.json")
        mock_frame_folder = pathlib.Path("some/path")
        mock_step = ApplicationDeploymentDefinition(
            mode=DeploymentMode.incremental,
            name="somename",
            arm_file=None,
            puff_file=None,
        )

        (
            result_template,
            result_puff,
            result_parameters,
            result_target,
        ) = _construct_deployment_paths(
            mock_step,
            mock_puff_parameter_name,
            mock_app_name,
            mock_frame_folder,
            self.MOCK_CONTEXT,
        )

        assert result_template == pathlib.Path("some/path/this_app.json")
        assert result_puff == pathlib.Path("some/path/this_app.yml")

    def test_parameter_file(self):
        mock_app_name = "this_app"
        mock_puff_parameter_name = pathlib.Path("some.puff.file.json")
        mock_frame_folder = pathlib.Path("some/path")
        mock_step = ApplicationDeploymentDefinition(
            mode=DeploymentMode.incremental,
            name="somename",
        )

        (
            result_template,
            result_puff,
            result_parameters,
            result_target,
        ) = _construct_deployment_paths(
            mock_step,
            mock_puff_parameter_name,
            mock_app_name,
            mock_frame_folder,
            self.MOCK_CONTEXT,
        )

        assert result_parameters == pathlib.Path(
            "some/path/some.puff.file.json"
        )

    def test_arm_file_none_puff_file(self):
        mock_app_name = "this_app"
        mock_puff_parameter_name = pathlib.Path("some.puff.file.json")
        mock_frame_folder = pathlib.Path("some/path")
        mock_step = ApplicationDeploymentDefinition(
            mode=DeploymentMode.incremental,
            name="somename",
            arm_file=pathlib.Path("arm_file.json"),
            puff_file=None,
        )

        (
            result_template,
            result_puff,
            result_parameters,
            result_target,
        ) = _construct_deployment_paths(
            mock_step,
            mock_puff_parameter_name,
            mock_app_name,
            mock_frame_folder,
            self.MOCK_CONTEXT,
        )

        assert result_template == pathlib.Path("some/path/arm_file.json")
        assert result_puff == pathlib.Path("some/path/arm_file.yml")

    def test_independent_arm_file_puff_file(self):
        mock_app_name = "this_app"
        mock_puff_parameter_name = pathlib.Path("some.puff.file.json")
        mock_frame_folder = pathlib.Path("some/path")
        mock_step = ApplicationDeploymentDefinition(
            mode=DeploymentMode.incremental,
            name="somename",
            arm_file=pathlib.Path("arm_file.json"),
            puff_file=pathlib.Path("puff_file.yml"),
        )

        (
            result_template,
            result_puff,
            result_parameters,
            result_target,
        ) = _construct_deployment_paths(
            mock_step,
            mock_puff_parameter_name,
            mock_app_name,
            mock_frame_folder,
            self.MOCK_CONTEXT,
        )

        assert result_template == pathlib.Path("some/path/arm_file.json")
        assert result_puff == pathlib.Path("some/path/puff_file.yml")


class TestConstructResourceGroupName:
    def test_clean_none_user(self):
        result = _construct_resource_group_name("app", "frame", "client", None)

        assert result == "app-frame-client"

    def test_clean_user_precedence(self):
        result = _construct_resource_group_name(
            "app", "frame", "client", "some_name"
        )

        assert result == "some_name"


class TestPrepareDeploymentFiles:
    MOCK_PARAMETERS = {
        "k1": "v1",
        "k2": "v2",
    }

    @pytest.mark.asyncio
    async def test_clean(self, mock_async_method):
        mock_path = pathlib.Path("some/path")
        mock_puff = mock_async_method(
            "foodx_devops_tools.deploy_me._deployment.run_puff"
        )

        actual_arm, actual_puff = await prepare_deployment_files(
            mock_path, mock_path, mock_path, self.MOCK_PARAMETERS
        )

        assert actual_puff == mock_path
        assert actual_arm == mock_path
        mock_puff.assert_called_once_with(
            mock_path, False, False, disable_ascii_art=True
        )

    @pytest.mark.asyncio
    async def test_jinja2_puff(self, mock_async_method):
        mock_other_paths = pathlib.Path("some/file")
        mock_puff_path = pathlib.Path("some/jinja2.path")
        expected_target = pathlib.Path("some/path")
        mock_puff = mock_async_method(
            "foodx_devops_tools.deploy_me._deployment.run_puff"
        )
        mock_template = mock_async_method(
            "foodx_devops_tools.deploy_me._deployment.FrameTemplates"
            ".apply_template"
        )

        actual_arm, actual_puff = await prepare_deployment_files(
            mock_puff_path,
            mock_other_paths,
            mock_other_paths,
            self.MOCK_PARAMETERS,
        )

        assert actual_puff == expected_target
        assert actual_arm == mock_other_paths
        mock_puff.assert_called_once_with(
            expected_target, False, False, disable_ascii_art=True
        )
        mock_template.assert_called_once_with(
            mock_puff_path.name, expected_target, self.MOCK_PARAMETERS
        )

    @pytest.mark.asyncio
    async def test_jinja2_arm(self, mock_async_method):
        mock_other_paths = pathlib.Path("some/file")
        mock_arm_path = pathlib.Path("some/jinja2.path")
        expected_target = pathlib.Path("some/path")
        mock_puff = mock_async_method(
            "foodx_devops_tools.deploy_me._deployment.run_puff"
        )
        mock_template = mock_async_method(
            "foodx_devops_tools.deploy_me._deployment.FrameTemplates"
            ".apply_template"
        )

        actual_arm, actual_puff = await prepare_deployment_files(
            mock_other_paths,
            mock_arm_path,
            mock_other_paths,
            self.MOCK_PARAMETERS,
        )

        assert actual_arm == expected_target
        assert actual_puff == mock_other_paths
        mock_puff.assert_called_once_with(
            mock_other_paths, False, False, disable_ascii_art=True
        )
        mock_template.assert_called_once_with(
            mock_arm_path.name, expected_target, self.MOCK_PARAMETERS
        )
