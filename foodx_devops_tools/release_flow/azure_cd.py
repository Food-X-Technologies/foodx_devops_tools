# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Azure CD release flow utility."""

import enum
import sys

import click

from foodx_devops_tools._version import acquire_version

from .._exceptions import GitReferenceError
from ..console import report_failure
from ._cd_release_id import identify_release_id
from ._cd_release_state import identify_release_state
from ._exceptions import ReleaseIdentityError, ReleaseStateError

COMMAND_OUTPUT_TYPES = [
    "id",
    "state",
]


@enum.unique
class ExitState(enum.Enum):
    """Release flow utility CLI exit states."""

    UNKNOWN = 100
    MISSING_GITREF = 101
    GITREF_PARSE_FAILURE = 102


def _do_release_state_actions(git_reference: str) -> None:
    """
    Process git reference to infer release state.

    Args:
        git_reference: Git reference to process.
    """
    state = identify_release_state(git_reference)
    click.echo("{0}".format(state.name), nl=False)


def _do_release_id_actions(git_reference: str) -> None:
    """
    Process git reference to infer release id.

    Args:
        git_reference: Git reference to process.
    """
    this_id = identify_release_id(git_reference)
    click.echo("{0}".format(this_id), nl=False)


COMMAND_ACTIONS = {
    "id": _do_release_id_actions,
    "state": _do_release_state_actions,
}


@click.command()
@click.version_option(acquire_version())
@click.argument(
    "output_type",
    type=click.Choice(COMMAND_OUTPUT_TYPES),
)
@click.argument(
    "git_reference",
    type=str,
)
def azure_subcommand(output_type: str, git_reference: str) -> None:
    """
    From git reference extract Azure deployment release state or release id.

    Report result to stdout.
    """
    try:
        COMMAND_ACTIONS[output_type](git_reference)
    except GitReferenceError as e:
        report_failure(str(e))
        sys.exit(ExitState.MISSING_GITREF)
    except (ReleaseStateError, ReleaseIdentityError) as e:
        report_failure(str(e))
        sys.exit(ExitState.GITREF_PARSE_FAILURE)
    except Exception as e:
        report_failure("unknown error; {0}".format(str(e)))
        sys.exit(ExitState.UNKNOWN)
