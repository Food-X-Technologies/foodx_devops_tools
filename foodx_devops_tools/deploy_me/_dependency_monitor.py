#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Deployment status monitoring."""

import asyncio
import copy
import logging

import click

from foodx_devops_tools.pipeline_config import (
    IterationContext,
    SingularFrameDefinition,
)

from ._exceptions import DeploymentCancelledError
from ._state import PipelineCliOptions
from ._status import DeploymentState, DeploymentStatus

log = logging.getLogger(__name__)


async def _status_wait(
    this_context: IterationContext,
    frame_data: SingularFrameDefinition,
    frame_status: DeploymentStatus,
    status_monitor_sleep_seconds: float,
) -> None:
    assert frame_data.depends_on

    async def cancel_deployment() -> None:
        nonlocal frame_data, frame_status, this_context

        message = "cancelled due to dependency failure, {0}, {1}".format(
            this_context, str(frame_data.depends_on)
        )
        log.error(message)
        click.echo(click.style(message, fg="red"))
        await frame_status.write(
            str(this_context),
            DeploymentState.ResultType.cancelled,
            message=message,
        )
        raise DeploymentCancelledError(message)

    async def report_completion() -> None:
        nonlocal frame_status, this_context

        message = (
            "dependencies completed. proceeding with deployment, {0}".format(
                this_context
            )
        )
        log.info(message)
        click.echo(click.style(message))
        await frame_status.write(
            str(this_context), DeploymentState.ResultType.in_progress
        )

    async def report_missing_dependencies() -> None:
        nonlocal frame_data, frame_status, this_context

        message = "dependency frames not in frame status, {0}, {1}".format(
            this_context, str(frame_data.depends_on)
        )
        log.warning(message)
        click.echo(click.style(message, fg="yellow"))
        await frame_status.write(
            str(this_context),
            DeploymentState.ResultType.pending,
            message=message,
        )

    # pause until dependencies are complete
    paused = True
    while paused:
        try:
            dependency_context = list()
            base = copy.deepcopy(this_context)
            for x in frame_data.depends_on:
                base[-1] = x
                dependency_context.append(str(base))
            dependency_status = [
                (await frame_status.read(x)).code for x in dependency_context
            ]
            if any(
                [
                    x
                    in [
                        DeploymentState.ResultType.failed,
                        DeploymentState.ResultType.cancelled,
                    ]
                    for x in dependency_status
                ]
            ):
                await cancel_deployment()

            if all(
                [
                    x == DeploymentState.ResultType.success
                    for x in dependency_status
                ]
            ):
                await report_completion()
                paused = False
            else:
                message = "waiting for dependency completion, {0}, {1}".format(
                    this_context, dependency_context
                )
                log.info(message)
                await asyncio.sleep(status_monitor_sleep_seconds)
        except KeyError:
            # we know the key is *supposed* to exist because it's defined in
            # `depends_on` (although it could be a typo), so keep trying in
            # case we just polled too early and it hasn't been registered
            # yet. the wait timeout will take care of it being the wrong value.
            await report_missing_dependencies()
            await asyncio.sleep(status_monitor_sleep_seconds)


async def process_dependencies(
    iteration_context: IterationContext,
    frame_data: SingularFrameDefinition,
    frame_status: DeploymentStatus,
    pipeline_parameters: PipelineCliOptions,
) -> None:
    """
    Wait for dependency frame status to succeed or fail.

    A timeout occurs if the specified duration is exceeded.

    Args:
        iteration_context: Current deployment hierarchy object.
        frame_data: Frame configuration data.
        frame_status: Status reporting object for frames.
        pipeline_parameters: Command line parameters.

    Raises:
        DeploymentCancelledError: If any dependencies don't complete or the
                                  maximum wait duration is exceeded.
    """
    # evaluate dependency status if they exist
    if frame_data.depends_on:
        try:
            await asyncio.wait_for(
                _status_wait(
                    iteration_context,
                    frame_data,
                    frame_status,
                    pipeline_parameters.monitor_sleep_seconds,
                ),
                timeout=pipeline_parameters.wait_timeout_seconds,
            )
        except asyncio.TimeoutError as e:
            message = "timeout waiting for dependencies, {0}".format(
                iteration_context
            )
            log.error(message)
            await frame_status.write(
                str(iteration_context),
                DeploymentState.ResultType.cancelled,
                message=message,
            )
            raise DeploymentCancelledError(message) from e
