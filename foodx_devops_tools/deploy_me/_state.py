#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import dataclasses
import enum


@dataclasses.dataclass
class PipelineCliOptions:
    """Pipeline configuration options provided from CLI."""

    enable_validation: bool
    monitor_sleep_seconds: int
    wait_timeout_seconds: int


@enum.unique
class ExitState(enum.Enum):
    """Exit state definitions for ``deploy-me`` utility."""

    UNKNOWN_ERROR = 100
    BAD_CLI_ARGUMENTS = 101
    BAD_DEPLOYMENT_CONFIGURATION = 102
