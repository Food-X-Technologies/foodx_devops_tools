#  Copyright (c) 2022 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import logging
import time

from foodx_devops_tools.profiling import timing

log = logging.getLogger(__name__)


def test_clean(mocker):
    mocker.patch(
        "foodx_devops_tools.profiling.time.monotonic", side_effect=[1.2, 3.5]
    )

    with timing(log, "some.context") as t:
        time.sleep(0.2)

    assert t.elapsed_time_seconds == 2.3
    assert t.elapsed_time_formatted == "0:00:02.300000"
