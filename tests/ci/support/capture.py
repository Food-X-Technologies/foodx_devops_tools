# Copyright (c) 2021 Food-X Technologies
#
# This file is part of foodx_devops_tools.
#
# You should have received a copy of the MIT License along with
# foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import contextlib
import io
import sys


@contextlib.contextmanager
def capture_stdout_stderr(reset_seek: bool = True) -> None:
    new_stderr = io.StringIO()
    new_stdout = io.StringIO()
    with contextlib.redirect_stderr(
        new_stderr
    ) as err, contextlib.redirect_stdout(new_stdout) as out:
        yield out, err

    if reset_seek:
        # Reset the file pointer to the beginning of the stream.
        out.seek(0)
        err.seek(0)
