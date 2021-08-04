#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""
Azure cloud utilities.

Exports:

* AzureSubscriptionConfiguration class
* deploy_resource_group function
"""

from .model import AzureSubscriptionConfiguration  # noqa: F401
from .resource_group import deploy as deploy_resource_group  # noqa: F401
