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

import logging

import pytest

from foodx_devops_tools.pipeline_config import (
    ClientsDefinition,
    DeploymentsDefinition,
    FramesDefinition,
    PipelineConfiguration,
    PuffMapGeneratedFiles,
    ReleaseStatesDefinition,
    ServicePrincipals,
    StaticSecrets,
    SubscriptionsDefinition,
    SystemsDefinition,
    TenantsDefinition,
)
from tests.ci.support.pipeline_config import MOCK_RESULTS

log = logging.getLogger(__name__)


@pytest.fixture()
def mock_loads(mocker):
    def _apply(mock_data: PipelineConfiguration) -> None:
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_clients",
            return_value=ClientsDefinition.parse_obj(
                {"clients": mock_data.clients}
            ),
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_deployments",
            return_value=DeploymentsDefinition.parse_obj(
                {"deployments": mock_data.deployments}
            ),
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_frames",
            return_value=FramesDefinition.parse_obj(
                {"frames": mock_data.frames}
            ),
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_puff_map",
            return_value=PuffMapGeneratedFiles.parse_obj(
                {"puff_map": mock_data.puff_map}
            ),
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_release_states",
            return_value=ReleaseStatesDefinition.parse_obj(
                {"release_states": mock_data.release_states}
            ),
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_service_principals",
            return_value=ServicePrincipals.parse_obj(
                {"service_principals": mock_data.service_principals}
            ),
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_static_secrets",
            return_value=StaticSecrets.parse_obj(
                {"static_secrets": mock_data.static_secrets}
            ),
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_subscriptions",
            return_value=SubscriptionsDefinition.parse_obj(
                {"subscriptions": mock_data.subscriptions}
            ),
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_systems",
            return_value=SystemsDefinition.parse_obj(
                {"systems": mock_data.systems}
            ),
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_tenants",
            return_value=TenantsDefinition.parse_obj(
                {"tenants": mock_data.tenants}
            ),
        )

    return _apply


@pytest.fixture()
def mock_results():
    results_copy = MOCK_RESULTS.copy()
    pipeline_config = PipelineConfiguration.parse_obj(results_copy)

    return pipeline_config
