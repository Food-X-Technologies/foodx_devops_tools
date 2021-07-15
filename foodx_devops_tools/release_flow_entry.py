#!python3
# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Release flow utility."""

import sys
import typing

import click

from .console import report_failure
from .exceptions import GitReferenceError, ReleaseStateError
from .release_flow import ExitState, identify_release_state


def _main(command_line_arguments: typing.List[str]) -> None:
    """
    Primary execution path to extract release state from git reference.

    Report release state to stdout.

    Args:
        command_line_arguments: ``sys.argv`` style command line arguments.

    Raises:
        RuntimeError: If incorrect arguments are provided.
    """
    try:
        if len(command_line_arguments) != 2:
            raise GitReferenceError("git reference must be specified")

        state = identify_release_state(command_line_arguments[1])

        click.echo("{0}".format(state.name))
    except GitReferenceError as e:
        report_failure(str(e))
        sys.exit(ExitState.MISSING_GITREF)
    except ReleaseStateError as e:
        report_failure(str(e))
        sys.exit(ExitState.GITREF_PARSE_FAILURE)
    except Exception as e:
        report_failure("unknown error; {0}".format(str(e)))
        sys.exit(ExitState.UNKNOWN)


def flit_entry() -> None:
    """Flit script entry function for release_flow utility."""
    _main(sys.argv)
