#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Azure authentication utilities."""

import asyncio
import dataclasses
import json
import logging
import typing

from foodx_devops_tools.utilities import CapturedStreams, run_async_command
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


def _failure_logging(
    result: typing.Optional[CapturedStreams],
    credentials: AzureCredentials,
    e: Exception,
) -> None:
    log.error(
        "az login failed, {0} ({1}, {2}), {3}".format(
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


async def login_service_principal(credentials: AzureCredentials) -> dict:
    """
    Login to Azure Cloud using service principal credentials.

    Args:
        credentials: Require Azure Cloud credentials.

    Returns:
        Parsed JSON from ``az login`` output.
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
        result_data = json.loads(result.out)
        return result_data
    except asyncio.CancelledError:
        # should almost always let async cancelled exceptions propagate.
        log.debug("az login cancelled")
        raise
    except CommandError as e:
        _failure_logging(result, credentials, e)
        raise AzureAuthenticationError(
            "Service principal authentication failed, {0}".format(str(e))
        ) from e
    except Exception as e:
        _failure_logging(result, credentials, e)
        raise AzureAuthenticationError(
            "Service principal authentication failed, {0}".format(str(e))
        ) from e
