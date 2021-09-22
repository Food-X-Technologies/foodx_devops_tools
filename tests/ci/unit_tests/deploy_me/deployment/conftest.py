#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.deploy_me._deployment import PipelineCliOptions
from foodx_devops_tools.patterns import SubscriptionData


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
