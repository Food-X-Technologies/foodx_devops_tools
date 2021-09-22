#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools.patterns import SubscriptionData, SubscriptionNameError


def test_clean():
    name = "some_sub123scription_name"

    under_test = SubscriptionData.from_subscription_name(name)

    assert under_test.client == "sub123scription"
    assert under_test.system == "some"
    assert under_test.resource_suffix == "name"


EXPECTED_MESSAGE = r"^Subscription name does not conform to naming pattern"


def test_bad_raises1():
    name = "badname"

    with pytest.raises(SubscriptionNameError, match=EXPECTED_MESSAGE):
        SubscriptionData.from_subscription_name(name)


def test_bad_raises2():
    name = "not-valid-either"

    with pytest.raises(SubscriptionNameError, match=EXPECTED_MESSAGE):
        SubscriptionData.from_subscription_name(name)
