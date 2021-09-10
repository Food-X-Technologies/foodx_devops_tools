#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.deploy_me._deployment import do_deploy
from foodx_devops_tools.pipeline_config import PipelineConfiguration
from tests.ci.support.pipeline_config import MOCK_RESULTS


@pytest.fixture()
def prep_data(mock_async_method, mock_flattened_deployment):
    pipeline_config = PipelineConfiguration.parse_obj(MOCK_RESULTS)

    deployment_data = mock_flattened_deployment[0]
    deployment_data.data.iteration_context.append("f1")
    deployment_data.context.frame_name = "f1"
    deployment_data.context.release_state = "r1"
    deployment_data.context.azure_subscription_name = "sub1"
    deployment_data.data.puff_map = pipeline_config.puff_map

    mock_frame = mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.deploy_frame"
    )
    mock_async_method("foodx_devops_tools.deploy_me._deployment.run_puff")

    return mock_frame, deployment_data, pipeline_config


class TestDoDeploy:
    @pytest.mark.asyncio
    async def test_validation_clean(
        self, mocker, prep_data, mock_completion_event, pipeline_parameters
    ):
        cli_options = pipeline_parameters()
        mock_frame, deployment_data, pipeline_config = prep_data

        await do_deploy(
            pipeline_config,
            deployment_data,
            cli_options,
        )

        mock_frame.assert_called_once_with(
            pipeline_config.frames.frames["f1"],
            mocker.ANY,
            mocker.ANY,
            cli_options,
        )
