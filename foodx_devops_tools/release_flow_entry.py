#!python3
# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Release flow utility."""

from .release_flow import release_flow


def flit_entry() -> None:
    """Flit script entry function for ``foodx-release-flow`` utility."""
    release_flow()
