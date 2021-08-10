#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.deployment import DeploymentTuple


def test_clean():
    under_test = DeploymentTuple(
        client="this_client", release_state="this_release", system="this_system"
    )


def test_str():
    under_test = DeploymentTuple(
        client="this_client", release_state="this_release", system="this_system"
    )

    assert str(under_test) == "this_system-this_client-this_release"
