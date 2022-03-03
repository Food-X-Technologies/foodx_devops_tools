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

import click

from foodx_devops_tools.azure.cloud.auth import (
    AzureAuthenticationError,
    login_service_principal,
)
from foodx_devops_tools.pipeline_config import (
    ApplicationDefinition,
    ApplicationDeploymentSteps,
    FlattenedDeployment,
    PipelineConfiguration,
    SingularFrameDefinition,
)
from foodx_devops_tools.pipeline_config.frames import (
    ApplicationStepDelay,
    ApplicationStepDeploymentDefinition,
    ApplicationStepScript,
)
from foodx_devops_tools.profiling import timing
from foodx_devops_tools.puff import PuffError

from ._dependency_monitor import wait_for_dependencies
from ._exceptions import DeploymentError
from ._state import PipelineCliOptions
from ._status import DeploymentState, DeploymentStatus, all_success
from .application_steps import delay_step, deploy_step, script_step

log = logging.getLogger(__name__)

STATUS_SLEEP_SECONDS = 1


def any_failed(values: typing.List[DeploymentState]) -> bool:
    """Evaluate if any deployment states failed."""
    result = any([x.code == DeploymentState.ResultType.failed for x in values])
    return result


def all_cancelled(values: typing.List[DeploymentState]) -> bool:
    """Evaluate if all deployments were cancelled."""
    result = all(
        [x.code == DeploymentState.ResultType.cancelled for x in values]
    )
    return result


async def assess_results(
    results: typing.List[DeploymentState],
) -> DeploymentState:
    """
    Condense an array of deployment results into a single result.

    Args:
        results: Array of results to condense.

    Returns:
        Success, if all results are success. Failed otherwise.
    """
    if all_success(results):
        log.debug("assessed result success")
        this_result = DeploymentState(code=DeploymentState.ResultType.success)
    elif any_failed(results):
        log.debug("assessed result failed")
        this_result = DeploymentState(code=DeploymentState.ResultType.failed)
    elif all_cancelled(results):
        log.debug("assessed result cancelled")
        this_result = DeploymentState(code=DeploymentState.ResultType.cancelled)
    else:
        # fallback is failure.
        log.debug("fallback to failed")
        messages = [
            x.message
            for x in results
            if x.message and (x.code != DeploymentState.ResultType.success)
        ]
        this_result = DeploymentState(
            code=DeploymentState.ResultType.failed, message=str(messages)
        )

    return this_result


async def _do_application_deployment(
    this_context: str,
    application_data: ApplicationDeploymentSteps,
    deployment_data: FlattenedDeployment,
    application_status: DeploymentStatus,
    enable_validation: bool,
) -> None:
    try:
        puff_frame_data = deployment_data.data.puff_map.frames[
            deployment_data.context.frame_name
        ]
        puff_application_data = puff_frame_data.applications[
            deployment_data.context.application_name
        ]
        puff_parameter_data = puff_application_data.arm_parameters_files[
            deployment_data.context.release_state
        ][deployment_data.context.azure_subscription_name]

        for this_step in application_data:
            with timing(log, this_context):
                if isinstance(this_step, ApplicationStepDeploymentDefinition):
                    await deploy_step(
                        this_step,
                        deployment_data,
                        puff_parameter_data,
                        this_context,
                        enable_validation,
                    )
                elif isinstance(this_step, ApplicationStepScript):
                    await script_step(
                        this_step,
                        deployment_data,
                        this_context,
                    )
                elif isinstance(this_step, ApplicationStepDelay):
                    await delay_step(this_step.delay_seconds)
                else:
                    raise DeploymentError(
                        "Bad application step definition, "
                        "{0}".format(this_context)
                    )

        log.info("application deployment succeeded, {0}".format(this_context))
        await application_status.write(
            this_context, DeploymentState.ResultType.success
        )
    except asyncio.CancelledError:
        message = "async cancelled signal"
        log.error(message)
        await application_status.write(
            this_context,
            DeploymentState.ResultType.cancelled,
            message,
        )
        raise
    except (AzureAuthenticationError, PuffError) as e:
        message = (
            "application deployment authentication "
            "failure, {0}, {1}, {2}".format(this_context, type(e), str(e))
        )
        await application_status.write(
            this_context,
            DeploymentState.ResultType.failed,
            message,
        )
        log.error(message)


async def deploy_application(
    application_data: ApplicationDefinition,
    deployment_data: FlattenedDeployment,
    application_status: DeploymentStatus,
    enable_validation: bool,
) -> None:
    """
    Deploy the steps of a frame application.

    Application steps must be deployed in sequence (serially).
    """
    this_context = str(deployment_data.data.iteration_context)
    try:
        message = "starting application deployment, {0}".format(this_context)
        log.info(message)
        click.echo(message)
        await application_status.initialize(this_context)

        await wait_for_dependencies(
            deployment_data.data.iteration_context,
            application_data.depends_on
            if application_data.depends_on
            else list(),
            application_status,
        )

        await application_status.write(
            this_context, DeploymentState.ResultType.in_progress
        )

        deploy_to = deployment_data.data.to
        application_name = deployment_data.context.application_name
        if deploy_to.application and (
            application_name != deploy_to.application
        ):
            await application_status.write(
                this_context,
                DeploymentState.ResultType.skipped,
                message="deployment targeted application, {0}".format(
                    str(deploy_to)
                ),
            )
        else:
            with timing(log, this_context):
                await _do_application_deployment(
                    this_context,
                    application_data.steps,
                    deployment_data,
                    application_status,
                    enable_validation,
                )
    except Exception as e:
        message = "application deployment failed, {0}, {1}, {2}".format(
            this_context, type(e), str(e)
        )
        await application_status.write(
            this_context,
            DeploymentState.ResultType.failed,
            message,
        )
        log.exception(message)

    message = "application deployment completed, {0}".format(this_context)
    log.info(message)
    click.echo(click.style(message, fg="yellow"))


async def _do_frame_deployment(
    this_context: str,
    pipeline_parameters: PipelineCliOptions,
    deployment_data: FlattenedDeployment,
    frame_data: SingularFrameDefinition,
    frame_status: DeploymentStatus,
) -> None:
    # application status will show as "pending" until deployment activates.
    application_status = DeploymentStatus(
        this_context, pipeline_parameters.wait_timeout_seconds
    )
    try:
        wait_task = asyncio.create_task(
            application_status.wait_for_all_completed()
        )
        application_status.start_monitor()

        await wait_for_dependencies(
            deployment_data.data.iteration_context,
            frame_data.depends_on if frame_data.depends_on else list(),
            frame_status,
        )

        frame_deployment = copy.deepcopy(deployment_data)
        frame_deployment.data.frame_folder = frame_data.folder

        await asyncio.gather(
            *[
                deploy_application(
                    application_data,
                    frame_deployment.copy_add_application(application_name),
                    application_status,
                    pipeline_parameters.enable_validation,
                )
                for application_name, application_data in frame_data.applications.items()  # noqa: E501
            ],
            return_exceptions=False,
        )

        await wait_task

        message = "frame deployment completed, {0}".format(this_context)
        log.info(message)
        click.echo(click.style(message, fg="yellow"))
    except asyncio.TimeoutError:
        message = "timeout waiting for application deployment, {0}".format(
            deployment_data.data.iteration_context
        )
        log.error(message)
        click.echo(message, err=True)
        raise

    # read the state of the completed _applications_
    results = [
        await application_status.read(x)
        for x in await application_status.names()
    ]
    condensed_result = await assess_results(results)
    await frame_status.write(
        this_context, condensed_result.code, condensed_result.message
    )
    message = "frame deployment {0}, {1}".format(
        condensed_result.code.name, this_context
    )
    log.info(message)
    click.echo(
        click.style(
            message, fg=DeploymentStatus.STATE_COLOURS[condensed_result.code]
        )
    )


async def deploy_frame(
    frame_data: SingularFrameDefinition,
    deployment_data: FlattenedDeployment,
    frame_status: DeploymentStatus,
    pipeline_parameters: PipelineCliOptions,
) -> None:
    """
    Deploy the applications of a frame.

    Frame applications are deployed concurrently (in parallel).

    Raises:
        DeploymentTerminatedError: If any dependencies fail preventing
                                  completion.
    """
    this_context = str(deployment_data.data.iteration_context)
    message = "starting frame deployment, {0}".format(this_context)
    log.info(message)
    click.echo(message)

    await frame_status.initialize(this_context)
    await frame_status.write(
        this_context, DeploymentState.ResultType.in_progress
    )
    deploy_to = deployment_data.data.to
    frame_name = deployment_data.context.frame_name
    if deploy_to.frame and (frame_name != deploy_to.frame):
        await frame_status.write(
            this_context,
            DeploymentState.ResultType.skipped,
            message="deployment targeted frame, {0}".format(str(deploy_to)),
        )
    else:
        with timing(log, this_context):
            await _do_frame_deployment(
                this_context,
                pipeline_parameters,
                deployment_data,
                frame_data,
                frame_status,
            )


async def do_deploy(
    configuration: PipelineConfiguration,
    deployment_data: FlattenedDeployment,
    pipeline_parameters: PipelineCliOptions,
) -> DeploymentState:
    """
    Deploy the frames in a flattened deployment configuration.

    Raises:
        asyncio.TimeoutError: If the maximum wait time in
                              ``pipeline_parameters`` is exceeded.
    """
    this_frames = configuration.frames
    this_context = deployment_data.data.iteration_context.copy()
    deployment_data.data.iteration_context.append(
        deployment_data.data.deployment_tuple
    )
    deployment_data.data.puff_map = configuration.puff_map

    frame_deployment_status = DeploymentStatus(
        str(deployment_data.data.iteration_context),
        timeout_seconds=pipeline_parameters.wait_timeout_seconds,
    )
    try:
        with timing(log, str(this_context)):
            # this is a temporary work-around to the login concurrency problem -
            # it works provided there is no more than a single subscription per
            # deployment at a time.
            # https://github.com/Food-X-Technologies/foodx_devops_tools/issues/129
            await login_service_principal(
                deployment_data.data.azure_credentials
            )

            wait_task = asyncio.create_task(
                frame_deployment_status.wait_for_all_completed()
            )
            frame_deployment_status.start_monitor()

            await asyncio.gather(
                *[
                    deploy_frame(
                        frame_data,
                        deployment_data.copy_add_frame(frame_name),
                        frame_deployment_status,
                        pipeline_parameters,
                    )
                    for frame_name, frame_data in this_frames.frames.items()
                ],
                return_exceptions=False,
            )
            await wait_task
    except asyncio.TimeoutError:
        message = "timeout waiting for frame deployments, {0}".format(
            deployment_data.data.iteration_context
        )
        log.error(message)
        click.echo(message, err=True)
        raise

    results = [
        await frame_deployment_status.read(x)
        for x in await frame_deployment_status.names()
    ]
    condensed_result = await assess_results(results)

    return condensed_result
