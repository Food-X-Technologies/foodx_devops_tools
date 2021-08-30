#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.deploy_me._deployment import PipelineCliOptions


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
