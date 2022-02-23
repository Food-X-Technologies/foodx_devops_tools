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
    ApplicationStepDeploymentDefinition,
    ApplicationStepScript,
    FlattenedDeployment,
    PipelineCliOptions,
)
from foodx_devops_tools.patterns import SubscriptionData
from foodx_devops_tools.pipeline_config.frames import DeploymentMode
from foodx_devops_tools.pipeline_config.views import (
    AzureCredentials,
    DeployDataView,
)
from tests.ci.support.pipeline_config import MOCK_CONTEXT


@pytest.fixture()
def mock_login(mock_async_method):
    mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.login_service_principal"
    )


@pytest.fixture()
def mock_rg_deploy(mock_async_method):
    this_mock = mock_async_method(
        "foodx_devops_tools.deploy_me.application_steps._deploy"
        ".deploy_resource_group"
    )
    return this_mock


@pytest.fixture()
def mock_run_puff(mock_async_method):
    this_mock = mock_async_method(
        "foodx_devops_tools.utilities.templates.run_puff"
    )
    return this_mock


@pytest.fixture()
def mock_completion_event(mock_async_method):
    mock_async_method(
        "foodx_devops_tools.deploy_me._deployment"
        ".DeploymentStatus.wait_for_all_completed"
    )


@pytest.fixture()
def pipeline_parameters():
    def _apply(
        enable_validation=True,
        monitor_sleep_seconds=30,
        wait_timeout_seconds=10,
    ):
        cli_options = PipelineCliOptions(
            enable_validation=enable_validation,
            monitor_sleep_seconds=monitor_sleep_seconds,
            wait_timeout_seconds=wait_timeout_seconds,
        )

        return cli_options

    return _apply


@pytest.fixture()
def default_override_parameters():
    def _apply(context):
        subscription_data = SubscriptionData.from_subscription_name(
            context.context.azure_subscription_name
        )
        result = {
            "locations": {
                "primary": context.data.location_primary,
                "secondary": context.data.location_secondary,
            },
            "tags": {
                "application_name": context.context.application_name,
                "client": context.context.client,
                "commit_sha": context.context.commit_sha,
                "frame_name": context.context.frame_name,
                "pipeline_id": context.context.pipeline_id,
                "release_id": context.context.release_id,
                "release_state": context.context.release_state,
                "resource_suffix": subscription_data.resource_suffix,
                "subscription_name": context.context.azure_subscription_name,
                "system": context.context.system,
                "tenant_name": context.context.azure_tenant_name,
            },
        }

        return result

    return _apply


@pytest.fixture()
def mock_base_context():
    mock_context = copy.deepcopy(MOCK_CONTEXT)
    mock_context.application_name = "app-name"
    mock_context.azure_tenant_name = "t1"
    mock_context.azure_subscription_name = "sys1_c1_r1a"
    mock_context.client = "c1"
    mock_context.system = "sys1"
    mock_context.frame_name = "f1"

    data_view = DeployDataView(
        azure_credentials=AzureCredentials(
            userid="abc",
            secret="verysecret",
            subscription="sys1_c1_r1a",
            name="n",
            tenant="123abc",
        ),
        deployment_tuple="a-b-c",
        location_primary="uswest2",
        release_state="r1",
        root_fqdn="some.where",
        static_secrets=dict(),
        subscription_id="s-12345",
        tenant_id="t-abc",
        url_endpoints=["a", "p"],
        user_defined_template_context=dict(),
    )
    data_view.frame_folder = pathlib.Path("frame/folder")

    arguments = {
        "deployment_data": FlattenedDeployment(
            context=mock_context, data=data_view
        ),
        "this_context": "some.context",
    }
    return arguments


@pytest.fixture()
def mock_shellstep_context(mock_base_context):
    arguments = {
        **mock_base_context,
        **{
            "this_step": ApplicationStepScript(
                name="this_step",
                script="""do something
make {{ context.tags.frame_name }}
""",
            ),
        },
    }
    return arguments


@pytest.fixture()
def mock_deploystep_context(mock_base_context):
    arguments = {
        **mock_base_context,
        **{
            "this_step": ApplicationStepDeploymentDefinition(
                mode=DeploymentMode.incremental,
                name="this_step",
                arm_file=pathlib.Path("arm.file"),
                puff_file=pathlib.Path("puff.file"),
                resource_group="rgn",
            ),
            "puff_parameter_data": {
                "this_step": pathlib.Path("puff_generated.path"),
            },
            "enable_validation": False,
        },
    }

    return arguments
