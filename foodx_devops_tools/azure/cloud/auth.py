#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Azure authentication utilities."""

import asyncio
import dataclasses
import logging

from foodx_devops_tools.utilities import run_async_command
from foodx_devops_tools.utilities.exceptions import CommandError

log = logging.getLogger(__name__)


class AzureAuthenticationError(Exception):
    """Problem authenticating to Azure Cloud."""


@dataclasses.dataclass
class AzureCredentials:
    """Credentials data required for Azure Cloud authentication."""

    name: str
    secret: str
    subscription: str
    tenant: str
    userid: str


async def login_service_principal(credentials: AzureCredentials) -> None:
    """
    Login to Azure Cloud using service principal credentials.

    Args:
        credentials: Require Azure Cloud credentials.

    Raises:
        AzureAuthenticationError: If any error occurs during login.
    """
    result = None
    try:
        this_command = [
            "az",
            "login",
            "--service-principal",
            "--username",
            credentials.userid,
            "--password",
            credentials.secret,
            "--tenant",
            credentials.tenant,
        ]

        log.debug(str(this_command))
        result = await run_async_command(this_command)

        log.info(
            "login succeeded, {0} ({1}, {2})".format(
                credentials.name, credentials.subscription, credentials.tenant
            )
        )
    except asyncio.CancelledError:
        # should almost always let async cancelled exceptions propagate.
        raise
    except CommandError as e:
        log.error(
            "resource group deployment failed, {0} ({1}, {2}), {3}".format(
                credentials.name,
                credentials.subscription,
                credentials.tenant,
                str(e),
            )
        )
        if result:
            log.debug(
                "az login stdout, {0} ({1}, {2}), {3}".format(
                    credentials.name,
                    credentials.subscription,
                    credentials.tenant,
                    result.out,
                )
            )
            log.debug(
                "az login stderr, {0} ({1}, {2}), {3}".format(
                    credentials.name,
                    credentials.subscription,
                    credentials.tenant,
                    result.error,
                )
            )
        else:
            log.error(
                "unexpected error, {0} ({1}, {2}), {3}".format(
                    credentials.name,
                    credentials.subscription,
                    credentials.tenant,
                    str(e),
                )
            )
        raise AzureAuthenticationError(
            "Service principal authentication failed"
        ) from e
