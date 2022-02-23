#  Copyright (c) 2022 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import logging
import re
import typing

import click

from foodx_devops_tools.azure.cloud.resource_group import (
    AzureSubscriptionConfiguration,
)
from foodx_devops_tools.azure.cloud.resource_group import (
    deploy as deploy_resource_group,
)
from foodx_devops_tools.pipeline_config import FlattenedDeployment
from foodx_devops_tools.pipeline_config.frames import (
    ApplicationStepDeploymentDefinition,
)
from foodx_devops_tools.pipeline_config.puff_map import PuffMapPaths
from foodx_devops_tools.utilities.templates import prepare_deployment_files

log = logging.getLogger(__name__)


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

        if enable_validation:
            log.info(f"validation deployment enabled, {step_context}")
            resource_group = _mangle_validation_resource_group(
                resource_group,
                deployment_data.context.pipeline_id,
            )
        else:
            log.info(f"deployment enabled, {step_context}")

        template_parameters = deployment_data.construct_template_parameters(
            resource_group
        )
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


async def deploy_step(
    this_step: ApplicationStepDeploymentDefinition,
    deployment_data: FlattenedDeployment,
    puff_parameter_data: PuffMapPaths,
    this_context: str,
    enable_validation: bool,
) -> None:
    """
    Deploy Azure resources.

    Args:
        this_step: Deployment definition for this step action.
        deployment_data: Deployment context related parameters.
        puff_parameter_data: Puff file parameter data.
        this_context: Structured string context id.
        enable_validation: Enable or disable Azure validation deployment.
    """
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
