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

from foodx_devops_tools.deploy_me._deployment import (
    DeploymentState,
    _construct_fqdn,
    _construct_resource_group_name,
    assess_results,
)


class TestConstructFqdn:
    def test_structured_subscription(self):
        result = _construct_fqdn(
            "api", "some.where", "client", "system_client_stub"
        )

        assert result == "api.stub.client.some.where"

    def test_unstructured_subscription(self):
        result = _construct_fqdn(
            "api", "some.where", "client", "system_client_stub"
        )

        assert result == "api.stub.client.some.where"


class TestConstructResourceGroupName:
    def test_clean(self):
        result = _construct_resource_group_name("app", "frame", "client")

        assert result == "app-frame-client"


class TestAssessResults:
    def test_success(self):
        mock_results = [
            DeploymentState(code=DeploymentState.ResultType.success),
            DeploymentState(code=DeploymentState.ResultType.success),
        ]

        result = assess_results(mock_results)

        assert result.code == DeploymentState.ResultType.success

    def test_fail(self):
        mock_results = [
            DeploymentState(code=DeploymentState.ResultType.success),
            DeploymentState(code=DeploymentState.ResultType.failed),
        ]

        result = assess_results(mock_results)

        assert result.code == DeploymentState.ResultType.failed
