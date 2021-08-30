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
import typing

import click

from foodx_devops_tools.pipeline_config import (
    IterationContext,
    SingularFrameDefinition,
)

from ._exceptions import DeploymentTerminatedError
from ._status import (
    DeploymentState,
    DeploymentStatus,
    all_success,
    any_completed_dirty,
)

log = logging.getLogger(__name__)

STATUS_KEY_MAX_RETRIES = 20
STATUS_KEY_RETRY_SLEEP_SECONDS = 10


def _generate_dependency_contexts(
    this_context: IterationContext, dependency_names: typing.Set[str]
) -> typing.Set[str]:
    dependency_context = set()
    for x in dependency_names:
        base = copy.deepcopy(this_context)
        base[-1] = x
        dependency_context.add(str(base))

    return dependency_context


async def _confirm_dependency_frame_status(
    dependency_names: typing.Set[str],
    frame_status: DeploymentStatus,
    this_context: IterationContext,
    status_monitor_sleep_seconds: float,
) -> typing.Set[str]:
    """Check that dependency frames are present in frame status."""

    async def report_missing_dependencies(
        this_state: DeploymentState.ResultType,
        console_report: bool,
    ) -> str:
        nonlocal dependency_names, frame_status, this_context

        message = "dependency frames not in frame status, {0}, {1}".format(
            this_context, str(dependency_names)
        )
        log.warning(message)
        if console_report:
            click.echo(click.style(message, fg="yellow"))
        await frame_status.write(
            str(this_context),
            this_state,
            message=message,
        )

        return message

    dependency_contexts = _generate_dependency_contexts(
        this_context, dependency_names
    )

    # we know the key is *supposed* to exist because it's defined in
    # `depends_on` (although it could be a typo), so keep trying in
    # case we just polled too early and it hasn't been registered
    # yet. the wait timeout will take care of it being the wrong value.
    not_found = True
    attempt_count = 0
    while not_found and (attempt_count < STATUS_KEY_MAX_RETRIES):
        frame_contexts = await frame_status.names()
        if all([x in frame_contexts for x in dependency_contexts]):
            not_found = False
            log.debug(
                "all dependencies found in status, {0}, {1}, "
                "({2} retries)".format(
                    frame_contexts, dependency_contexts, attempt_count
                )
            )
        else:
            attempt_count += 1
            await report_missing_dependencies(
                DeploymentState.ResultType.pending, False
            )
            await asyncio.sleep(status_monitor_sleep_seconds)

    if not_found:
        message = await report_missing_dependencies(
            DeploymentState.ResultType.failed, True
        )
        raise DeploymentTerminatedError(message)

    return dependency_contexts


async def process_dependencies(
    iteration_context: IterationContext,
    frame_data: SingularFrameDefinition,
    frame_status: DeploymentStatus,
) -> None:
    """
    Wait for dependency frame status to succeed or fail.

    A timeout occurs if the specified duration is exceeded.

    Args:
        iteration_context: Current deployment hierarchy object.
        frame_data: Frame configuration data.
        frame_status: Status reporting object for frames.

    Raises:
        DeploymentTerminatedError: If any dependencies don't complete or the
                                  maximum wait duration is exceeded.
    """

    async def cancel_deployment() -> None:
        nonlocal frame_data, frame_status, iteration_context

        message = "cancelled due to dependency failure, {0}, {1}".format(
            iteration_context, str(frame_data.depends_on)
        )
        log.error(message)
        click.echo(click.style(message, fg="red"))
        await frame_status.write(
            str(iteration_context),
            DeploymentState.ResultType.cancelled,
            message=message,
        )
        raise DeploymentTerminatedError(message)

    async def report_success() -> None:
        nonlocal frame_status, iteration_context

        message = (
            "dependencies completed. proceeding with deployment, {0}".format(
                iteration_context
            )
        )
        log.info(message)
        click.echo(click.style(message, fg="cyan"))
        await frame_status.write(
            str(iteration_context), DeploymentState.ResultType.in_progress
        )

    # if there are no dependencies just skip dependency processing.
    if frame_data.depends_on:
        dependency_names = set(frame_data.depends_on)
        dependency_contexts = await _confirm_dependency_frame_status(
            dependency_names,
            frame_status,
            iteration_context,
            STATUS_KEY_RETRY_SLEEP_SECONDS,
        )

        message = "waiting for dependency completion, {0}, {1}".format(
            iteration_context, dependency_contexts
        )
        log.info(message)
        click.echo(click.style(message))
        try:
            await asyncio.gather(
                *[
                    frame_status.wait_for_completion(x)
                    for x in dependency_contexts
                ]
            )

            dependency_status = [
                await frame_status.read(x) for x in dependency_contexts
            ]
            if all_success(dependency_status):
                await report_success()
            elif any_completed_dirty(dependency_status):
                await cancel_deployment()
        except asyncio.TimeoutError:
            await frame_status.write(
                str(iteration_context),
                DeploymentState.ResultType.cancelled,
                message=message,
            )
            message = (
                "deployment cancelled due to timeout waiting for "
                "dependency completion, {0}".format(str(iteration_context))
            )
            log.error(message)
            click.echo(click.style(message, fg="red"))
            raise DeploymentTerminatedError(message)
