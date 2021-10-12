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
import logging
import pathlib
import sys
import traceback
import typing

import click

from ._declarations import (
    DEFAULT_CONSOLE_LOGGING_ENABLED,
    DEFAULT_FILE_LOGGING_DISABLED,
    DEFAULT_LOG_LEVEL,
    VALID_LOG_LEVELS,
)
from ._logging import LoggingState
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

log = logging.getLogger(__name__)

DEFAULT_LOG_FILE = pathlib.Path("validate_configuration.log")


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
@click.option(
    "--log-disable-file",
    "disable_file_log",
    default=DEFAULT_FILE_LOGGING_DISABLED,
    help="Disable file logging.",
    is_flag=True,
)
@click.option(
    "--log-enable-console",
    "enable_console_log",
    default=DEFAULT_CONSOLE_LOGGING_ENABLED,
    help="Log to console.",
    is_flag=True,
)
@click.option(
    "--log-level",
    "log_level",
    default=DEFAULT_LOG_LEVEL,
    help="Select logging level to apply to all enabled log sinks.",
    show_default=True,
    type=click.Choice(VALID_LOG_LEVELS, case_sensitive=False),
)
def _main(
    client_path: pathlib.Path,
    system_path: pathlib.Path,
    password_file: typing.IO,
    check_paths: bool,
    disable_vaults: bool,
    disable_file_log: bool,
    enable_console_log: bool,
    log_level: str,
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
    log_file = DEFAULT_LOG_FILE
    try:
        # currently no need to change logging configuration at run time,
        # so no need to preserve the object.
        LoggingState(
            disable_file_logging=disable_file_log,
            enable_console_logging=enable_console_log,
            log_level_text=log_level,
            default_log_file=log_file,
        )

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
            asyncio.run(do_path_check(pipeline_configuration))

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
        this_traceback = traceback.format_exc()
        log.debug(this_traceback)
        report_failure(
            "unknown error, {0}. See log for more details, "
            "{1}.".format(str(e), log_file.resolve())
        )
        sys.exit(ExitState.UNKNOWN.value)


def flit_entry() -> None:
    """Flit script entry function for ``validate-configuration`` utility."""
    _main()
