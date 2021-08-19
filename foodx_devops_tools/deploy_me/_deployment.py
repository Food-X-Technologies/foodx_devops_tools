#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import logging
import pathlib
import re
import typing

import click

from foodx_devops_tools.azure.cloud.resource_group import (
    AzureSubscriptionConfiguration,
)
from foodx_devops_tools.azure.cloud.resource_group import (
    deploy as deploy_resource_group,
)
from foodx_devops_tools.azure.cloud.resource_group import (
    validate as validate_resource_group,
)
from foodx_devops_tools.pipeline_config import (
    ApplicationDeploymentSteps,
    FlattenedDeployment,
    PipelineConfiguration,
    SingularFrameDefinition,
)

from ._dependency_monitor import process_dependencies
from ._state import PipelineCliOptions
from ._status import DeploymentState, DeploymentStatus

log = logging.getLogger(__name__)

SUBSCRIPTION_NAME_REGEX = (
    r"(?P<system>[a-z0-9]+)_(?P<client>[a-z0-9]+)_(?P<state>[a-z0-9]+)"
)


def assess_results(results: typing.List[DeploymentState]) -> DeploymentState:
    """
    Condense an array of deployment results into a single result.

    Args:
        results: Array of results to condense.

    Returns:
        Success, if all results are success. Failed otherwise.
    """
    if all([x.code == DeploymentState.ResultType.success for x in results]):
        this_result = DeploymentState(code=DeploymentState.ResultType.success)
    else:
        messages = [
            x.message
            for x in results
            if x.message and (x.code != DeploymentState.ResultType.success)
        ]
        this_result = DeploymentState(
            code=DeploymentState.ResultType.failed, message=str(messages)
        )

    return this_result


def _construct_resource_group_name(
    application_name: str, frame_name: str, client: str
) -> str:
    """Construct a resource group name from deployment context."""
    return "-".join([application_name, frame_name, client])


def _construct_fqdn(
    leaf_name: str, domain_root: str, client: str, subscription_name: str
) -> str:
    """Construct an FQDN from deployment context."""
    this_match = re.match(SUBSCRIPTION_NAME_REGEX, subscription_name)
    if this_match is not None:
        subd_state = this_match.group("state")
    else:
        # assume the entire subscription name is DNS valid
        subd_state = subscription_name

    return ".".join([leaf_name, subd_state, client, domain_root])


def _mangle_validation_resource_group(current_name: str, suffix: str) -> str:
    this_suffix = re.sub(r"[_.+]", "-", suffix)
    mangled_name = f"{current_name}-{this_suffix}"

    return mangled_name


async def deploy_application(
    application_data: ApplicationDeploymentSteps,
    deployment_data: FlattenedDeployment,
    application_status: DeploymentStatus,
    enable_validation: bool,
    frame_folder: pathlib.Path,
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

        await application_status.write(
            this_context, DeploymentState.ResultType.in_progress
        )

        puff_frame_data = deployment_data.data.puff_map.frames[
            deployment_data.context.frame_name
        ]
        puff_application_data = puff_frame_data.applications[
            deployment_data.context.application_name
        ]
        puff_parameter_data = puff_application_data.arm_parameters_files[
            deployment_data.context.release_state
        ][deployment_data.context.azure_subscription_name]

        this_subscription = AzureSubscriptionConfiguration(
            subscription_id=deployment_data.context.azure_subscription_name
        )
        for this_step in application_data:
            resource_group = (
                _construct_resource_group_name(
                    deployment_data.context.application_name,
                    deployment_data.context.frame_name,
                    deployment_data.context.client,
                )
                if not this_step.resource_group
                else this_step.resource_group
            )
            arm_template_path = (
                frame_folder / this_step.arm_file
                if this_step.arm_file
                else frame_folder
                / "{0}.json".format(deployment_data.context.application_name)
            )
            arm_parameters_path = (
                frame_folder / puff_parameter_data[this_step.name]
            )

            log.debug(
                "deployment_data.context, {0}, {1}".format(
                    this_context, str(deployment_data.context)
                )
            )
            log.debug(
                "deployment_data.data, {0}, {1}".format(
                    this_context, str(deployment_data.data)
                )
            )
            if enable_validation:
                log.info(
                    "validation deployment enabled, {0}".format(this_context)
                )
                resource_group = _mangle_validation_resource_group(
                    resource_group,
                    deployment_data.context.pipeline_id,
                )
                log.info(
                    "validation resource group name, {0}".format(resource_group)
                )
                await validate_resource_group(
                    resource_group,
                    arm_template_path,
                    arm_parameters_path,
                    deployment_data.data.location_primary,
                    this_step.mode.value,
                    this_subscription,
                )
            else:
                log.info("deployment enabled, {0}".format(this_context))
                await deploy_resource_group(
                    resource_group,
                    arm_template_path,
                    arm_parameters_path,
                    deployment_data.data.location_primary,
                    this_step.mode.value,
                    this_subscription,
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

    log.info("application deployment completed, {0}".format(this_context))


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
        DeploymentCancelledError: If any dependencies fail preventing
                                  completion.
    """
    this_context = str(deployment_data.data.iteration_context)
    message = "starting frame deployment, {0}".format(this_context)
    log.info(message)
    click.echo(message)

    await frame_status.initialize(this_context)
    # application status will show as "pending" until deployment activates.
    application_status = DeploymentStatus(this_context)
    await application_status.start_monitor()

    await process_dependencies(
        deployment_data.data.iteration_context,
        frame_data,
        frame_status,
        pipeline_parameters,
    )

    await asyncio.gather(
        *[
            deploy_application(
                application_data,
                deployment_data.copy_add_application(application_name),
                application_status,
                pipeline_parameters.enable_validation,
                frame_data.folder,
            )
            for application_name, application_data in frame_data.applications.items()  # noqa: E501
        ],
        return_exceptions=False,
    )

    results = [await frame_status.read(x) for x in await frame_status.names()]
    condensed_result = assess_results(results)
    await frame_status.write(
        this_context, condensed_result.code, condensed_result.message
    )


async def do_deploy(
    configuration: PipelineConfiguration,
    deployment_data: FlattenedDeployment,
    pipeline_parameters: PipelineCliOptions,
) -> DeploymentState:
    """Deploy the frames in a flattened deployment configuration."""
    this_frames = configuration.frames
    deployment_data.data.iteration_context.append(
        deployment_data.data.deployment_tuple
    )
    deployment_data.data.puff_map = configuration.puff_map

    frame_deployment_status = DeploymentStatus(
        str(deployment_data.data.iteration_context)
    )
    await frame_deployment_status.start_monitor()

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

    results = [
        await frame_deployment_status.read(x)
        for x in await frame_deployment_status.names()
    ]
    condensed_result = assess_results(results)

    return condensed_result
