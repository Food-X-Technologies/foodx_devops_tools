# https://gitlab.com/ci-cd-devops/build_harness/-/blob/feature/27-fix-main-test-publish/build_harness/commands/_logging.py
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

"""Logging configuration."""

import logging
import logging.handlers
import pathlib
import typing

import pydantic

from ._declarations import (
    DEFAULT_FILE_ROTATION_BACKUPS,
    DEFAULT_FILE_ROTATION_ENABLED,
    DEFAULT_FILE_ROTATION_SIZE_MB,
)

log = logging.getLogger(__name__)

T = typing.TypeVar("T", bound="LoggingState")


class LoggingConfiguration(pydantic.BaseModel):
    """Logging configuration data."""

    disable_file_logging: bool
    enable_console_logging: bool
    enable_file_rotation: bool
    file_rotation_size_megabytes: int
    log_file_path: typing.Optional[pathlib.Path]
    log_level: int
    max_rotation_backup_files: int


class LoggingState:
    """Logging configuration parameters."""

    configuration: LoggingConfiguration
    rotation_handler: typing.Optional[logging.handlers.RotatingFileHandler]

    def __init__(
        self: T,
        disable_file_logging: bool,
        enable_console_logging: bool,
        log_level_text: str,
        default_log_file: pathlib.Path,
    ) -> None:
        """
        Construct ``LoggingState`` object.

        Args:
            disable_file_logging: Disable file logging flag.
            enable_console_logging: Enable console logging flag.
        """
        self.configuration = LoggingConfiguration(
            **{
                "disable_file_logging": disable_file_logging,
                "enable_console_logging": enable_console_logging,
                "enable_file_rotation": DEFAULT_FILE_ROTATION_ENABLED,
                "file_rotation_size_megabytes": DEFAULT_FILE_ROTATION_SIZE_MB,
                "log_file_path": (
                    default_log_file if not disable_file_logging else None
                ),
                "log_level": getattr(logging, log_level_text.upper()),
                "max_rotation_backup_files": DEFAULT_FILE_ROTATION_BACKUPS,
            }
        )
        self.rotation_handler = None

        self.set_logging_state()

    def set_logging_state(self: T) -> None:
        """Apply the logging state from configured parameters."""
        root_logger = logging.getLogger()
        self.__set_log_level(root_logger)
        self.__set_file_logging(root_logger)
        self.__set_console_logging(root_logger)

        log.info("Logging state set")
        log.debug(
            "Applied logging configuration, {0}".format(
                self.configuration.dict()
            )
        )

    def __set_file_logging(self: T, root_logger: logging.Logger) -> None:
        """
        Enable or disable file logging.

        Args:
            root_logger: Root logger to modify.
        """
        if not self.configuration.disable_file_logging:
            # No change if a rotation handler already exists.
            if not self.rotation_handler:
                this_handler = logging.handlers.RotatingFileHandler(
                    str(self.configuration.log_file_path),
                    backupCount=self.configuration.max_rotation_backup_files,
                    maxBytes=self.configuration.file_rotation_size_megabytes
                    * (1024 ** 2),
                )
                this_handler.setLevel(self.configuration.log_level)
                self.rotation_handler = this_handler

                root_logger.addHandler(self.rotation_handler)
        elif self.rotation_handler:
            root_logger.removeHandler(self.rotation_handler)
            self.rotation_handler = None
        # else self.rotation_handler is None and self.disable_file_logging
        # so do nothing

    def __set_console_logging(self: T, root_logger: logging.Logger) -> None:
        """
        Enable or disable console logging.

        Args:
            root_logger: Root logger to modify.
        """

        def remove_stream_handlers() -> None:
            for this_handler in root_logger.handlers:
                if type(this_handler) == logging.StreamHandler:
                    root_logger.removeHandler(this_handler)

        remove_stream_handlers()
        if self.configuration.enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.configuration.log_level)

            root_logger.addHandler(console_handler)

    def __set_log_level(self: T, root_logger: logging.Logger) -> None:
        """
        Set log level on any existing handlers.

        Args:
            root_logger: Root logger to modify.
        """
        for this_handler in root_logger.handlers:
            this_handler.setLevel(self.configuration.log_level)
        # Ensure that the logging level propagates to any subsequently
        # created handlers.
        root_logger.setLevel(self.configuration.log_level)
