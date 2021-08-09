#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.deploy_me._deployment import (
    DeploymentState,
    DeploymentStatus,
    SingularFrameDefinition,
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


class TestDeployFrame:
    MOCK_FRAME_DATA = {
        "f1": SingularFrameDefinition.parse_obj(
            {
                "applications": {
                    "a1": [
                        {
                            "resource_group": "rg1",
                            "mode": "Incremental",
                        }
                    ],
                    "a2": [
                        {
                            "resource_group": "rg2",
                            "mode": "Complete",
                            "arm_file": "something.json",
                        }
                    ],
                },
                "folder": "some/path",
            }
        )
    }

    @pytest.mark.asyncio
    async def test_validation_clean(self, mock_flattened_deployment):
        enable_validation = True

        this_status = DeploymentStatus()
        await deploy_frame(
            self.MOCK_FRAME_DATA.copy(),
            mock_flattened_deployment[0],
            this_status,
            enable_validation,
        )

        # placeholder hard-coded success result
        result_state = await this_status.read("f1")
        assert result_state.code == DeploymentState.ResultType.success

    @pytest.mark.asyncio
    async def test_deployment_clean(self, mock_flattened_deployment):
        enable_validation = False

        this_status = DeploymentStatus()
        await deploy_frame(
            self.MOCK_FRAME_DATA.copy(),
            mock_flattened_deployment[0],
            this_status,
            enable_validation,
        )

        # placeholder hard-coded failed result
        result_state = await this_status.read("f1")
        assert result_state.code == DeploymentState.ResultType.failed


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


class TestDoDeploy:
    @pytest.mark.asyncio
    async def test_validation_clean(
        self, mock_pipeline_config, mock_flattened_deployment
    ):
        enable_validation = True

        result = await do_deploy(
            mock_pipeline_config(),
            mock_flattened_deployment[0],
            enable_validation,
        )

        # placeholder hard-coded success result
        assert result.code == DeploymentState.ResultType.success

    @pytest.mark.asyncio
    async def test_deployment_clean(
        self, mock_pipeline_config, mock_flattened_deployment
    ):
        enable_validation = False

        result = await do_deploy(
            mock_pipeline_config(),
            mock_flattened_deployment[0],
            enable_validation,
        )

        # placeholder hard-coded success result
        assert result.code == DeploymentState.ResultType.failed
