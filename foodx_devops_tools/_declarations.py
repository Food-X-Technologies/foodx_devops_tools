# https://gitlab.com/ci-cd-devops/build_harness/-/blob/feature/27-fix-main-test-publish/build_harness/commands/_declarations.py
#  Copyright (c) 2021 Russell Smiley
#
#  This file is part of build_harness.
#
#  You should have received a copy of the MIT License along with build_harness.
#  If not, see <https://opensource.org/licenses/MIT>.

#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Common constants for command definitions."""

DEFAULT_CONSOLE_LOGGING_ENABLED = False
DEFAULT_FILE_LOGGING_DISABLED = False
DEFAULT_FILE_ROTATION_BACKUPS = 10
DEFAULT_FILE_ROTATION_ENABLED = True
DEFAULT_FILE_ROTATION_SIZE_MB = 1

DEFAULT_LOG_LEVEL = "warning"
VALID_LOG_LEVELS = ["critical", "error", "warning", "info", "debug", "notset"]
