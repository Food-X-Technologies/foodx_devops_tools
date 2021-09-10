#!python3
# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Validation pipeline configuration data."""

import asyncio
import enum
import pathlib
import sys
import typing

import click

from ._version import acquire_version
from .console import report_failure, report_success
from .pipeline_config import (
    PipelineConfiguration,
    PipelineConfigurationPaths,
    do_path_check,
)
from .pipeline_config.exceptions import (
    ClientsDefinitionError,
    ConfigurationPathsError,
    DeploymentsDefinitionError,
    FrameDefinitionsError,
    PipelineConfigurationError,
    PipelineViewError,
    ReleaseStatesDefinitionError,
    SubscriptionsDefinitionError,
    SystemsDefinitionError,
    TenantsDefinitionError,
)
from .utilities import acquire_token


@enum.unique
class ExitState(enum.Enum):
    """Validate configuration script exit states."""

    UNKNOWN = 100
    MISSING_GITREF = 101
    GITREF_PARSE_FAILURE = 102
    BAD_CONFIGURATION_PATHS = 103


@click.command()
@click.version_option(acquire_version())
@click.argument(
    "client_path",
    type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
@click.argument(
    "system_path",
    type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
@click.argument(
    "password_file",
    type=click.File(mode="r"),
)
@click.option(
    "--check-paths",
    default=False,
    help="Check paths in configuration for file or directory existence.",
    is_flag=True,
)
@click.option(
    "--disable-vaults",
    default=False,
    help="""Disable encrypted file validation (local developer use only).

Disabling the validation still checks for the presence of the correct file,
but does not attempt to decrypt the contents for further validation in order
to avoid having to specify the decryption password.
""",
    is_flag=True,
)
def _main(
    client_path: pathlib.Path,
    system_path: pathlib.Path,
    password_file: typing.IO,
    check_paths: bool,
    disable_vaults: bool,
) -> None:
    """
    Validate pipeline configuration files.

    Exits non-zero if validation fails. Without the ``--check-paths`` option
    the utility loads the configuration to check for self-consistency of the
    data. In this case the release state does not need to be known.

    With the ``--check-paths`` option, the utility iterates over the release
    states configured for the client to check that all arm template and arm
    templates parameter files are in the expected locations unless the
    ``--git-ref`` option is also specified. In this case the check path tests
    only apply to the release state implied by the git ref.

    If ``--disable-sp`` is NOT specified the client service principal vault
    decryption password must be piped via stdin using an ``echo`` or ``cat``
    command.

    CLIENT_PATH:  The path to the directory where client files are located.
    SYSTEM_PATH:  The path to the directory where system files are located.
    PASSWORD_FILE:  The path to a file where the service principal decryption
                    password is stored, or "-" for stdin.
    """
    try:
        client_config = client_path / "configuration"
        system_config = system_path / "configuration"
        configuration_paths = PipelineConfigurationPaths.from_paths(
            client_config, system_config
        )

        decrypt_token = None
        if not disable_vaults:
            decrypt_token = acquire_token(password_file)

        pipeline_configuration = PipelineConfiguration.from_files(
            configuration_paths, decrypt_token
        )

        if check_paths:
            asyncio.run(do_path_check(pipeline_configuration, system_path))

        report_success("pipeline configuration validated")
    except FileNotFoundError as e:
        report_failure(str(e))
        sys.exit(ExitState.BAD_CONFIGURATION_PATHS.value)
    except ConfigurationPathsError as e:
        report_failure(str(e))
        sys.exit(ExitState.BAD_CONFIGURATION_PATHS.value)
    except PipelineConfigurationError as e:
        report_failure(str(e))
        sys.exit(ExitState.MISSING_GITREF.value)
    except (
        PipelineConfigurationError,
        ClientsDefinitionError,
        DeploymentsDefinitionError,
        FrameDefinitionsError,
        ReleaseStatesDefinitionError,
        SubscriptionsDefinitionError,
        SystemsDefinitionError,
        TenantsDefinitionError,
        PipelineViewError,
    ) as e:
        report_failure("Configuration schema error, {0}".format(e))
        sys.exit(ExitState.BAD_CONFIGURATION_PATHS.value)
    except Exception as e:
        report_failure("unknown error, {0}".format(str(e)))
        sys.exit(ExitState.UNKNOWN.value)


def flit_entry() -> None:
    """Flit script entry function for ``validate-configuration`` utility."""
    _main()
