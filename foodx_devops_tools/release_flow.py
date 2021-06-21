#!python3
# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Release flow utility."""

import enum
import re
import sys
import typing

import click

from .console import report_failure
from .exceptions import GitReferenceError
from .patterns import BRANCH_PREFIX, SEMANTIC_VERSION_GITREF, TAG_PREFIX
from .release import ReleaseState

SEMANTIC_TAG_GITREF = r"{0}{1}".format(TAG_PREFIX, SEMANTIC_VERSION_GITREF)

REGEX_TABLE = {
    ReleaseState.ftr.name: r"^({0}feature/)|(refs/pull/)".format(BRANCH_PREFIX),
    ReleaseState.dev.name: r"^{0}main$".format(BRANCH_PREFIX),
    ReleaseState.qa.name: r"^{0}-alpha\.\d+$".format(SEMANTIC_TAG_GITREF),
    ReleaseState.stg.name: r"^{0}-beta\.\d+$".format(SEMANTIC_TAG_GITREF),
    ReleaseState.prd.name: r"^{0}$".format(SEMANTIC_TAG_GITREF),
}


@enum.unique
class ExitState(enum.Enum):
    """Release flow utility CLI exit states."""

    UNKNOWN = 100
    MISSING_GITREF = 101
    GITREF_PARSE_FAILURE = 102


class ReleaseStateError(Exception):
    """Problem parsing release state from git reference."""


def identify_release_state(git_ref: str) -> ReleaseState:
    """
    Parse git reference to map to release states.

    Args:
        git_ref: git reference to parse

    Returns:
        Parsed release state.
    Raises:
        ReleaseStateError: If no release state can be inferred.
    """
    found_state = False
    state_found = None
    for label, pattern in REGEX_TABLE.items():
        if re.match(pattern, git_ref) is not None:
            found_state = True
            state_found = ReleaseState[label]

    if (not found_state) or (not state_found):
        raise ReleaseStateError(
            "Unable to match git reference to any release state, {0}".format(
                git_ref
            )
        )

    return state_found


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
