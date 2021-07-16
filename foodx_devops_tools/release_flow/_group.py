#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import click

from .._version import acquire_version
from .azure_cd import azure_subcommand
from .npm_ci import npm_subcommand


@click.group()
@click.version_option(version=acquire_version())
def release_flow() -> None:
    """Release flow command group."""


release_flow.add_command(azure_subcommand, name="azure")
release_flow.add_command(npm_subcommand, name="npm")
