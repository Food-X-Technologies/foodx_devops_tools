#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import re

from ..patterns import BRANCH_PREFIX, SEMANTIC_VERSION_GITREF, TAG_PREFIX
from ..release import ReleaseState
from ._exceptions import ReleaseStateError

SEMANTIC_TAG_GITREF = r"{0}{1}".format(TAG_PREFIX, SEMANTIC_VERSION_GITREF)

REGEX_TABLE = {
    ReleaseState.ftr.name: r"^({0}feature/)|(refs/pull/)".format(BRANCH_PREFIX),
    ReleaseState.dev.name: r"^{0}main$".format(BRANCH_PREFIX),
    ReleaseState.qa.name: r"^{0}-alpha\.\d+$".format(SEMANTIC_TAG_GITREF),
    ReleaseState.stg.name: r"^{0}-beta\.\d+$".format(SEMANTIC_TAG_GITREF),
    ReleaseState.prd.name: r"^{0}$".format(SEMANTIC_TAG_GITREF),
}


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
