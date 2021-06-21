#!python3
# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Release id utility."""

import enum
import re
import sys
import typing

import click

from .console import report_failure
from .exceptions import GitReferenceError
from .patterns import SEMANTIC_VERSION_GITREF, TAG_PREFIX
from .release_flow import (
    ReleaseState,
    ReleaseStateError,
    identify_release_state,
)


@enum.unique
class ExitState(enum.Enum):
    """Release id utility CLI exit states."""

    UNKNOWN = 100
    MISSING_GITREF = 101
    GITREF_PARSE_FAILURE = 102


REGEX_TABLE = {
    ReleaseState.qa: r"^{0}(?P<id>{1}-alpha\.\d+)$".format(
        TAG_PREFIX, SEMANTIC_VERSION_GITREF
    ),
    ReleaseState.stg: r"^{0}(?P<id>{1}-beta\.\d+)$".format(
        TAG_PREFIX, SEMANTIC_VERSION_GITREF
    ),
    ReleaseState.prd: r"^{0}(?P<id>{1})$".format(
        TAG_PREFIX, SEMANTIC_VERSION_GITREF
    ),
}

ERROR_TEXT = "Unable to match git reference to any release id, {0}"


class ReleaseIdentityError(Exception):
    """Problem parsing release id from git reference."""


def identify_release_id(git_ref: str) -> str:
    """
    Parse git reference to extract release identity.

    Args:
        git_ref: git reference to parse

    Returns:
        Extracted release identity.
    Raises:
        ReleaseIdentityError: If no release id can be inferred.
    """
    try:
        state = identify_release_state(git_ref)

        found_id = False
        id_found = None
        if state in REGEX_TABLE:
            match_result = re.match(REGEX_TABLE[state], git_ref)
            if match_result is not None:
                found_id = True
                id_found = match_result.group("id")
        elif state in [ReleaseState.ftr, ReleaseState.dev]:
            # PEP-440 style "-post" convention should be valid for
            # https://semver.org/ compliant systems.
            found_id = True
            # WARNING: Placeholder! Needs to apply `git describe` to repo and
            # extract the correct attribute.
            id_found = "0.0.0-post.000"

        if (not found_id) or (not id_found):
            raise ReleaseIdentityError(ERROR_TEXT.format(git_ref))
    except ReleaseStateError as e:
        raise ReleaseIdentityError(ERROR_TEXT.format(git_ref)) from e

    return id_found


def _main(command_line_arguments: typing.List[str]) -> None:
    """
    Primary execution path to extract release id from git reference.

    Report release id to stdout.

    Args:
        command_line_arguments: ``sys.argv`` style command line arguments.

    Raises:
        RuntimeError: If incorrect arguments are provided.
    """
    try:
        if len(command_line_arguments) != 2:
            raise GitReferenceError("git reference must be specified")

        this_id = identify_release_id(command_line_arguments[1])
        click.echo("{0}".format(this_id))
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
    """Flit script entry function for release_id utility."""
    _main(sys.argv)
