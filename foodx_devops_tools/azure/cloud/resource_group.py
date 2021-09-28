#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Azure resource group utilities."""

import asyncio
import contextlib
import json
import logging
import pathlib
import re
import typing

from foodx_devops_tools.utilities import run_async_command
from foodx_devops_tools.utilities.exceptions import CommandError

from .model import AzureSubscriptionConfiguration

log = logging.getLogger(__name__)

AZURE_GROUP_ID_PATTERN = (
    r"^/subscriptions/"
    r"(?P<subscription_id>[0-9a-z\-]+)"
    r"/resourceGroups/"
    r"(?P<group_name>[A-Za-z0-9\-_]+)"
)
AZURE_GROUP_MATCH = re.compile(AZURE_GROUP_ID_PATTERN)


class ResourceGroupError(Exception):
    """Problem occurred with resource group related actions."""


async def check_exists(
    resource_group_name: str, subscription: AzureSubscriptionConfiguration
) -> dict:
    """
    Determine if a resource group exists in the specified subscription.

    Assume authentication has already occurred such that subsequent ``az``
    CLI commands will succeed.

    Args:
        resource_group_name: Name of resource group to find
        subscription: Subscription to search for resource group

    Returns:
        Query result data on success. Empty dictionary otherwise.
    Raises:
        ResourceGroupError: If any error occurs preventing the search from
                            completing.
    """
    try:
        this_command = [
            "az",
            "group",
            "list",
            "--subscription",
            subscription.subscription_id,
        ]
        log.debug("{0}".format(str(this_command)))
        result = await run_async_command(this_command)
        log.debug(
            "resource group existence check stdout, {0}".format(result.out)
        )
        log.debug(
            "resource group existence check stderr, {0}".format(result.error)
        )

        result_data = json.loads(result.out)
        log.debug("{0}".format(str(result_data)))
        group_result = dict()
        for this_group in result_data:
            this_match = AZURE_GROUP_MATCH.match(this_group["id"])
            if (
                this_match
                and this_match.group("group_name") == resource_group_name
            ):
                group_result = this_group.copy()
                log.debug("group exists, {0}".format(str(group_result)))

        return group_result
    except asyncio.CancelledError:
        # should almost always let async cancelled exceptions propagate.
        raise
    except Exception as e:
        raise ResourceGroupError(
            "Problem acquiring resource group data, {0}, {1}, {2}".format(
                resource_group_name, type(e), str(e)
            )
        ) from e


async def create(
    resource_group_name: str,
    location: str,
    subscription: AzureSubscriptionConfiguration,
) -> None:
    """
    Idempotent creation of an Azure resource group.

    Args:
        resource_group_name: Name of resource group to create.
        location: Azure location in which to create the resource group.
        subscription: Azure subscription identity for the resource group.
    """
    group_data = await check_exists(resource_group_name, subscription)
    if not group_data:
        result = await run_async_command(
            [
                "az",
                "group",
                "create",
                "--resource-group",
                resource_group_name,
                "--location",
                location,
            ]
        )
        log.debug("resource group creation stdout, {0}".format(result.out))
        log.debug("resource group creation stderr, {0}".format(result.error))


async def delete(
    resource_group_name: str,
    subscription: AzureSubscriptionConfiguration,
) -> None:
    """
    Delete an Azure resource group.

    Args:
        resource_group_name: Name of resource group to create.
        subscription: Azure subscription identity for the resource group.
    """
    group_data = await check_exists(resource_group_name, subscription)
    if group_data:
        log.info(
            "deleting resource group, {0}, {1}".format(
                resource_group_name, subscription.subscription_id
            )
        )
        result = await run_async_command(
            [
                "az",
                "group",
                "delete",
                "--resource-group",
                resource_group_name,
                "--yes",
            ]
        )
        log.debug("resource group deletion stdout, {0}".format(result.out))
        log.debug("resource group deletion stderr, {0}".format(result.error))
    else:
        log.info(
            "no delete resource group as it does not exist, {0}, {1}".format(
                resource_group_name, subscription.subscription_id
            )
        )


def _make_arm_parameter_values(key_values: dict) -> dict:
    """Transform a key-value dictionary into ARM template parameter data."""
    result = dict()
    for k, v in key_values.items():
        result[k] = {"value": v}

    return result


async def deploy(
    resource_group_name: str,
    arm_template_path: pathlib.Path,
    arm_parameters_path: pathlib.Path,
    location: str,
    mode: str,
    subscription: AzureSubscriptionConfiguration,
    deployment_name: typing.Optional[str] = None,
    override_parameters: typing.Optional[dict] = None,
    validate: bool = False,
) -> None:
    """
    Deploy resource to a resource group.

    The resources are defined in ARM template JSON or bicep files, per Azure
    CLI utility.

    Args:
        resource_group_name: Resource group name
        arm_template_path: Path to ARM template deployment file.
        arm_parameters_path: Path to ARM template deployment parameters file.
        location: Azure location in which to deploy resource group.
        mode: Deployment mode; "Complete" or "Incremental".
        subscription: Target subscription/tenant for deployment.
        override_parameters: Key-value pairs of json compatible data to pass
            to deployment. (optional; default None)
        validate: Flag to enable deployment validation. (optional; default
            False)
    """
    result = None
    try:
        await create(resource_group_name, location, subscription)
        # assume az cli is in the PATH when command is run...
        this_command = [
            "az",
            "deployment",
            "group",
            "create" if not validate else "validate",
            "--mode",
            mode,
            "--resource-group",
            resource_group_name,
            "--template-file",
            str(arm_template_path),
            "--parameters",
            "@{0}".format(arm_parameters_path),
        ]
        if deployment_name:
            this_command += [
                "--name",
                deployment_name,
            ]
        log.debug("az command, {0}".format(str(this_command)))
        if override_parameters:
            # WARNING: these external parameters may be sensitive content
            # such as secrets, so DO NOT LOG.
            log.debug(
                "az command override parameters specified. content "
                "withheld from log."
            )
            this_command += [
                "--parameters",
                "{0}".format(
                    json.dumps(_make_arm_parameter_values(override_parameters))
                ),
            ]

        result = await run_async_command(this_command)
        log.info(
            "resource group deployment succeeded, {0} ({1})".format(
                resource_group_name, subscription.subscription_id
            )
        )
    except CommandError as e:
        log.error(
            "resource group deployment failed, {0} ({1}), {2}".format(
                resource_group_name, subscription.subscription_id, str(e)
            )
        )
        if result:
            log.debug(
                "resource group deployment stdout, {0} ({1}), {2}".format(
                    resource_group_name,
                    subscription.subscription_id,
                    result.out,
                )
            )
            log.debug(
                "resource group deployment stderr, {0} ({1}), {2}".format(
                    resource_group_name,
                    subscription.subscription_id,
                    result.error,
                )
            )
        else:
            log.error(
                "unexpected error, {0} ({1}), {2}".format(
                    resource_group_name, subscription.subscription_id, str(e)
                )
            )
        raise


@contextlib.asynccontextmanager
async def delete_when_done(
    resource_group_name: str,
    subscription: AzureSubscriptionConfiguration,
) -> typing.AsyncGenerator[None, None]:
    """
    Delete a resource group when this context goes out of scope.

    Should probably not be used for "normal" resource group creation
    deployments, but is likely to be useful for clean up of validation
    deployments.

    Args:
        resource_group_name: Name of resource group to delete.
        subscription: Subscription that "owns" the resource group.
    """
    yield

    # don't block for deletion event.
    await asyncio.shield(
        asyncio.create_task(delete(resource_group_name, subscription))
    )
