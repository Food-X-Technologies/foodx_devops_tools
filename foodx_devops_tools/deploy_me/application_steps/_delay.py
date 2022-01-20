#  Copyright (c) 2022 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import asyncio
import logging

import click

log = logging.getLogger(__name__)


async def delay_step(delay_seconds: float) -> None:
    """
    Pause a deployment for the specified duration.

    Args:
        delay_seconds: Pause delay in seconds.
    """
    message = "application steps paused for, {0} (seconds)".format(
        delay_seconds
    )
    log.info(message)
    click.echo(message)
    await asyncio.sleep(delay_seconds)
