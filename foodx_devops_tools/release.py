#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Declarations relating to release management."""

import enum


@enum.unique
class ReleaseState(enum.Enum):
    """Enumeration of release states."""

    ftr = enum.auto()
    dev = enum.auto()
    qa = enum.auto()
    stg = enum.auto()
    prd = enum.auto()
