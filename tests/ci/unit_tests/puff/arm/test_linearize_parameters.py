#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

from ruamel.yaml import YAML

from foodx_devops_tools.puff.arm import _linearize_parameters


class TestLinearizeParameters:
    def test_empty_environment(self):
        mock_base = {
            "p1": "bp1",
            "k2": "bk2",
            "environments": {
                "e1": dict(),
            },
        }
        expected_result = {
            "this.stub.e1": {
                "p1": "bp1",
                "k2": "bk2",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_environment_empty_region(self):
        mock_base = {
            "p1": "bp1",
            "k2": "bk2",
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "regions": [
                        {
                            "r1": dict(),
                        }
                    ],
                },
            },
        }
        expected_result = {
            "this.stub.e1.r1": {
                "p1": "e1p1",
                "k2": "bk2",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_environment_none_region(self):
        mock_base = {
            "p1": "bp1",
            "k2": "bk2",
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "regions": [
                        {
                            "r1": None,
                        }
                    ],
                },
            },
        }
        expected_result = {
            "this.stub.e1.r1": {
                "p1": "e1p1",
                "k2": "bk2",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_environment_empty_region_empty_base(self):
        mock_base = {
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "regions": [
                        {
                            "r1": dict(),
                        }
                    ],
                },
            },
        }
        expected_result = {
            "this.stub.e1.r1": {
                "p1": "e1p1",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_environment_none_region_empty_base(self):
        mock_base = {
            "environments": {
                "e1": {
                    "p1": "e1p1",
                    "regions": [
                        {
                            "r1": None,
                        }
                    ],
                },
            },
        }
        expected_result = {
            "this.stub.e1.r1": {
                "p1": "e1p1",
            },
        }
        result = _linearize_parameters(mock_base, "this.stub")

        assert result == expected_result

    def test_from_yaml(self):
        empty_region = """environments:
          e1:
            p1: e1p1
            p2: e1p2
            p3:
              p3p4: e1p3p4
              p3p5: e1p3p5
            p6: e1p6
            regions:
              - r1:
        """
        expected_result = {
            "this.stub.e1.r1": {
                "p1": "e1p1",
                "p2": "e1p2",
                "p3": {
                    "p3p4": "e1p3p4",
                    "p3p5": "e1p3p5",
                },
                "p6": "e1p6",
            },
        }
        yaml = YAML(typ="safe")
        yaml_data = yaml.load(empty_region)

        result = _linearize_parameters(yaml_data, "this.stub")

        assert result == expected_result
