#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import pytest

from foodx_devops_tools._to import StructuredTo, StructuredToError


def test_default():
    under_test = StructuredTo()

    assert under_test.frame is None
    assert under_test.application is None
    assert under_test.step is None


class TestFromSpecifier:
    def test_all_clean(self):
        under_test = StructuredTo.from_specifier(
            "this_frame.this_application.this_step"
        )

        assert under_test.frame == "this_frame"
        assert under_test.application == "this_application"
        assert under_test.step == "this_step"

    def test_missing_application_clean(self):
        under_test = StructuredTo.from_specifier("this_frame")

        assert under_test.frame == "this_frame"
        assert under_test.application is None
        assert under_test.step is None

    def test_missing_range_clean(self):
        under_test = StructuredTo.from_specifier("this_frame.this_application")

        assert under_test.frame == "this_frame"
        assert under_test.application == "this_application"
        assert under_test.step is None

    def test_none_specifier_default(self):
        under_test = StructuredTo.from_specifier(None)

        assert under_test.frame is None
        assert under_test.application is None
        assert under_test.step is None

    def test_bad_specifier_raises(self):
        with pytest.raises(
            StructuredToError, match=r"^Bad structured deployment specifier"
        ):
            StructuredTo.from_specifier("bad&specifier")
