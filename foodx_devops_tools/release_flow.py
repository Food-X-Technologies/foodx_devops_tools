#!python3

"""Release flow utility."""

import enum
import re
import sys
import typing


@enum.unique
class ReleaseState(enum.Enum):
    """Enumeration of release states."""

    ftr = enum.auto()
    dev = enum.auto()
    qa = enum.auto()
    stg = enum.auto()
    prd = enum.auto()


SEMANTIC_VERSION_GITREF = r"refs/tags/(\d+\.\d+\.\d+)"

REGEX_TABLE = {
    ReleaseState.ftr.name: r"^(refs/heads/feature/)|(refs/pull/)",
    ReleaseState.dev.name: r"^refs/heads/main$",
    ReleaseState.qa.name: r"^{0}-alpha\.\d+$".format(SEMANTIC_VERSION_GITREF),
    ReleaseState.stg.name: r"^{0}-beta\.\d+$".format(SEMANTIC_VERSION_GITREF),
    ReleaseState.prd.name: r"^{0}$".format(SEMANTIC_VERSION_GITREF),
}


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
    if len(command_line_arguments) != 2:
        raise RuntimeError("git reference must be specified")

    state = identify_release_state(command_line_arguments[1])
    print("{0}".format(state.name))


def flit_entry() -> None:
    """Flit script entry function for release_flow utility."""
    _main(sys.argv)
