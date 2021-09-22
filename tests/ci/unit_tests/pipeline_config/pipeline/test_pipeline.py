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
import os

import pytest

from foodx_devops_tools.pipeline_config import (
    ClientsDefinition,
    DeploymentsDefinition,
    PipelineConfiguration,
    PipelineConfigurationPaths,
    ServicePrincipals,
    StaticSecrets,
    SubscriptionsDefinition,
)
from foodx_devops_tools.pipeline_config.exceptions import (
    PipelineConfigurationError,
)
from tests.ci.support.pipeline_config import (
    CLEAN_SPLIT,
    MOCK_PATHS,
    MOCK_RESULTS,
    MOCK_SECRET,
    split_directories,
)

log = logging.getLogger(__name__)


class TestPipelineConfiguration:
    def test_default(self, mock_loads, mock_results):
        mock_loads(mock_results)
        under_test = PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

        assert len(under_test.clients) == 2
        assert "c1" in under_test.clients
        assert len(under_test.release_states) == 2
        assert under_test.release_states[0] == "r1"
        assert len(under_test.subscriptions) == 1
        assert (
            under_test.subscriptions["sys1_c1_r1a"].ado_service_connection
            == "some-name"
        )
        assert under_test.subscriptions["sys1_c1_r1a"].azure_id == "abc123"
        assert len(under_test.systems) == 2
        assert under_test.systems[0] == "sys1"

        assert len(under_test.tenants) == 1
        assert under_test.tenants["t1"].azure_id == "123abc"

    def test_bad_deployment_name_raises(self, mock_loads, mock_results):
        mock_results.deployments = DeploymentsDefinition.parse_obj(
            {
                "deployments": {
                    "badname": {
                        "subscriptions": {
                            "sys1_c1_r1a": {
                                "locations": [
                                    {"primary": "l1"},
                                    {"primary": "l2"},
                                ]
                            },
                        },
                    },
                }
            }
        ).deployments
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad deployment tuple"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

    def test_bad_deployment_clients_raises(self, mock_loads, mock_results):
        mock_results.deployments = DeploymentsDefinition.parse_obj(
            {
                "deployments": {
                    "sys1-bad-r1": {
                        "subscriptions": {
                            "sys1_c1_r1a": {
                                "locations": [
                                    {"primary": "l1"},
                                    {"primary": "l2"},
                                ]
                            }
                        },
                    },
                }
            }
        ).deployments
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad client in deployment tuple"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

    def test_bad_deployment_release_states_raises(
        self, mock_loads, mock_results
    ):
        mock_results.deployments = DeploymentsDefinition.parse_obj(
            {
                "deployments": {
                    "s1-c1-bad": {
                        "subscriptions": {
                            "subname": {
                                "locations": [
                                    {"primary": "l1"},
                                    {"primary": "l2"},
                                ]
                            }
                        },
                    },
                }
            }
        ).deployments
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError,
            match=r"Bad release state in deployment tuple",
        ):
            PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

    def test_bad_deployment_systems_raises(self, mock_loads, mock_results):
        mock_results.deployments = DeploymentsDefinition.parse_obj(
            {
                "deployments": {
                    "bad-c1-r1": {
                        "subscriptions": {
                            "subname": {
                                "locations": [
                                    {"primary": "l1"},
                                    {"primary": "l2"},
                                ]
                            }
                        },
                    },
                }
            }
        ).deployments
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad system in deployment tuple"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

    def test_bad_deployment_subscription_raises(self, mock_loads, mock_results):
        mock_results.deployments = DeploymentsDefinition.parse_obj(
            {
                "deployments": {
                    "sys1-c1-r1": {
                        "subscriptions": {
                            "bad_name": {
                                "locations": [
                                    {"primary": "l1"},
                                    {"primary": "l2"},
                                ]
                            }
                        },
                    },
                }
            }
        ).deployments
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError,
            match=r"Bad subscription in deployment",
        ):
            PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

    def test_bad_client_release_states_raises(self, mock_loads, mock_results):
        mock_results.clients = ClientsDefinition.parse_obj(
            {
                "clients": {
                    "c1": {"release_states": ["bad_state"], "system": "s1"},
                },
            }
        ).clients
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad release state in client"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

    def test_bad_client_system_raises(self, mock_loads, mock_results):
        mock_results.clients = ClientsDefinition.parse_obj(
            {
                "clients": {
                    "c1": {"release_states": ["r1"], "system": "bad_system"},
                },
            }
        ).clients
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad system in client"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

    def test_bad_subscription_tenant_raises(self, mock_loads, mock_results):
        mock_results.subscriptions = SubscriptionsDefinition.parse_obj(
            {
                "subscriptions": {
                    "sys1_c1_r1a": {
                        "ado_service_connection": "some-name",
                        "azure_id": "abc123",
                        "tenant": "bad_name",
                    },
                },
            }
        ).subscriptions
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError, match=r"Bad tenant\(s\) in subscription"
        ):
            PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

    def test_bad_service_principals_subscription_raises(
        self, mock_loads, mock_results
    ):
        mock_results.service_principals = ServicePrincipals.parse_obj(
            {
                "service_principals": {
                    "bad_name": {
                        "id": "12345",
                        "secret": "verysecret",
                        "name": "some_name",
                    },
                },
            }
        ).service_principals
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError,
            match=r"Bad subscription\(s\) in service_principals",
        ):
            PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

    def test_bad_secrets_subscription_raises(self, mock_loads, mock_results):
        mock_results.static_secrets = StaticSecrets.parse_obj(
            {
                "static_secrets": {
                    "bad_name": {
                        "k1": "k1v",
                        "k2": "k2v",
                    },
                },
            }
        ).static_secrets
        mock_loads(mock_results)

        with pytest.raises(
            PipelineConfigurationError,
            match=r"Bad subscription\(s\) in static_secrets",
        ):
            PipelineConfiguration.from_files(MOCK_PATHS, MOCK_SECRET)

    def test_load_files(self):
        with split_directories(CLEAN_SPLIT.copy()) as (
            client_path,
            system_path,
        ):
            client_config = client_path / "configuration"
            system_config = system_path / "configuration"
            this_paths = PipelineConfigurationPaths.from_paths(
                client_config, system_config
            )
            # just expect no exceptions, for now.
            PipelineConfiguration.from_files(this_paths, MOCK_SECRET)

    def test_none_token_clean(self):
        with split_directories(CLEAN_SPLIT.copy()) as (
            client_path,
            system_path,
        ):
            client_config = client_path / "configuration"
            system_config = system_path / "configuration"
            this_paths = PipelineConfigurationPaths.from_paths(
                client_config, system_config
            )
            # just expect no exceptions, for now.
            PipelineConfiguration.from_files(this_paths, None)

    def test_none_token_raises(self):
        """Missing service principals file raises."""
        with split_directories(CLEAN_SPLIT.copy()) as (
            client_path,
            system_path,
        ):
            client_config = client_path / "configuration"
            system_config = system_path / "configuration"
            this_paths = PipelineConfigurationPaths.from_paths(
                client_config, system_config
            )
            # ensure the vault file doesn't exist
            os.remove(client_config / "service_principals.vault")
            with pytest.raises(
                FileNotFoundError,
                match=r"^Missing service principals vault file",
            ):
                PipelineConfiguration.from_files(this_paths, None)

    def test_load_dict(self):
        under_test = PipelineConfiguration.parse_obj(MOCK_RESULTS.copy())
