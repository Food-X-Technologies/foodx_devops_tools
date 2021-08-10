#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pathlib


def initialize_filesystem(file_name: pathlib.Path, file_content: str):
    with file_name.open("w") as f:
        f.write(file_content)
