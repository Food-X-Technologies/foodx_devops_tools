#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""I/O related utilities."""

import typing


def acquire_token(password_file: typing.IO) -> str:
    """
    Read a password token from the specified stream.

    Args:
        password_file: Input file stream to read password token from.

    Returns:
        Read token.
    """
    with password_file:
        content = password_file.read()

    return content
