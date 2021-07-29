#!python3
# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Validation pipeline configuration data."""

import enum
import pathlib
import sys

import click

from .console import report_failure, report_success
from .pipeline_config import (
    PipelineConfiguration,
    PipelineConfigurationError,
    PipelineConfigurationPaths,
)

DEFAULT_CONFIGURATION_FILES = {
    "clients": "clients.yml",
    "deployments": "deployments.yml",
    "frames": "frames.yml",
    "release_states": "release_states.yml",
    "subscriptions": "subscriptions.yml",
    "systems": "systems.yml",
    "tenants": "tenants.yml",
}


@enum.unique
class ExitState(enum.Enum):
    """Validate configuration script exit states."""

    UNKNOWN = 100
    MISSING_GITREF = 101
    GITREF_PARSE_FAILURE = 102


@click.command()
@click.argument(
    "configuration_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def _main(configuration_dir: str) -> None:
    """Validate pipeline configuration files.

    Exits non-zero if validation fails.

    CONFIGURATION_DIR is the path to the directory where pipeline configuration
    files are located.
    """
    try:
        this_dir = pathlib.Path(configuration_dir)
        paths = PipelineConfigurationPaths(
            **{x: this_dir / y for x, y in DEFAULT_CONFIGURATION_FILES.items()}
        )
        PipelineConfiguration.from_files(paths)

        report_success("pipeline configuration validated")
    except PipelineConfigurationError as e:
        report_failure(str(e))
        sys.exit(ExitState.MISSING_GITREF.value)
    except Exception as e:
        report_failure("unknown error, {0}".format(str(e)))
        sys.exit(ExitState.UNKNOWN.value)


def flit_entry() -> None:
    """Flit script entry function for ``validate-configuration`` utility."""
    _main()
