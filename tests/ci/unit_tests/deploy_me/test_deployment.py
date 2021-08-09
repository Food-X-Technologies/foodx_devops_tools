#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import logging

import pytest

from foodx_devops_tools.deploy_me._deployment import (
    DeploymentError,
    DeploymentState,
    DeploymentStatus,
    FlattenedDeployment,
    assess_results,
    deploy_frame,
    do_deploy,
)


@pytest.fixture()
def status_instance():
    _status_instance = DeploymentStatus()

    return _status_instance


class TestDeploymentStatus:
    @pytest.mark.asyncio
    async def test_clean(self, status_instance):
        this_name = "some_name"
        assert not await status_instance.names()
        await status_instance.initialize(this_name)

        assert await status_instance.names() == {this_name}

        await status_instance.write(
            this_name,
            DeploymentState.ResultType.pending,
            message="some message",
        )

        result = await status_instance.read(this_name)
        assert result.code == DeploymentState.ResultType.pending
        assert result.message == "some message"


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
