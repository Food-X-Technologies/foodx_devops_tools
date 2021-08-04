#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Azure data model definitions."""

import dataclasses
import typing


@dataclasses.dataclass()
class AzureSubscriptionConfiguration:
    """Base Azure subscription details for resource deployments."""

    subscription_id: str
    tenant_id: typing.Optional[str] = None
