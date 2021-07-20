#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""ARM template parameters header."""

import typing

ARMTEMPLATE_PARAMETERS_HEADER: typing.Dict[str, typing.Any] = {
    "$schema": "https://schema.management.azure.com/schemas/2019-04-01"
    "/deploymentParameters.json#",
    "contentVersion": "1.0.0.0",
    "parameters": dict(),
}
