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

import copy

import pytest

from foodx_devops_tools.pipeline_config.exceptions import PipelineViewError
from foodx_devops_tools.pipeline_config.views import (
    DeploymentTuple,
    DeploymentView,
    IterationContext,
    ReleaseView,
    SubscriptionView,
)
from tests.ci.support.pipeline_config import MOCK_CONTEXT, MOCK_TO


class TestIterationContext:
    def test_clean(self):
        under_test = IterationContext()
        under_test.append("one")
        under_test.append("two")

        assert str(under_test) == "one.two"

    def test_empty(self):
        under_test = IterationContext()

        assert str(under_test) == ""


class TestFlattenedDeployment:
    def test_copy_add_frame(self, mock_flattened_deployment):
        expected_frame = "f1"
        under_test = mock_flattened_deployment[0]

        assert expected_frame not in under_test.data.iteration_context

        result = under_test.copy_add_frame(expected_frame)

        assert id(result) != id(under_test)
        assert expected_frame in result.data.iteration_context
        assert result.context.frame_name == expected_frame

    def test_copy_add_application(self, mock_flattened_deployment):
        expected_name = "a1"
        under_test = mock_flattened_deployment[0]

        assert expected_name not in under_test.data.iteration_context

        result = under_test.copy_add_application(expected_name)

        assert id(result) != id(under_test)
        assert expected_name in result.data.iteration_context
        assert result.context.application_name == expected_name

    def test_construct_app_fqdns(self, mock_flattened_deployment):
        under_test = mock_flattened_deployment[0]

        result = under_test.construct_app_fqdns()

        assert result == {
            "a": "a.r1a.c1.some.where",
            "p": "p.r1a.c1.some.where",
            "root": "some.where",
            "support": "support.c1.some.where",
        }

    def test_construct_app_urls(self, mock_flattened_deployment):
        under_test = mock_flattened_deployment[0]

        result = under_test.construct_app_urls()

        assert result == {
            "a": "https://a.r1a.c1.some.where",
            "p": "https://p.r1a.c1.some.where",
            "support": "https://support.c1.some.where",
        }

    def test_construct_fqdn(self, mock_flattened_deployment):
        under_test = mock_flattened_deployment[0]

        result = under_test.construct_fqdn("api")

        assert result == "api.r1a.c1.some.where"

    def test_construct_template_parameters(self, mock_flattened_deployment):
        under_test = mock_flattened_deployment[0]
        under_test.context.frame_name = "f1"
        under_test.data.template_context = {
            "v1": {"k1": 3.14},
            "v2": "vv2",
        }

        result = under_test.construct_template_parameters("this_name")

        assert result == {
            "context": {
                "environment": {
                    "azure": {
                        "subscription_id": "abc123",
                        "tenant_id": "123abc",
                    },
                    "resource_group": "this_name",
                },
                "v1": {"k1": 3.14},
                "v2": "vv2",
                "locations": {
                    "primary": "l1",
                    "secondary": None,
                },
                "network": {
                    "fqdns": {
                        "a": "a.r1a.c1.some.where",
                        "p": "p.r1a.c1.some.where",
                        "root": "some.where",
                        "support": "support.c1.some.where",
                    },
                    "urls": {
                        "a": "https://a.r1a.c1.some.where",
                        "p": "https://p.r1a.c1.some.where",
                        "support": "https://support.c1.some.where",
                    },
                },
                "tags": {
                    "application_name": None,
                    "client": "c1",
                    "commit_sha": "abc123",
                    "frame_name": "f1",
                    "pipeline_id": "123456",
                    "release_id": "3.1.4+local",
                    "release_state": "r1",
                    "resource_suffix": "r1a",
                    "subscription_name": "sys1_c1_r1a",
                    "system": "sys1",
                    "tenant_name": "t1",
                },
            }
        }

    def test_default_resource_group(self, mock_flattened_deployment):
        under_test = mock_flattened_deployment[0]
        under_test.context.frame_name = "f1"
        under_test.data.template_context = {
            "v1": {"k1": 3.14},
            "v2": "vv2",
        }

        result = under_test.construct_template_parameters()

        assert result["context"]["environment"]["resource_group"] is None


class TestSubscriptionView:
    def test_clean(self, mock_pipeline_config):
        release_view = ReleaseView(mock_pipeline_config(), MOCK_CONTEXT)
        deployment_view = DeploymentView(
            release_view,
            DeploymentTuple(client="c1", release_state="r1", system="sys1"),
        )
        SubscriptionView(
            deployment_view,
            "sys1_c1_r1a",
        )

    def test_deploy_data_clean(self, mock_pipeline_config):
        release_view = ReleaseView(mock_pipeline_config(), MOCK_CONTEXT)
        deployment_view = DeploymentView(
            release_view,
            DeploymentTuple(client="c1", release_state="r1", system="sys1"),
        )
        under_test = SubscriptionView(
            deployment_view,
            "sys1_c1_r1a",
        )

        result = under_test.deploy_data

        assert [x.azure_credentials.userid for x in result] == [
            "12345",
            "12345",
        ]
        assert {x.location_primary for x in result} == {"l1", "l2"}

    def test_bad_subscription_raises(self, mock_pipeline_config):
        release_view = ReleaseView(mock_pipeline_config(), MOCK_CONTEXT)
        deployment_view = DeploymentView(
            release_view,
            DeploymentTuple(client="c1", release_state="r1", system="sys1"),
        )
        with pytest.raises(PipelineViewError, match=r"^Bad subscription"):
            SubscriptionView(
                deployment_view,
                "bad_sub",
            )


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

        result_tuples = {str(x.deployment_tuple) for x in result}
        assert result_tuples == {
            "sys1-c1-r1",
        }

    def test_deployments_empty(self, mock_pipeline_config):
        this_context = copy.deepcopy(MOCK_CONTEXT)
        this_context.release_state = "r2"
        under_test = ReleaseView(mock_pipeline_config(), this_context)

        result = under_test.deployments

        result_tuples = {str(x.deployment_tuple) for x in result}
        assert not result_tuples

    def test_flatten_clean(self, mock_pipeline_config):
        under_test = ReleaseView(mock_pipeline_config(), MOCK_CONTEXT)

        result = under_test.flatten(MOCK_TO)

        assert len(result) == 2
        assert {x.context.client for x in result} == {
            "c1",
        }
        assert {x.context.system for x in result} == {
            "sys1",
        }
        assert {x.data.location_primary for x in result} == {
            "l1",
            "l2",
        }
        assert [x.data.to for x in result] == [
            MOCK_TO,
            MOCK_TO,
        ]
