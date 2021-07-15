#!python3
# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Axure CD release flow utility."""

import enum
import re
import sys

import click

from .._exceptions import GitReferenceError
from ..console import report_failure
from ..patterns import BRANCH_PREFIX, SEMANTIC_VERSION_GITREF, TAG_PREFIX
from ..release import ReleaseState

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


@click.command()
@click.argument(
    "git_reference",
    type=str,
)
def azure_subcommand(git_reference: str) -> None:
    """
    Extract Azure deployment release state from git reference.

    Report release state to stdout.
    """
    try:
        state = identify_release_state(git_reference)

        click.echo("{0}".format(state.name), nl=False)
    except GitReferenceError as e:
        report_failure(str(e))
        sys.exit(ExitState.MISSING_GITREF)
    except ReleaseStateError as e:
        report_failure(str(e))
        sys.exit(ExitState.GITREF_PARSE_FAILURE)
    except Exception as e:
        report_failure("unknown error; {0}".format(str(e)))
        sys.exit(ExitState.UNKNOWN)
