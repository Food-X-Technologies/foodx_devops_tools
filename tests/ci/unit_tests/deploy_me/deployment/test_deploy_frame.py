#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio

import pytest

from foodx_devops_tools._to import StructuredTo
from foodx_devops_tools.deploy_me._deployment import (
    ApplicationDeploymentSteps,
    DeploymentState,
    DeploymentStatus,
    FlattenedDeployment,
    deploy_frame,
)
from foodx_devops_tools.deploy_me.exceptions import DeploymentTerminatedError
from foodx_devops_tools.pipeline_config import IterationContext

MOCK_ITERATION_CONTEXT = IterationContext()
MOCK_ITERATION_CONTEXT.append("some")
MOCK_ITERATION_CONTEXT.append("context")
MOCK_CONTEXT = str(MOCK_ITERATION_CONTEXT)


@pytest.fixture()
def mock_application_deploy(mock_async_method, prep_frame_data):
    deployment_data, frame_data = prep_frame_data
    mock_application = mock_async_method(
        "foodx_devops_tools.deploy_me._deployment.deploy_application"
    )

    return mock_application, deployment_data, frame_data


class MockAppDeploy:
    def __init__(self, status):
        self.status = status

    async def __call__(
        self,
        application_data: ApplicationDeploymentSteps,
        deployment_data: FlattenedDeployment,
        application_status: DeploymentStatus,
        enable_validation: bool,
    ) -> None:
        this_context = str(deployment_data.data.iteration_context)
        await application_status.initialize(this_context)
        await application_status.write(this_context, self.status)


@pytest.mark.asyncio
async def test_clean(
    mocker, mock_completion_event, pipeline_parameters, prep_frame_data
):
    cli_options = pipeline_parameters()
    deployment_data, frame_data = prep_frame_data
    mock_app_deploy = MockAppDeploy(DeploymentState.ResultType.success)

    mocker.patch(
        "foodx_devops_tools.deploy_me._deployment.deploy_application" "",
        mock_app_deploy,
    )

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
    await deploy_frame(
        frame_data,
        deployment_data,
        this_status,
        cli_options,
    )

    result = await this_status.read("f1")
    assert result.code == DeploymentState.ResultType.success


@pytest.mark.asyncio
async def test_app_failed(
    mocker, mock_completion_event, pipeline_parameters, prep_frame_data
):
    cli_options = pipeline_parameters()
    deployment_data, frame_data = prep_frame_data
    mock_app_deploy = MockAppDeploy(DeploymentState.ResultType.failed)

    mocker.patch(
        "foodx_devops_tools.deploy_me._deployment.deploy_application" "",
        mock_app_deploy,
    )

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
    await deploy_frame(
        frame_data,
        deployment_data,
        this_status,
        cli_options,
    )

    result = await this_status.read("f1")
    assert result.code == DeploymentState.ResultType.failed


@pytest.mark.asyncio
async def test_app_cancelled(
    mocker, mock_completion_event, pipeline_parameters, prep_frame_data
):
    cli_options = pipeline_parameters()
    deployment_data, frame_data = prep_frame_data
    mock_app_deploy = MockAppDeploy(DeploymentState.ResultType.cancelled)

    mocker.patch(
        "foodx_devops_tools.deploy_me._deployment.deploy_application" "",
        mock_app_deploy,
    )

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
    await deploy_frame(
        frame_data,
        deployment_data,
        this_status,
        cli_options,
    )

    result = await this_status.read("f1")
    assert result.code == DeploymentState.ResultType.cancelled


@pytest.mark.asyncio
async def test_correct_results(
    mocker, mock_completion_event, pipeline_parameters, prep_frame_data
):
    """Test that a frame is correctly reporting the results of it's
    applications (and not the results of other frames)."""
    cli_options = pipeline_parameters()
    deployment_data, frame_data = prep_frame_data
    mock_app_deploy = MockAppDeploy(DeploymentState.ResultType.success)

    mocker.patch(
        "foodx_devops_tools.deploy_me._deployment.deploy_application" "",
        mock_app_deploy,
    )

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)

    # ensure that another frame has failed to avoid masking a false positive
    # in frame status reporting if it is accidentally reporting
    await this_status.initialize("other-f")
    await this_status.write("other-f", DeploymentState.ResultType.failed)

    await deploy_frame(
        frame_data,
        deployment_data,
        this_status,
        cli_options,
    )

    result = await this_status.read("f1")
    assert result.code == DeploymentState.ResultType.success


@pytest.mark.asyncio
async def test_dependency_failed(
    mock_application_deploy, mock_completion_event, pipeline_parameters
):
    cli_options = pipeline_parameters
    dependency_frame = "other-frame"

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
    await this_status.initialize(dependency_frame)
    await this_status.write(dependency_frame, DeploymentState.ResultType.failed)

    await check_is_cancelled(
        this_status, frame_data, deployment_data, cli_options
    )


async def check_is_cancelled(
    this_status, frame_data, deployment_data, pipeline_parameters
):
    cli_options = pipeline_parameters()
    with pytest.raises(
        DeploymentTerminatedError, match=r"^cancelled due to dependency failure"
    ):
        await deploy_frame(
            frame_data,
            deployment_data,
            this_status,
            cli_options,
        )


@pytest.mark.asyncio
async def test_dependency_cancelled(
    mock_application_deploy, mock_completion_event, pipeline_parameters
):
    cli_options = pipeline_parameters
    dependency_frame = "other-frame"

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
    await this_status.initialize(dependency_frame)
    await this_status.write(
        dependency_frame, DeploymentState.ResultType.cancelled
    )

    await check_is_cancelled(
        this_status, frame_data, deployment_data, cli_options
    )


@pytest.mark.asyncio
async def test_multiple_dependencies_one_failed(
    mock_application_deploy, mock_completion_event, pipeline_parameters
):
    cli_options = pipeline_parameters
    dependencies = {
        "df1": DeploymentState.ResultType.success,
        "df2": DeploymentState.ResultType.failed,
    }

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = list(dependencies.keys())

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
    for this_df in dependencies.keys():
        await this_status.initialize(this_df)
        await this_status.write(this_df, dependencies[this_df])

    await check_is_cancelled(
        this_status, frame_data, deployment_data, cli_options
    )


@pytest.mark.asyncio
async def test_dependencies_success(
    mock_application_deploy, mock_completion_event, pipeline_parameters
):
    cli_options = pipeline_parameters()
    dependency_frame = "other-frame"
    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
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
async def test_pausing(
    mock_application_deploy, mock_completion_event, pipeline_parameters
):
    cli_options = pipeline_parameters()
    dependency_frame = "other-frame"

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
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
async def test_in_progress_timeout(
    mock_application_deploy, mock_completion_event, pipeline_parameters
):
    cli_options = pipeline_parameters(
        monitor_sleep_seconds=2, wait_timeout_seconds=1
    )
    dependency_frame = "other-frame"

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
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
        DeploymentTerminatedError,
        match=r"^deployment cancelled due to timeout waiting for "
        "dependency completion",
    ):
        await deploy_frame(
            frame_data,
            deployment_data,
            this_status,
            cli_options,
        )


@pytest.mark.asyncio
async def test_frame_skipped(
    mock_application_deploy, mock_completion_event, pipeline_parameters
):
    cli_options = pipeline_parameters(
        monitor_sleep_seconds=2, wait_timeout_seconds=1
    )
    dependency_frame = "other-frame"

    mock_application, deployment_data, frame_data = mock_application_deploy
    frame_data.depends_on = [dependency_frame]

    this_status = DeploymentStatus(MOCK_CONTEXT, timeout_seconds=1)
    await this_status.initialize(dependency_frame)

    await asyncio.create_task(
        delayed_completion(
            dependency_frame,
            this_status,
            0.5,
            DeploymentState.ResultType.in_progress,
        )
    )
    deployment_data.data.to = StructuredTo(frame="f2")

    await deploy_frame(
        frame_data,
        deployment_data,
        this_status,
        cli_options,
    )

    f1_status = await this_status.read("f1")
    assert f1_status.code == DeploymentState.ResultType.skipped
