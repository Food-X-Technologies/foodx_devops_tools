#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy
import pathlib

import pytest

from foodx_devops_tools.deploy_me._deployment import (
    AzureSubscriptionConfiguration,
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

mock_pipeline_config = PipelineConfiguration.parse_obj(MOCK_RESULTS)
MOCK_APPLICATION_DATA = mock_pipeline_config.frames.frames["f1"].applications[
    "a1"
]


@pytest.fixture()
def prep_data(mock_async_method, mock_flattened_deployment):
    app_data = copy.deepcopy(MOCK_APPLICATION_DATA)

    deployment_data = mock_flattened_deployment[0]
    deployment_data.data.iteration_context.append("f1")
    deployment_data.context.frame_name = "f1"
    deployment_data.context.application_name = "a1"
    deployment_data.context.release_state = "r1"
    deployment_data.context.azure_subscription_name = "sub1"
    deployment_data.data.puff_map = PuffMapGeneratedFiles.parse_obj(
        {"puff_map": MOCK_RESULTS["puff_map"]}
    ).puff_map

    mock_validate = mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.validate_resource_group"
    )
    mock_deploy = mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.deploy_resource_group"
    )

    return mock_validate, mock_deploy, deployment_data, app_data


class DeploymentChecks:
    async def check_static_resource_group(
        self, enable_validation: bool, prep_data
    ):
        mock_validate, mock_deploy, deployment_data, app_data = prep_data

        this_status = DeploymentStatus(MOCK_ITERATION_CONTEXT)
        await deploy_application(
            app_data,
            deployment_data,
            this_status,
            enable_validation,
            pathlib.Path("some/path"),
        )

        return mock_validate, mock_deploy

    async def check_auto_resource_group(
        self, enable_validation: bool, prep_data
    ):
        mock_validate, mock_deploy, deployment_data, app_data = prep_data

        updated = copy.deepcopy(app_data)
        updated[0].resource_group = None
        this_status = DeploymentStatus(MOCK_ITERATION_CONTEXT)
        await deploy_application(
            updated,
            deployment_data,
            this_status,
            enable_validation,
            pathlib.Path("some/path"),
        )

        return mock_validate, mock_deploy


class TestValidation(DeploymentChecks):
    @pytest.mark.asyncio
    async def test_static_resource_group(self, prep_data):
        enable_validation = True

        mock_validate, mock_deploy = await self.check_static_resource_group(
            enable_validation, prep_data
        )

        mock_deploy.assert_not_called()
        mock_validate.assert_called_once_with(
            "a1_group-123456",
            pathlib.Path("some/path/a1.json"),
            pathlib.Path("some/path/some/puff_map/path"),
            "l1",
            "Incremental",
            AzureSubscriptionConfiguration(subscription_id="sub1"),
        )

    @pytest.mark.asyncio
    async def test_auto_resource_group(self, prep_data):
        enable_validation = True

        mock_validate, mock_deploy = await self.check_auto_resource_group(
            enable_validation, prep_data
        )

        mock_deploy.assert_not_called()
        mock_validate.assert_called_once_with(
            "a1-f1-c1-123456",
            pathlib.Path("some/path/a1.json"),
            pathlib.Path("some/path/some/puff_map/path"),
            "l1",
            "Incremental",
            AzureSubscriptionConfiguration(subscription_id="sub1"),
        )


class TestDeployment(DeploymentChecks):
    @pytest.mark.asyncio
    async def test_static_resource_group(self, prep_data):
        enable_validation = False

        mock_validate, mock_deploy = await self.check_static_resource_group(
            enable_validation, prep_data
        )

        mock_validate.assert_not_called()
        mock_deploy.assert_called_once_with(
            "a1_group",
            pathlib.Path("some/path/a1.json"),
            pathlib.Path("some/path/some/puff_map/path"),
            "l1",
            "Incremental",
            AzureSubscriptionConfiguration(subscription_id="sub1"),
        )

    @pytest.mark.asyncio
    async def test_auto_resource_group(self, prep_data):
        enable_validation = False

        mock_validate, mock_deploy = await self.check_auto_resource_group(
            enable_validation, prep_data
        )

        mock_validate.assert_not_called()
        mock_deploy.assert_called_once_with(
            "a1-f1-c1",
            pathlib.Path("some/path/a1.json"),
            pathlib.Path("some/path/some/puff_map/path"),
            "l1",
            "Incremental",
            AzureSubscriptionConfiguration(subscription_id="sub1"),
        )
