#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import copy
import logging
import re
import typing

import click

from foodx_devops_tools.azure.cloud.auth import (
    AzureAuthenticationError,
    login_service_principal,
)
from foodx_devops_tools.azure.cloud.resource_group import (
    AzureSubscriptionConfiguration,
)
from foodx_devops_tools.azure.cloud.resource_group import (
    deploy as deploy_resource_group,
)
from foodx_devops_tools.pipeline_config import (
    ApplicationDefinition,
    ApplicationDeploymentSteps,
    ApplicationStepDelay,
    FlattenedDeployment,
    PipelineConfiguration,
    SingularFrameDefinition,
)
from foodx_devops_tools.pipeline_config.frames import (
    ApplicationStepDeploymentDefinition,
)
from foodx_devops_tools.pipeline_config.puff_map import PuffMapPaths
from foodx_devops_tools.puff import PuffError
from foodx_devops_tools.utilities.templates import prepare_deployment_files

from ._dependency_monitor import wait_for_dependencies
from ._exceptions import DeploymentError
from ._state import PipelineCliOptions
from ._status import DeploymentState, DeploymentStatus, all_success

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


def _construct_resource_group_name(
    client: str,
    user_resource_group_name: str,
) -> str:
    """Construct a resource group name from deployment context."""
    # want the client id as a prefix for easier sorting & grouping in portal.
    result = "-".join([client, user_resource_group_name])

    return result


def _mangle_validation_resource_group(current_name: str, suffix: str) -> str:
    this_suffix = re.sub(r"[_.+]", "-", suffix)
    mangled_name = f"{current_name}-{this_suffix}"

    return mangled_name


def _make_secrets_object(key_values: dict) -> typing.List[dict]:
    """Construct secrets into object form required by Foodx ARM template."""
    result = list()
    for k, v in key_values.items():
        this_entry = {
            "enabled": True,
            "key": k,
            "value": v,
        }
        result.append(this_entry)

    return result


def _construct_override_parameters(
    deployment_data: FlattenedDeployment,
    static_secrets_enabled: typing.Optional[bool],
    step_context: str,
) -> typing.Dict[str, typing.Any]:
    result: typing.Dict[str, typing.Any] = {
        "locations": {
            "primary": deployment_data.data.location_primary,
            "secondary": deployment_data.data.location_secondary,
        },
        "tags": deployment_data.context.as_dict(),
    }
    if static_secrets_enabled:
        if deployment_data.data.static_secrets:
            # pass static secrets as a single object containing all the
            # secret key-value pairs.
            parameter_object: typing.Dict[str, typing.Any] = {
                "staticSecrets": _make_secrets_object(
                    deployment_data.data.static_secrets
                )
            }
            result.update(parameter_object)
        else:
            log.warning(
                "There are no static_secrets even though secrets have been"
                " enabled, {0}".format(step_context)
            )

    return result


async def _do_step_deployment(
    this_step: ApplicationStepDeploymentDefinition,
    deployment_data: FlattenedDeployment,
    puff_parameter_paths: PuffMapPaths,
    this_context: str,
    enable_validation: bool,
) -> None:
    step_context = f"{this_context}.{this_step.name}"

    log.debug(
        f"deployment_data.context, "
        f"{step_context}, {str(deployment_data.context)}"
    )
    log.debug(
        f"deployment_data.data, {step_context}, "
        f"{str(deployment_data.data.deployment_tuple)}, "
        f"{str(deployment_data.data.location_primary)}, "
        f"{str(deployment_data.data.location_secondary)}, "
        f"{str(deployment_data.data.release_state)}, "
        f"{str(deployment_data.data.iteration_context)}"
    )
    try:
        resource_group = _construct_resource_group_name(
            deployment_data.context.client,
            this_step.resource_group,
        )

        await login_service_principal(deployment_data.data.azure_credentials)
        if enable_validation:
            log.info(f"validation deployment enabled, {step_context}")
            resource_group = _mangle_validation_resource_group(
                resource_group,
                deployment_data.context.pipeline_id,
            )
        else:
            log.info(f"deployment enabled, {step_context}")

        template_parameters = deployment_data.construct_template_parameters()
        log.debug(f"template parameters, {step_context}, {template_parameters}")

        template_files = deployment_data.construct_deployment_paths(
            this_step.arm_file,
            this_step.puff_file,
            puff_parameter_paths[this_step.name],
        )
        log.debug(f"template files, {template_files}")

        deployment_files = await prepare_deployment_files(
            template_files,
            template_parameters,
        )

        override_parameters = _construct_override_parameters(
            deployment_data, this_step.static_secrets, step_context
        )
        deployment_name = deployment_data.construct_deployment_name(
            this_step.name
        )
        this_subscription = AzureSubscriptionConfiguration(
            subscription_id=deployment_data.context.azure_subscription_name
        )
        await deploy_resource_group(
            resource_group,
            deployment_files.arm_template,
            deployment_files.parameters,
            deployment_data.data.location_primary,
            this_step.mode.value,
            this_subscription,
            deployment_name=deployment_name,
            override_parameters=override_parameters,
            validate=enable_validation,
        )
    except Exception as e:
        message = f"step deployment failed, {step_context}, {str(e)}"
        log.error(message)
        click.echo(click.style(message, fg="red"), err=True)
        raise


async def _deploy_step(
    this_step: ApplicationStepDeploymentDefinition,
    deployment_data: FlattenedDeployment,
    puff_parameter_data: PuffMapPaths,
    this_context: str,
    enable_validation: bool,
) -> None:
    step_context = "{0}.{1}".format(this_context, this_step.name)
    deploy_to = deployment_data.data.to
    if deploy_to.step and (this_step.name != deploy_to.step):
        log.warning(
            "application step skipped using deployment specifier, "
            "{0} skipped {1}".format(str(deploy_to), step_context)
        )
    else:
        await _do_step_deployment(
            this_step,
            deployment_data,
            puff_parameter_data,
            this_context,
            enable_validation,
        )
        log.info("application step succeeded, {0}".format(step_context))


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
            if isinstance(this_step, ApplicationStepDeploymentDefinition):
                await _deploy_step(
                    this_step,
                    deployment_data,
                    puff_parameter_data,
                    this_context,
                    enable_validation,
                )
            elif isinstance(this_step, ApplicationStepDelay):
                message = "application steps paused for, {0} (seconds)".format(
                    this_step.delay_seconds
                )
                log.info(message)
                click.echo(message)
                await asyncio.sleep(this_step.delay_seconds)
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
    deployment_data.data.iteration_context.append(
        deployment_data.data.deployment_tuple
    )
    deployment_data.data.puff_map = configuration.puff_map

    frame_deployment_status = DeploymentStatus(
        str(deployment_data.data.iteration_context),
        timeout_seconds=pipeline_parameters.wait_timeout_seconds,
    )
    try:
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
