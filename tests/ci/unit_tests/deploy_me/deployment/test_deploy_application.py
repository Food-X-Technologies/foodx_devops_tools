#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy
import pathlib

import pytest

from foodx_devops_tools._to import StructuredTo
from foodx_devops_tools.deploy_me._deployment import (
    AzureSubscriptionConfiguration,
    DeploymentState,
    DeploymentStatus,
    deploy_application,
)
from foodx_devops_tools.pipeline_config import (
    IterationContext,
    PipelineConfiguration,
)
from foodx_devops_tools.pipeline_config.puff_map import PuffMapGeneratedFiles
from tests.ci.support.pipeline_config import MOCK_RESULTS

MOCK_ITERATION_CONTEXT = IterationContext()
MOCK_ITERATION_CONTEXT.append("some")
MOCK_ITERATION_CONTEXT.append("context")

MOCK_CONTEXT = str(MOCK_ITERATION_CONTEXT)

mock_pipeline_config = PipelineConfiguration.parse_obj(MOCK_RESULTS)
MOCK_APPLICATION_DATA = mock_pipeline_config.frames.frames["f1"].applications[
    "a1"
]


@pytest.fixture()
def prep_data(mock_async_method, mock_flattened_deployment):
    app_data = copy.deepcopy(MOCK_APPLICATION_DATA)

    deployment_data = mock_flattened_deployment[0]
    deployment_data.data.iteration_context.append("a1")
    deployment_data.context.frame_name = "f1"
    deployment_data.context.application_name = "a1"
    deployment_data.context.release_state = "r1"
    deployment_data.context.azure_subscription_name = "sys1_c1_r1a"
    deployment_data.data.puff_map = PuffMapGeneratedFiles.parse_obj(
        {"puff_map": MOCK_RESULTS["puff_map"]}
    ).puff_map

    mock_deploy = mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.deploy_resource_group"
    )
    mock_puff = mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.run_puff"
    )
    mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.do_snippet_substitution"
    )
    mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.login_service_principal"
    )

    return mock_deploy, mock_puff, deployment_data, app_data


class DeploymentChecks:
    async def check_static_resource_group(
        self, enable_validation: bool, prep_data
    ):
        mock_deploy, mock_puff, deployment_data, app_data = prep_data

        this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=0.1)
        application_deployment_data = copy.deepcopy(deployment_data)
        application_deployment_data.data.frame_folder = pathlib.Path(
            "some/path"
        )
        await deploy_application(
            app_data,
            application_deployment_data,
            this_status,
            enable_validation,
        )

        mock_puff.assert_called_once()

        return mock_deploy

    async def check_auto_resource_group(
        self, enable_validation: bool, prep_data
    ):
        mock_deploy, mock_puff, deployment_data, app_data = prep_data

        updated = copy.deepcopy(app_data)
        updated[0].resource_group = None
        this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
        application_deployment_data = copy.deepcopy(deployment_data)
        application_deployment_data.data.frame_folder = pathlib.Path(
            "some/path"
        )
        await deploy_application(
            updated,
            application_deployment_data,
            this_status,
            enable_validation,
        )

        mock_puff.assert_called_once()

        return mock_deploy


class TestValidation(DeploymentChecks):
    @pytest.mark.asyncio
    async def test_static_resource_group(
        self, default_override_parameters, prep_data
    ):
        enable_validation = True

        mock_deploy = await self.check_static_resource_group(
            enable_validation, prep_data
        )

        expected_parameters = default_override_parameters(prep_data[2])
        mock_deploy.assert_called_once_with(
            "a1_group-123456",
            pathlib.Path("some/path/a1.json.escolar"),
            pathlib.Path("some/path/some/puff_map/path"),
            "l1",
            "Incremental",
            AzureSubscriptionConfiguration(subscription_id="sys1_c1_r1a"),
            deployment_name="a1_a1l1_123456",
            override_parameters=expected_parameters,
            validate=True,
        )

    @pytest.mark.asyncio
    async def test_auto_resource_group(
        self, default_override_parameters, prep_data
    ):
        enable_validation = True

        mock_deploy = await self.check_auto_resource_group(
            enable_validation, prep_data
        )

        expected_parameters = default_override_parameters(prep_data[2])
        mock_deploy.assert_called_once_with(
            "a1-f1-c1-123456",
            pathlib.Path("some/path/a1.json.escolar"),
            pathlib.Path("some/path/some/puff_map/path"),
            "l1",
            "Incremental",
            AzureSubscriptionConfiguration(subscription_id="sys1_c1_r1a"),
            deployment_name="a1_a1l1_123456",
            override_parameters=expected_parameters,
            validate=True,
        )


class TestDeployment(DeploymentChecks):
    @pytest.mark.asyncio
    async def test_static_resource_group(
        self, default_override_parameters, prep_data
    ):
        enable_validation = False

        mock_deploy = await self.check_static_resource_group(
            enable_validation, prep_data
        )

        expected_parameters = default_override_parameters(prep_data[2])
        mock_deploy.assert_called_once_with(
            "a1_group",
            pathlib.Path("some/path/a1.json.escolar"),
            pathlib.Path("some/path/some/puff_map/path"),
            "l1",
            "Incremental",
            AzureSubscriptionConfiguration(subscription_id="sys1_c1_r1a"),
            deployment_name="a1_a1l1_123456",
            override_parameters=expected_parameters,
            validate=False,
        )

    @pytest.mark.asyncio
    async def test_auto_resource_group(
        self, default_override_parameters, prep_data
    ):
        enable_validation = False

        mock_deploy = await self.check_auto_resource_group(
            enable_validation, prep_data
        )

        expected_parameters = default_override_parameters(prep_data[2])
        mock_deploy.assert_called_once_with(
            "a1-f1-c1",
            pathlib.Path("some/path/a1.json.escolar"),
            pathlib.Path("some/path/some/puff_map/path"),
            "l1",
            "Incremental",
            AzureSubscriptionConfiguration(subscription_id="sys1_c1_r1a"),
            deployment_name="a1_a1l1_123456",
            override_parameters=expected_parameters,
            validate=False,
        )

    @pytest.mark.asyncio
    async def test_application_skip(self, prep_data):
        enable_validation = False
        mock_deploy, mock_puff, deployment_data, app_data = prep_data

        updated = copy.deepcopy(app_data)
        updated[0].resource_group = None
        this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=0.1)
        application_deployment_data = copy.deepcopy(deployment_data)
        application_deployment_data.data.frame_folder = pathlib.Path(
            "some/path"
        )
        application_deployment_data.data.to = StructuredTo(
            frame="f1", application="a2"
        )

        await deploy_application(
            updated,
            application_deployment_data,
            this_status,
            enable_validation,
        )

        status = await this_status.read("a1")
        assert status.code == DeploymentState.ResultType.skipped
