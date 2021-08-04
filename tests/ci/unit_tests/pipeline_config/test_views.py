#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import copy

import pytest

from foodx_devops_tools.pipeline_config import PipelineConfiguration
from foodx_devops_tools.pipeline_config.views import (
    DeploymentContext,
    DeploymentState,
    DeploymentView,
    PipelineViewError,
    ReleaseView,
    SubscriptionView,
)
from tests.ci.support.pipeline_config import MOCK_RESULTS


@pytest.fixture
def mock_pipeline_config():
    def _apply(mock_data=MOCK_RESULTS.copy()) -> PipelineConfiguration:
        return PipelineConfiguration.parse_obj(mock_data)

    return _apply


MOCK_CONTEXT = DeploymentContext(
    commit_sha="abc123",
    pipeline_id="12345",
    release_id="0.0.0-dev.3",
    release_state="r1",
)


class TestSubscriptionView:
    def test_clean(self, mock_pipeline_config):
        release_view = ReleaseView(mock_pipeline_config(), MOCK_CONTEXT)
        deployment_view = DeploymentView(
            release_view,
            DeploymentState(client="c1", release_state="r1", system="sys1"),
        )
        under_test = SubscriptionView(
            deployment_view,
            "sub1",
        )

    def test_deploy_data_clean(self, mock_pipeline_config):
        release_view = ReleaseView(mock_pipeline_config(), MOCK_CONTEXT)
        deployment_view = DeploymentView(
            release_view,
            DeploymentState(client="c1", release_state="r1", system="sys1"),
        )
        under_test = SubscriptionView(
            deployment_view,
            "sub1",
        )

        result = under_test.deploy_data

        assert [x.ado_service_connection for x in result] == [
            "some-name",
            "some-name",
        ]
        assert {x.location_primary for x in result} == {"l1", "l2"}

    def test_bad_subscription_raises(self, mock_pipeline_config):
        release_view = ReleaseView(mock_pipeline_config(), MOCK_CONTEXT)
        deployment_view = DeploymentView(
            release_view,
            DeploymentState(client="c1", release_state="r1", system="sys1"),
        )
        with pytest.raises(PipelineViewError, match=r"^Bad subscription"):
            SubscriptionView(
                deployment_view,
                "bad_sub",
            )


class TestDeploymentView:
    def test_clean(self, mock_pipeline_config):
        expected_state = DeploymentState(
            client="c1", release_state="r2", system="sys1"
        )
        this_context = copy.deepcopy(MOCK_CONTEXT)
        this_context.release_state = "r2"
        release_view = ReleaseView(mock_pipeline_config(), this_context)
        under_test = DeploymentView(release_view, expected_state)

        assert under_test.release_view == release_view
        assert under_test.deployment_state == expected_state

    def test_bad_deployment_state_raises(self, mock_pipeline_config):
        this_context = copy.deepcopy(MOCK_CONTEXT)
        this_context.release_state = "r2"
        release_view = ReleaseView(mock_pipeline_config(), this_context)
        with pytest.raises(PipelineViewError, match=r"^Bad client"):
            DeploymentView(
                release_view,
                DeploymentState(
                    client="bad_client", release_state="r2", system="sys2"
                ),
            )
        with pytest.raises(PipelineViewError, match=r"^Bad release state"):
            DeploymentView(
                release_view,
                DeploymentState(
                    client="c1", release_state="bad_release", system="sys2"
                ),
            )
        with pytest.raises(PipelineViewError, match=r"^Bad system"):
            DeploymentView(
                release_view,
                DeploymentState(
                    client="c1", release_state="r2", system="bad_system"
                ),
            )

    def test_subscriptions_clean(self, mock_pipeline_config):
        expected_state = DeploymentState(
            client="c1", release_state="r1", system="sys1"
        )
        this_context = copy.deepcopy(MOCK_CONTEXT)
        this_context.release_state = "r2"
        release_view = ReleaseView(mock_pipeline_config(), this_context)
        under_test = DeploymentView(release_view, expected_state)

        assert under_test.release_view == release_view
        assert under_test.deployment_state == expected_state

        assert under_test.subscriptions

    def test_subscriptions_empty(self, mock_pipeline_config):
        this_context = copy.deepcopy(MOCK_CONTEXT)
        this_context.release_state = "r2"
        release_view = ReleaseView(mock_pipeline_config(), this_context)
        under_test = DeploymentView(
            release_view,
            DeploymentState(client="c2", release_state="r2", system="sys2"),
        )

        assert not under_test.subscriptions


class TestReleaseView:
    def test_clean(self, mock_pipeline_config):
        this_context = copy.deepcopy(MOCK_CONTEXT)
        this_context.release_state = "r2"
        under_test = ReleaseView(mock_pipeline_config(), this_context)

        assert under_test.configuration == mock_pipeline_config()
        assert under_test.deployment_context.release_state == "r2"

    def test_bad_release_state_raises(self, mock_pipeline_config):
        this_context = copy.deepcopy(MOCK_CONTEXT)
        this_context.release_state = "r3"
        with pytest.raises(PipelineViewError, match=r"^Bad release state"):
            ReleaseView(mock_pipeline_config(), this_context)

    def test_deployments_clean(self, mock_pipeline_config):
        under_test = ReleaseView(mock_pipeline_config(), MOCK_CONTEXT)

        result = under_test.deployments

        result_tuples = {str(x.deployment_state) for x in result}
        assert result_tuples == {
            "sys1-c1-r1",
        }

    def test_deployments_empty(self, mock_pipeline_config):
        this_context = copy.deepcopy(MOCK_CONTEXT)
        this_context.release_state = "r2"
        under_test = ReleaseView(mock_pipeline_config(), this_context)

        result = under_test.deployments

        result_tuples = {str(x.deployment_state) for x in result}
        assert not result_tuples

    def test_flatten_clean(self, mock_pipeline_config):
        under_test = ReleaseView(mock_pipeline_config(), MOCK_CONTEXT)

        result = under_test.flatten()

        assert len(result) == 2
        assert {x["context"].client for x in result} == {
            "c1",
        }
        assert {x["context"].system for x in result} == {
            "sys1",
        }
        assert {x["data"].location_primary for x in result} == {
            "l1",
            "l2",
        }
