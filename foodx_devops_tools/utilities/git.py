#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Git related utilities."""

from .command import run_command


def get_sha() -> str:
    """Get the git commit SHA of HEAD."""
    result = run_command(
        ["git", "rev-parse", "HEAD"], text=True, capture_output=True
    )

    if result.returncode != 0:
        raise RuntimeError("Git commit SHA acquisition failed")
    else:
        this_sha = result.stdout[0:10]

    return this_sha
