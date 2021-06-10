#!python3

"""Release id utility."""

import re
import sys
import typing

from foodx_devops_tools.release_flow import (
    ReleaseState,
    ReleaseStateError,
    identify_release_state,
)

TAG_PREFIX = r"refs/tags/"
SEMANTIC_VERSION_GITREF = r"(\d+\.\d+\.\d+)"

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
    if len(command_line_arguments) != 2:
        raise RuntimeError("git reference must be specified")

    this_id = identify_release_id(command_line_arguments[1])
    print("{0}".format(this_id))


def flit_entry() -> None:
    """Flit script entry function for release_id utility."""
    _main(sys.argv)
