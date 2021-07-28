#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""
Publically exported exceptions.

Exports:

* ResourceError
* ResourceGroupError
"""

from .resource import ResourceError  # noqa: F401
from .resource_group import ResourceGroupError  # noqa: F401
