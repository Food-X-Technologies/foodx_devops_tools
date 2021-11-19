#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy

import pytest

from foodx_devops_tools.pipeline_config.exceptions import PipelineViewError
from foodx_devops_tools.pipeline_config.views import (
    DeploymentContext,
    DeploymentTuple,
    DeploymentView,
    ReleaseView,
)
from tests.ci.support.pipeline_config import MOCK_CONTEXT, MOCK_RESULTS


@pytest.fixture()
def mock_context() -> DeploymentContext:
    this_context = copy.deepcopy(MOCK_CONTEXT)
    this_context.release_state = "r2"

    return this_context


@pytest.fixture()
def this_deployment_view(mock_pipeline_config):
    def _apply(mock_results: dict, this_context: DeploymentContext):
        expected_state = DeploymentTuple(
            client="c1", release_state="r1", system="sys1"
        )
        release_view = ReleaseView(
            mock_pipeline_config(mock_results), this_context
        )
        under_test = DeploymentView(release_view, expected_state)

        return under_test

    return _apply


class TestDeploymentView:
    def test_clean(self, mock_context, mock_pipeline_config):
        expected_state = DeploymentTuple(
            client="c1", release_state="r1", system="sys1"
        )
        release_view = ReleaseView(mock_pipeline_config(), mock_context)
        under_test = DeploymentView(release_view, expected_state)

        assert under_test.release_view == release_view
        assert under_test.deployment_tuple == expected_state

    def test_bad_deployment_state_raises(
        self, mock_context, mock_pipeline_config
    ):
        release_view = ReleaseView(mock_pipeline_config(), mock_context)
        with pytest.raises(PipelineViewError, match=r"^Bad client"):
            DeploymentView(
                release_view,
                DeploymentTuple(
                    client="bad_client", release_state="r2", system="sys2"
                ),
            )
        with pytest.raises(PipelineViewError, match=r"^Bad release state"):
            DeploymentView(
                release_view,
                DeploymentTuple(
                    client="c1", release_state="bad_release", system="sys2"
                ),
            )
        with pytest.raises(PipelineViewError, match=r"^Bad system"):
            DeploymentView(
                release_view,
                DeploymentTuple(
                    client="c1", release_state="r2", system="bad_system"
                ),
            )

    def test_subscriptions_clean(self, mock_context, mock_pipeline_config):
        expected_state = DeploymentTuple(
            client="c1", release_state="r1", system="sys1"
        )
        release_view = ReleaseView(mock_pipeline_config(), mock_context)
        under_test = DeploymentView(release_view, expected_state)

        assert under_test.release_view == release_view
        assert under_test.deployment_tuple == expected_state

        assert under_test.subscriptions

    def test_subscriptions_empty(self, mock_context, mock_pipeline_config):
        this_context = copy.deepcopy(MOCK_CONTEXT)
        this_context.release_state = "r2"
        release_view = ReleaseView(mock_pipeline_config(), this_context)
        under_test = DeploymentView(
            release_view,
            DeploymentTuple(client="c2", release_state="r2", system="sys2"),
        )

        assert not under_test.subscriptions


@pytest.fixture()
def deployment_view_config():
    mock_results = copy.deepcopy(MOCK_RESULTS)
    mock_results["puff_map"] = {
        "frames": {
            "f1": {
                "applications": {
                    "a1": {
                        "arm_parameters_files": {
                            "r1": {
                                "sys1_c1_r1a": {
                                    "a1l1": "some/puff_map/path",
                                },
                                "sys1_c1_r1b": {
                                    "a1l1": "some/puff_map/path",
                                },
                                "sys1_c1_r1c": {
                                    "a1l1": "some/puff_map/path",
                                },
                            },
                        },
                    },
                },
            },
        },
    }
    mock_results["subscriptions"] = {
        "sys1_c1_r1a": {
            "ado_service_connection": "some-name",
            "azure_id": "abc123",
            "tenant": "t1",
        },
        "sys1_c1_r1b": {
            "ado_service_connection": "some-name",
            "azure_id": "abc123",
            "tenant": "t1",
        },
        "sys1_c1_r1c": {
            "ado_service_connection": "some-name",
            "azure_id": "abc123",
            "tenant": "t1",
        },
    }
    mock_results["service_principals"] = {
        "sys1_c1_r1a": {
            "id": "12345",
            "secret": "verysecret",
            "name": "sp_name",
        },
        "sys1_c1_r1b": {
            "id": "12345",
            "secret": "verysecret",
            "name": "sp_name",
        },
        "sys1_c1_r1c": {
            "id": "12345",
            "secret": "verysecret",
            "name": "sp_name",
        },
    }
    mock_results["static_secrets"] = {
        "sys1_c1_r1a": {"k1": "k1v1"},
        "sys1_c1_r1b": {"k1": "k1v2"},
        "sys1_c1_r1c": {"k1": "k1v2"},
    }

    return mock_results


class TestSubscriptionConstraints:
    def test_no_constraint(
        self, mock_context, deployment_view_config, this_deployment_view
    ):
        deployment_view_config["deployments"] = {
            "deployment_tuples": {
                "sys1-c1-r1": {
                    "subscriptions": {
                        "sys1_c1_r1a": {
                            "locations": [{"primary": "l1"}, {"primary": "l2"}],
                            "root_fqdn": "this.sub",
                        },
                        "sys1_c1_r1b": {
                            "locations": [{"primary": "l1"}, {"primary": "l2"}],
                            "root_fqdn": "other.sub",
                        },
                    },
                },
            },
            "url_endpoints": ["a", "p"],
        }
        under_test = this_deployment_view(deployment_view_config, mock_context)
        this_subscriptions = under_test.subscriptions

        assert len(under_test.subscriptions) == 2
        expected_names = {"sys1_c1_r1a", "sys1_c1_r1b"}
        assert {
            this_subscriptions[x].subscription_name
            for x in range(len(this_subscriptions))
        } == expected_names

    def test_plain_text(
        self, mock_context, deployment_view_config, this_deployment_view
    ):
        mock_context.git_ref = "b1"
        deployment_view_config["deployments"] = {
            "deployment_tuples": {
                "sys1-c1-r1": {
                    "subscriptions": {
                        "sys1_c1_r1a": {
                            "gitref_patterns": ["b1"],
                            "locations": [{"primary": "l1"}, {"primary": "l2"}],
                            "root_fqdn": "some.where",
                        },
                        "sys1_c1_r1b": {
                            "gitref_patterns": ["b2"],
                            "locations": [{"primary": "l1"}, {"primary": "l2"}],
                            "root_fqdn": "some.where",
                        },
                    },
                },
            },
            "url_endpoints": ["a", "p"],
        }
        under_test = this_deployment_view(deployment_view_config, mock_context)
        this_subscriptions = under_test.subscriptions

        assert len(under_test.subscriptions) == 1
        expected_names = {"sys1_c1_r1a"}
        assert {
            this_subscriptions[x].subscription_name
            for x in range(len(this_subscriptions))
        } == expected_names

    def test_regex(
        self, mock_context, deployment_view_config, this_deployment_view
    ):
        mock_context.git_ref = "b3/some/branch"
        deployment_view_config["deployments"] = {
            "deployment_tuples": {
                "sys1-c1-r1": {
                    "subscriptions": {
                        "sys1_c1_r1a": {
                            "gitref_patterns": ["^b[2-4]/.*"],
                            "locations": [{"primary": "l1"}, {"primary": "l2"}],
                            "root_fqdn": "some.where",
                        },
                        "sys1_c1_r1b": {
                            "gitref_patterns": ["b2"],
                            "locations": [{"primary": "l1"}, {"primary": "l2"}],
                            "root_fqdn": "some.where",
                        },
                    },
                },
            },
            "url_endpoints": ["a", "p"],
        }
        under_test = this_deployment_view(deployment_view_config, mock_context)
        this_subscriptions = under_test.subscriptions

        assert len(under_test.subscriptions) == 1
        expected_names = {"sys1_c1_r1a"}
        assert {
            this_subscriptions[x].subscription_name
            for x in range(len(this_subscriptions))
        } == expected_names

    def test_multiple(
        self, mock_context, deployment_view_config, this_deployment_view
    ):
        mock_context.git_ref = "c"
        deployment_view_config["deployments"] = {
            "deployment_tuples": {
                "sys1-c1-r1": {
                    "subscriptions": {
                        "sys1_c1_r1a": {
                            "gitref_patterns": ["^b[2-4]/.*", "c"],
                            "locations": [{"primary": "l1"}, {"primary": "l2"}],
                            "root_fqdn": "some.where",
                        },
                        "sys1_c1_r1b": {
                            "gitref_patterns": ["c"],
                            "locations": [{"primary": "l1"}, {"primary": "l2"}],
                            "root_fqdn": "some.where",
                        },
                        "sys1_c1_r1c": {
                            # this subscription should be excluded
                            "gitref_patterns": ["d"],
                            "locations": [{"primary": "l1"}, {"primary": "l2"}],
                            "root_fqdn": "some.where",
                        },
                    },
                },
            },
            "url_endpoints": ["a", "p"],
        }
        under_test = this_deployment_view(deployment_view_config, mock_context)
        this_subscriptions = under_test.subscriptions

        assert len(under_test.subscriptions) == 2
        expected_names = {"sys1_c1_r1a", "sys1_c1_r1b"}
        assert {
            this_subscriptions[x].subscription_name
            for x in range(len(this_subscriptions))
        } == expected_names
