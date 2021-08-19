#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Manage deployment related exceptions."""


class DeploymentError(Exception):
    """Problem executing deployment."""


class DeploymentCancelledError(DeploymentError):
    """Deployment was cancelled due to failing dependencies."""
