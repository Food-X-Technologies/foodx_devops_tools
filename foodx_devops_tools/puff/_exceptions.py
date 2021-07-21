#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Puff related exceptions."""


class PuffError(Exception):
    """Problem with puff utility."""


class ArmTemplateError(PuffError):
    """Problem occurred with ARM template generation."""
