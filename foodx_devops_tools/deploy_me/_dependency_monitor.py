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
    DependencyDeclarations,
    IterationContext,
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


async def _confirm_dependency_entity_status(
    dependency_names: typing.Set[str],
    entity_status: DeploymentStatus,
    this_context: IterationContext,
    status_monitor_sleep_seconds: float,
) -> typing.Set[str]:
    """
    Check that dependency entities are present in entity status.

    Entities here are either frames or applications.
    """

    async def report_missing_dependencies(
        this_state: DeploymentState.ResultType,
        console_report: bool,
    ) -> str:
        nonlocal dependency_names, entity_status, this_context

        message = "dependency not in entity status, {0}, {1}".format(
            this_context, str(dependency_names)
        )
        log.warning(message)
        if console_report:
            click.echo(click.style(message, fg="yellow"))
        await entity_status.write(
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
        entity_contexts = await entity_status.names()
        if all([x in entity_contexts for x in dependency_contexts]):
            not_found = False
            log.debug(
                "all dependencies found in status, {0}, {1}, "
                "({2} retries)".format(
                    entity_contexts, dependency_contexts, attempt_count
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


async def wait_for_dependencies(
    iteration_context: IterationContext,
    dependency_data: DependencyDeclarations,
    entity_status: DeploymentStatus,
) -> None:
    """
    Wait for dependency entity status to succeed or fail.

    A timeout occurs if the specified duration is exceeded.

    Args:
        iteration_context: Current deployment hierarchy object.
        dependency_data: Entity dependency data.
        entity_status: Status reporting object for entities.

    Raises:
        DeploymentTerminatedError: If any dependencies don't complete or the
                                  maximum wait duration is exceeded.
    """

    async def cancel_deployment() -> None:
        nonlocal dependency_data, entity_status, iteration_context

        message = "cancelled due to dependency failure, {0}, {1}".format(
            iteration_context, str(dependency_data)
        )
        log.error(message)
        click.echo(click.style(message, fg="red"))
        await entity_status.write(
            str(iteration_context),
            DeploymentState.ResultType.cancelled,
            message=message,
        )
        raise DeploymentTerminatedError(message)

    async def report_success() -> None:
        nonlocal entity_status, iteration_context

        message = (
            "dependencies completed. proceeding with deployment, {0}".format(
                iteration_context
            )
        )
        log.info(message)
        click.echo(click.style(message, fg="cyan"))
        await entity_status.write(
            str(iteration_context), DeploymentState.ResultType.in_progress
        )

    # if there are no dependencies just skip dependency processing.
    if dependency_data:
        dependency_names = set(dependency_data)
        dependency_contexts = await _confirm_dependency_entity_status(
            dependency_names,
            entity_status,
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
                    entity_status.wait_for_completion(x)
                    for x in dependency_contexts
                ]
            )

            dependency_status = [
                await entity_status.read(x) for x in dependency_contexts
            ]
            if all_success(dependency_status):
                await report_success()
            elif any_completed_dirty(dependency_status):
                await cancel_deployment()
        except asyncio.TimeoutError:
            await entity_status.write(
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
    else:
        log.debug("Skipping empty dependencies for status")
