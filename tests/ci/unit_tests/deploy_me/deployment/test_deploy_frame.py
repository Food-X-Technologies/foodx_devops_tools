#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio

import pytest

from foodx_devops_tools.deploy_me._deployment import (
    DeploymentState,
    DeploymentStatus,
    PipelineCliOptions,
    deploy_frame,
)
from foodx_devops_tools.deploy_me.exceptions import DeploymentCancelledError
from foodx_devops_tools.pipeline_config import IterationContext

MOCK_ITERATION_CONTEXT = IterationContext()
MOCK_ITERATION_CONTEXT.append("some")
MOCK_ITERATION_CONTEXT.append("context")


@pytest.fixture()
def mock_application_deploy(mock_async_method, prep_frame_data):
    deployment_data, frame_data = prep_frame_data
    mock_application = mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.deploy_application"
    )

    return mock_application, deployment_data, frame_data


@pytest.mark.asyncio
async def test_validation_clean(mocker, mock_application_deploy):
    cli_options = PipelineCliOptions(
        enable_validation=True,
        monitor_sleep_seconds=30,
        wait_timeout_seconds=(15 * 60),
    )

    mock_application, deployment_data, frame_data = mock_application_deploy

    this_status = DeploymentStatus(MOCK_ITERATION_CONTEXT)
    await deploy_frame(
        frame_data,
        deployment_data,
        this_status,
        cli_options,
    )

    mock_application.assert_called_once_with(
        frame_data.applications["a1"],
        mocker.ANY,
        mocker.ANY,
        cli_options.enable_validation,
        frame_data.folder,
    )


@pytest.mark.asyncio
async def test_dependency_failed(mock_application_deploy):
    dependency_frame = "other-frame"

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_ITERATION_CONTEXT)
    await this_status.initialize(dependency_frame)
    await this_status.write(dependency_frame, DeploymentState.ResultType.failed)

    await check_is_cancelled(this_status, frame_data, deployment_data)


async def check_is_cancelled(this_status, frame_data, deployment_data):
    cli_options = PipelineCliOptions(
        enable_validation=True,
        monitor_sleep_seconds=30,
        wait_timeout_seconds=(15 * 60),
    )
    with pytest.raises(
        DeploymentCancelledError, match=r"^cancelled due to dependency failure"
    ):
        await deploy_frame(
            frame_data,
            deployment_data,
            this_status,
            cli_options,
        )


@pytest.mark.asyncio
async def test_dependency_cancelled(mock_application_deploy):
    dependency_frame = "other-frame"

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_ITERATION_CONTEXT)
    await this_status.initialize(dependency_frame)
    await this_status.write(
        dependency_frame, DeploymentState.ResultType.cancelled
    )

    await check_is_cancelled(this_status, frame_data, deployment_data)


@pytest.mark.asyncio
async def test_multiple_dependencies_one_failed(mock_application_deploy):
    dependencies = {
        "df1": DeploymentState.ResultType.success,
        "df2": DeploymentState.ResultType.failed,
    }

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = list(dependencies.keys())

    this_status = DeploymentStatus(MOCK_ITERATION_CONTEXT)
    for this_df in dependencies.keys():
        await this_status.initialize(this_df)
        await this_status.write(this_df, dependencies[this_df])

    await check_is_cancelled(this_status, frame_data, deployment_data)


@pytest.mark.asyncio
async def test_dependencies_success(mock_application_deploy):
    cli_options = PipelineCliOptions(
        enable_validation=True,
        monitor_sleep_seconds=30,
        wait_timeout_seconds=(15 * 60),
    )
    dependency_frame = "other-frame"

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_ITERATION_CONTEXT)
    await this_status.initialize(dependency_frame)
    await this_status.write(
        dependency_frame, DeploymentState.ResultType.success
    )

    await deploy_frame(
        frame_data,
        deployment_data,
        this_status,
        cli_options,
    )


async def delayed_completion(
    name: str,
    status: DeploymentStatus,
    duration_seconds: float,
    final_state: DeploymentState.ResultType,
):
    await status.write(name, DeploymentState.ResultType.in_progress)
    await asyncio.sleep(duration_seconds)
    await status.write(name, final_state)


@pytest.mark.asyncio
async def test_pausing(mock_application_deploy):
    cli_options = PipelineCliOptions(
        enable_validation=True, monitor_sleep_seconds=1, wait_timeout_seconds=2
    )
    dependency_frame = "other-frame"

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_ITERATION_CONTEXT)
    await this_status.initialize(dependency_frame)

    await asyncio.create_task(
        delayed_completion(
            dependency_frame, this_status, 2, DeploymentState.ResultType.success
        )
    )

    await deploy_frame(
        frame_data,
        deployment_data,
        this_status,
        cli_options,
    )


@pytest.mark.asyncio
async def test_in_progress_timeout(mock_application_deploy):
    cli_options = PipelineCliOptions(
        enable_validation=True, monitor_sleep_seconds=2, wait_timeout_seconds=1
    )
    dependency_frame = "other-frame"

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_ITERATION_CONTEXT)
    await this_status.initialize(dependency_frame)

    await asyncio.create_task(
        delayed_completion(
            dependency_frame,
            this_status,
            0.5,
            DeploymentState.ResultType.in_progress,
        )
    )

    with pytest.raises(
        DeploymentCancelledError, match=r"^timeout waiting for dependencies"
    ):
        await deploy_frame(
            frame_data,
            deployment_data,
            this_status,
            cli_options,
        )
