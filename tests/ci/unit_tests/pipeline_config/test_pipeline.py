#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy
import pathlib

import pytest

from foodx_devops_tools.pipeline_config import (
    PipelineConfiguration,
    PipelineConfigurationError,
    PipelineConfigurationPaths,
)
from foodx_devops_tools.pipeline_config.clients import ClientsDefinition
from foodx_devops_tools.pipeline_config.deployments import DeploymentsDefinition
from foodx_devops_tools.pipeline_config.release_states import (
    ReleaseStatesDefinition,
)
from foodx_devops_tools.pipeline_config.subscriptions import (
    SubscriptionsDefinition,
)
from foodx_devops_tools.pipeline_config.systems import SystemsDefinition

MOCK_RESULTS = {
    "clients": ClientsDefinition.parse_obj(
        {
            "clients": {
                "c1": {
                    "release_states": [
                        "r1",
                        "r2",
                    ],
                    "system": "s1",
                },
                "c2": {
                    "depends_on": {"c1": "r1"},
                    "release_states": [
                        "r2",
                    ],
                    "system": "s2",
                },
            },
        }
    ),
    "release_states": ReleaseStatesDefinition.parse_obj(
        {"release_states": ["r1", "r2"]}
    ),
    "deployments": DeploymentsDefinition.parse_obj(
        {
            "deployments": {
                "s1-c1-r1": {
                    "locations": ["l1", "l2"],
                    "ado_service_connection": "some-name",
                },
            }
        }
    ),
    "subscriptions": SubscriptionsDefinition.parse_obj(
        {
            "subscriptions": {
                "subname": {
                    "ado_service_connection": "some-name",
                    "subscription_id": "abc123",
                },
            },
        }
    ),
    "systems": SystemsDefinition.parse_obj({"systems": ["s1", "s2"]}),
}


@pytest.fixture()
def mock_loads(mocker):
    def _apply(mock_data: dict) -> None:
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_clients",
            return_value=mock_data["clients"],
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_release_states",
            return_value=mock_data["release_states"],
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_deployments",
            return_value=mock_data["deployments"],
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_subscriptions",
            return_value=mock_data["subscriptions"],
        )
        mocker.patch(
            "foodx_devops_tools.pipeline_config.pipeline.load_systems",
            return_value=mock_data["systems"],
        )

    return _apply


MOCK_PATHS = PipelineConfigurationPaths(
    clients=pathlib.Path("client/path"),
    release_states=pathlib.Path("release_state/path"),
    deployments=pathlib.Path("deployment/path"),
    subscriptions=pathlib.Path("subscription/path"),
    systems=pathlib.Path("system/path"),
)


class TestPipelineConfiguration:
    def test_default(self, mock_loads):
        mock_loads(MOCK_RESULTS)

        under_test = PipelineConfiguration.from_files(MOCK_PATHS)

        assert len(under_test.clients) == 2
        assert "c1" in under_test.clients
        assert len(under_test.release_states) == 2
        assert under_test.release_states[0] == "r1"
        assert len(under_test.subscriptions) == 1
        assert (
            under_test.subscriptions["subname"].ado_service_connection
            == "some-name"
        )
        assert under_test.subscriptions["subname"].subscription_id == "abc123"
        assert len(under_test.systems) == 2
        assert under_test.systems[0] == "s1"

    def test_bad_deployment_name_raises(self, mock_loads):
        mock_results = copy.deepcopy(MOCK_RESULTS)
        mock_results["deployments"] = DeploymentsDefinition.parse_obj(
            {
                "deployments": {
                    "badname": {
                        "locations": ["l1", "l2"],
                        "ado_service_connection": "some-name",
                    },
                }
            }
        )
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad deployment tuple"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS)

    def test_bad_deployment_clients_raises(self, mock_loads):
        mock_results = copy.deepcopy(MOCK_RESULTS)
        mock_results["clients"] = ClientsDefinition.parse_obj(
            {
                "clients": {
                    "c3": {"release_states": ["r1"], "system": "s1"},
                },
            }
        )
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad client in deployment tuple"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS)

    def test_bad_client_release_states_raises(self, mock_loads):
        mock_results = copy.deepcopy(MOCK_RESULTS)
        mock_results["clients"] = ClientsDefinition.parse_obj(
            {
                "clients": {
                    "c1": {"release_states": ["bad_state"], "system": "s1"},
                },
            }
        )
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad release state in client"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS)

    def test_bad_client_system_raises(self, mock_loads):
        mock_results = copy.deepcopy(MOCK_RESULTS)
        mock_results["clients"] = ClientsDefinition.parse_obj(
            {
                "clients": {
                    "c1": {"release_states": ["r1"], "system": "bad_system"},
                },
            }
        )
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad system in client"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS)

    def test_bad_deployment_release_states_raises(self, mock_loads):
        mock_results = copy.deepcopy(MOCK_RESULTS)
        mock_results["release_states"] = ReleaseStatesDefinition.parse_obj(
            {
                "release_states": ["bad_state"],
            }
        )
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError,
            match=r"Bad release state in deployment tuple",
        ):
            PipelineConfiguration.from_files(MOCK_PATHS)

    def test_bad_deployment_systems_raises(self, mock_loads):
        mock_results = copy.deepcopy(MOCK_RESULTS)
        mock_results["systems"] = SystemsDefinition.parse_obj(
            {
                "systems": ["s3"],
            }
        )
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad system in deployment tuple"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS)
