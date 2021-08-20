#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Azure resource utilities."""

import asyncio
import json
import logging
import typing

from foodx_devops_tools.utilities import run_async_command

from .model import AzureSubscriptionConfiguration

log = logging.getLogger(__name__)


class ResourceError(Exception):
    """Problem occurred with resource related actions."""


async def list_resources(
    subscription: AzureSubscriptionConfiguration,
    name: typing.Optional[str] = None,
    location: typing.Optional[str] = None,
    tag: typing.Optional[str] = None,
) -> typing.List[dict]:
    """
    List resources in a specified subscription.

    The same name, location and tag glob filters as Azure CLI utility may be
    specified.

    Args:
        subscription: Subscription to list resources in.
        name: Name of resource to search for [optional].
        location: Location of resource to search for [optional].
        tag: Tag(s) of resource(s) to search for [optional].

    Returns:
        List of resource found. Empty list otherwise.
    """
    if (not name) and (not location) and (not tag):
        raise ResourceError(
            "Must specify at least one of name, location or tag"
        )

    this_command = [
        "az",
        "resource",
        "list",
        "--subscription",
        subscription.subscription_id,
    ]
    if name:
        this_command += ["--name", name]
    if location:
        this_command += ["--location", location]
    if tag:
        this_command += ["--tag", tag]
    log.debug("{0}".format(str(this_command)))
    result = await run_async_command(this_command)
    log.debug("list resources stdout, {0}".format(result.out))
    log.debug("list resources stderr, {0}".format(result.error))

    data: typing.List[dict] = json.loads(result.out)
    log.debug("{0}".format(str(data)))
    return data


async def check_exists(
    resource_name: str, subscription: AzureSubscriptionConfiguration
) -> typing.List[dict]:
    """
    Check that the named resource exists.

    Take care that multiple resources of different types could have the same
    name, so a non-null result is not necessarily affirmation of the
    existence you intend.

    Args:
        resource_name: Name of resource to find.
        subscription: Subscription to search for resource.

    Returns:
        Dictionary of resource(s) found. Empty dictionary otherwise.
    Raises:
        ResourceError: If any problems occur doing the check.
    """
    try:
        result_data = await list_resources(subscription, name=resource_name)

        matches = list()
        for this_resource in result_data:
            if this_resource["name"] == resource_name:
                matches.append(this_resource.copy())

        return matches
    except asyncio.CancelledError:
        # should almost always let async cancelled exceptions propagate.
        raise
    except Exception as e:
        raise ResourceError(
            "Problem acquiring resource  data, {0}".format(resource_name)
        ) from e
