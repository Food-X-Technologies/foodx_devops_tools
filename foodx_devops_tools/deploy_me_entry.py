#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Azure deployment utility."""

from .deploy_me import deploy_me


def flit_entry() -> None:
    """Flit script entry function for ``deploy-me`` utility."""
    deploy_me()
