#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

"""Console related reporting."""

import click


def report_success(message: str) -> None:
    """
    Report a success to console.

    The text "SUCCESS: " is pre-pended to the message for printing.

    Args:
        message: Success message to be reported.
    """
    click.echo(click.style("SUCCESS: {0}".format(message), fg="green"))


def report_failure(message: str) -> None:
    """
    Report a failure to console.

    The text "FAILURE: " is pre-pended to the message for printing.

    Args:
        message: Failure message to be reported.
    """
    click.echo(click.style("FAILURE: {0}".format(message), fg="red"), err=True)
