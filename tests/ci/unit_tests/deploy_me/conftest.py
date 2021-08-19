#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy

import pytest

from foodx_devops_tools.pipeline_config import PipelineConfiguration
from tests.ci.support.pipeline_config import MOCK_RESULTS


@pytest.fixture()
def prep_frame_data(mock_flattened_deployment):
    pipeline_config = PipelineConfiguration.parse_obj(MOCK_RESULTS)
    frame_data = copy.deepcopy(pipeline_config.frames.frames["f1"])

    deployment_data = mock_flattened_deployment[0]
    deployment_data.data.iteration_context.append("f1")
    deployment_data.context.frame_name = "f1"
    deployment_data.context.release_state = "r1"
    deployment_data.context.azure_subscription_name = "sub1"
    deployment_data.data.puff_map = pipeline_config.puff_map

    return deployment_data, frame_data
