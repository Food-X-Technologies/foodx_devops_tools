#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import copy
import logging
import typing

import pytest

from foodx_devops_tools.deploy_me._dependency_monitor import (
    DeploymentCancelledError,
    IterationContext,
    PipelineCliOptions,
    _status_wait,
    process_dependencies,
)
from foodx_devops_tools.deploy_me._deployment import (
    DeploymentState,
    DeploymentStatus,
    SingularFrameDefinition,
)

MOCK_ITERATION_CONTEXT = IterationContext()
MOCK_ITERATION_CONTEXT.append("some")
MOCK_ITERATION_CONTEXT.append("context")
MOCK_CONTEXT = str(MOCK_ITERATION_CONTEXT)
MOCK_PIPELINE_PARAMETERS = PipelineCliOptions(
    enable_validation=True, monitor_sleep_seconds=0.5, wait_timeout_seconds=0.1
)


class MockWaiter:
    def __init__(self, sleep_times: typing.List[float]):
        self.sleep_times = sleep_times

    async def __call__(
        self,
        this_context: str,
        frame_data: SingularFrameDefinition,
        frame_status: DeploymentStatus,
        status_monitor_sleep_seconds: int,
    ) -> None:
        for x in self.sleep_times:
            await asyncio.sleep(status_monitor_sleep_seconds)


@pytest.fixture()
async def mock_frame_dependency(prep_frame_data):
    async def _apply():
        deployment_data, frame_data = prep_frame_data
        this_context = copy.deepcopy(MOCK_ITERATION_CONTEXT)
        this_context.append("f1")

        frame_data.depends_on = ["df1"]

        this_status = DeploymentStatus(MOCK_CONTEXT)
        await this_status.initialize(str(this_context))
        for this_df in frame_data.depends_on:
            this_df_context = copy.deepcopy(MOCK_ITERATION_CONTEXT)
            this_df_context.append(this_df)
            await this_status.initialize(str(this_df_context))

        return this_context, this_status, deployment_data, frame_data

    return _apply


class TestStatusWait:
    MOCK_SLEEP = 0.1

    @pytest.mark.asyncio
    async def test_dependencies_clean(
        self, caplog, capsys, mock_frame_dependency
    ):
        with caplog.at_level(logging.INFO):
            (
                this_context,
                this_status,
                deployment_data,
                frame_data,
            ) = await mock_frame_dependency()

            # set the dependency status to "success"
            df_context = copy.deepcopy(MOCK_ITERATION_CONTEXT)
            df_context.append("df1")
            await this_status.write(
                str(df_context), DeploymentState.ResultType.success
            )

            await asyncio.wait_for(
                _status_wait(
                    this_context,
                    frame_data,
                    this_status,
                    self.MOCK_SLEEP,
                ),
                timeout=1,
            )

        expected_messages = [
            {
                "message": "dependencies completed. proceeding with deployment",
                "log_stdout_both": True,
            },
        ]
        self._check_messages(expected_messages, caplog, capsys)

    async def _change_dependency_state(
        self,
        iteration_context: IterationContext,
        frame_status: DeploymentStatus,
        new_state: DeploymentState.ResultType,
    ):
        await asyncio.sleep(0.5)
        await frame_status.write(str(iteration_context), new_state)

    def _check_messages(self, expected_messages, caplog, capsys):
        captured = capsys.readouterr()
        for this_item in expected_messages:
            this_message = this_item["message"]
            in_both = this_item["log_stdout_both"]
            if this_message not in caplog.text:
                pytest.fail(f"not found in logs, {this_message}")
            if in_both and (this_message not in captured.out):
                pytest.fail(f"not found in stdout, {this_message}")

    @pytest.mark.asyncio
    async def test_in_progress_dependency_succeeds(
        self, caplog, capsys, mock_frame_dependency
    ):
        with caplog.at_level(logging.INFO):
            (
                this_context,
                this_status,
                deployment_data,
                frame_data,
            ) = await mock_frame_dependency()

            # set the dependency status to "success"
            df_context = copy.deepcopy(MOCK_ITERATION_CONTEXT)
            df_context.append("df1")

            asyncio.create_task(
                self._change_dependency_state(
                    df_context, this_status, DeploymentState.ResultType.success
                )
            )

            await asyncio.wait_for(
                _status_wait(
                    this_context,
                    frame_data,
                    this_status,
                    self.MOCK_SLEEP,
                ),
                timeout=1,
            )

        expected_messages = [
            {
                "message": "waiting for dependency completion",
                "log_stdout_both": False,
            },
            {
                "message": "dependencies completed. proceeding with deployment",
                "log_stdout_both": True,
            },
        ]
        self._check_messages(expected_messages, caplog, capsys)

    @pytest.mark.asyncio
    async def test_in_progress_dependency_fails(
        self, caplog, capsys, mock_frame_dependency
    ):
        with caplog.at_level(logging.INFO):
            (
                this_context,
                this_status,
                deployment_data,
                frame_data,
            ) = await mock_frame_dependency()

            df_context = copy.deepcopy(MOCK_ITERATION_CONTEXT)
            df_context.append("df1")

            # set the dependency status to "failed"
            asyncio.create_task(
                self._change_dependency_state(
                    df_context, this_status, DeploymentState.ResultType.failed
                )
            )

            with pytest.raises(
                DeploymentCancelledError,
                match=r"cancelled due to dependency failure",
            ):
                await asyncio.wait_for(
                    _status_wait(
                        this_context,
                        frame_data,
                        this_status,
                        self.MOCK_SLEEP,
                    ),
                    timeout=1,
                )

    async def _dependency_late_initialization(
        self,
        iteration_context: IterationContext,
        frame_status: DeploymentStatus,
    ):
        await asyncio.sleep(0.05)
        await frame_status.initialize(str(iteration_context))
        await asyncio.sleep(0.1)
        await frame_status.write(
            str(iteration_context), DeploymentState.ResultType.in_progress
        )
        await asyncio.sleep(0.1)
        await frame_status.write(
            str(iteration_context), DeploymentState.ResultType.success
        )

    @pytest.mark.asyncio
    async def test_missing_dependency_becomes_available(
        self, caplog, capsys, mock_frame_dependency
    ):
        with caplog.at_level(logging.INFO):
            (
                this_context,
                _,
                deployment_data,
                frame_data,
            ) = await mock_frame_dependency()

            df_context = copy.deepcopy(MOCK_ITERATION_CONTEXT)
            df_context.append("df1")

            this_status = DeploymentStatus(MOCK_CONTEXT)
            await this_status.initialize(str(this_context))

            # set the dependency status to "failed"
            asyncio.create_task(
                self._dependency_late_initialization(df_context, this_status)
            )

            await asyncio.wait_for(
                _status_wait(
                    this_context,
                    frame_data,
                    this_status,
                    self.MOCK_SLEEP,
                ),
                timeout=1,
            )

        expected_messages = [
            {
                "message": "dependency frames not in frame status",
                "log_stdout_both": True,
            },
            {
                "message": "dependencies completed. proceeding with deployment",
                "log_stdout_both": True,
            },
        ]
        self._check_messages(expected_messages, caplog, capsys)


class TestProcessDependencies:
    @pytest.mark.asyncio
    async def test_no_dependencies(self, mocker, prep_frame_data):
        deployment_data, frame_data = prep_frame_data

        mocker.patch(
            "foodx_devops_tools.deploy_me._dependency_monitor" "._status_wait",
            side_effect=MockWaiter([0.5]),
        )

        frame_status = DeploymentStatus(MOCK_CONTEXT)

        await process_dependencies(
            MOCK_ITERATION_CONTEXT,
            frame_data,
            frame_status,
            MOCK_PIPELINE_PARAMETERS,
        )

    @pytest.mark.asyncio
    async def test_timeout(self, mocker, prep_frame_data):
        deployment_data, frame_data = prep_frame_data
        this_context = copy.deepcopy(MOCK_ITERATION_CONTEXT)
        this_context.append("f1")

        mocker.patch(
            "foodx_devops_tools.deploy_me._dependency_monitor._status_wait",
            MockWaiter([10]),
        )
        frame_data.depends_on = ["df1"]

        this_status = DeploymentStatus(MOCK_CONTEXT)
        await this_status.initialize(str(this_context))
        for this_df in frame_data.depends_on:
            this_df_context = copy.deepcopy(MOCK_ITERATION_CONTEXT)
            this_df_context.append(this_df)
            await this_status.initialize(str(this_df_context))

        with pytest.raises(
            DeploymentCancelledError, match=r"timeout waiting for dependencies"
        ):
            await process_dependencies(
                this_context,
                frame_data,
                this_status,
                MOCK_PIPELINE_PARAMETERS,
            )
