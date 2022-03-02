#  Copyright (c) 2022 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import time

from foodx_devops_tools.profiling import timing


def test_clean(mocker):
    mocker.patch(
        "foodx_devops_tools.profiling.time.monotonic", side_effect=[1.2, 3.5]
    )

    with timing() as t:
        time.sleep(0.2)

    assert t.elapsed_time_seconds == 2.3
