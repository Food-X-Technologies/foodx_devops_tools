#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Project internal exceptions."""


class GitReferenceError(Exception):
    """Problem with git reference."""


class ConfigurationPathsError(Exception):
    """Problem with configuration paths, or acquiring configuration."""
