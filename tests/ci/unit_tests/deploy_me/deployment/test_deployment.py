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

import pytest

from foodx_devops_tools.deploy_me._deployment import (
    DeploymentState,
    _construct_resource_group_name,
    assess_results,
)


class TestAssessResults:
    @pytest.mark.asyncio
    async def test_success(self):
        mock_results = [
            DeploymentState(code=DeploymentState.ResultType.success),
            DeploymentState(code=DeploymentState.ResultType.success),
        ]

        result = await assess_results(mock_results)

        assert result.code == DeploymentState.ResultType.success

    @pytest.mark.asyncio
    async def test_fail(self):
        mock_results = [
            DeploymentState(code=DeploymentState.ResultType.success),
            DeploymentState(code=DeploymentState.ResultType.failed),
        ]

        result = await assess_results(mock_results)

        assert result.code == DeploymentState.ResultType.failed


class TestConstructResourceGroupName:
    def test_clean_user_precedence(self):
        result = _construct_resource_group_name("client", "some_name")

        assert result == "client-some_name"
