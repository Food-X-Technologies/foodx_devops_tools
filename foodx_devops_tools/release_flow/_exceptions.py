#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Release flow package internal exceptions."""


class ReleaseIdentityError(Exception):
    """Problem parsing release id from git reference."""


class ReleaseStateError(Exception):
    """Problem parsing release state from git reference."""
