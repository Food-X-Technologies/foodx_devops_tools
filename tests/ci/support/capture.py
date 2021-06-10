import contextlib
import io
import sys


@contextlib.contextmanager
def capture_stdout_stderr():
    new_stderr = io.StringIO()
    new_stdout = io.StringIO()
    with contextlib.redirect_stderr(
        new_stderr
    ) as err, contextlib.redirect_stdout(new_stdout) as out:
        yield out, err
