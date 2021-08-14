#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from foodx_devops_tools.puff.arm import _linearize_regions


class TestLinearizedRegions:
    def test_regions(self):
        mock_base = {
            "this.stub": {
                "k1": "bk1",
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
        }
        expected_result = {
            "this.stub.r1": {
                "region": "r1",
                "k1": "e1r1k1",
            },
            "this.stub.r2": {
                "region": "r2",
                "k1": "bk1",
                "k2": "e1r2k2",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_multiple_stubs_mixed_regions(self):
        mock_base = {
            "stub1": {
                "k1": "stub1.k1",
                # "full" region in a stub
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
            "stub2": {
                "k1": "stub2.k1",
                # empty regions in a stub
                "regions": list(),
            },
        }
        expected_result = {
            "stub1.r1": {
                "region": "r1",
                "k1": "e1r1k1",
            },
            "stub1.r2": {
                "region": "r2",
                "k1": "stub1.k1",
                "k2": "e1r2k2",
            },
            "stub2": {
                "k1": "stub2.k1",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_empty_regions(self):
        mock_base = {
            "this.stub": {
                "k1": "bk1",
                "regions": list(),
            },
        }
        expected_result = {
            "this.stub": {
                "k1": "bk1",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_empty_region(self):
        mock_base = {
            "this.stub": {
                "k1": "bk1",
                "regions": [
                    {"r1": dict()},
                ],
            },
        }
        expected_result = {
            "this.stub.r1": {
                "region": "r1",
                "k1": "bk1",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_none_region(self):
        mock_base = {
            "this.stub": {
                "k1": "bk1",
                "regions": [
                    {"r1": None},
                ],
            },
        }
        expected_result = {
            "this.stub.r1": {
                "region": "r1",
                "k1": "bk1",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_no_regions(self):
        mock_base = {
            "this.stub": {
                "k1": "bk1",
            },
        }
        expected_result = {
            "this.stub": {
                "k1": "bk1",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_regions_empty_base(self):
        mock_base = {
            "this.stub": {
                "regions": [
                    {"r1": {"k1": "e1r1k1"}},
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
        }
        expected_result = {
            "this.stub.r1": {
                "region": "r1",
                "k1": "e1r1k1",
            },
            "this.stub.r2": {
                "region": "r2",
                "k2": "e1r2k2",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_no_regions_empty_base(self):
        mock_base = {
            "this.stub": dict(),
        }
        expected_result = {
            "this.stub": dict(),
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_merged_regions(self):
        mock_base = {
            "this.stub": {
                "k1": "bk1",
                "regions": [
                    # regions merged from other iterables (services or
                    # environments).
                    {"r1": {"k1": "e1r1k1"}},
                    {"r1": {"k2": "e2r1k2"}},
                    {"r1": {"k3": "e3r1k3"}},
                    {"r2": {"k4": "e1r2k2"}},
                    {"r2": {"k5": "e2r2k3"}},
                ],
            },
        }
        expected_result = {
            "this.stub.r1": {
                "region": "r1",
                "k1": "e1r1k1",
                "k2": "e2r1k2",
                "k3": "e3r1k3",
            },
            "this.stub.r2": {
                "region": "r2",
                "k1": "bk1",
                "k4": "e1r2k2",
                "k5": "e2r2k3",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result

    def test_none_regions(self):
        mock_base = {
            "this.stub": {
                "k1": "bk1",
                "regions": [
                    None,
                    {"r2": {"k2": "e1r2k2"}},
                ],
            },
        }
        expected_result = {
            "this.stub.r2": {
                "region": "r2",
                "k1": "bk1",
                "k2": "e1r2k2",
            },
        }
        result = _linearize_regions(mock_base)

        assert result == expected_result
