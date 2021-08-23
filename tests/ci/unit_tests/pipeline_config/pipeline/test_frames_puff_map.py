#  Copyright (c) 2021 Food-X Technologies
#
#  This file is part of foodx_devops_tools.
#
#  You should have received a copy of the MIT License along with
#  foodx_devops_tools. If not, see <https://opensource.org/licenses/MIT>.

import logging

import pytest

from foodx_devops_tools.pipeline_config import (
    FramesDefinition,
    PipelineConfiguration,
    PuffMapGeneratedFiles,
    ReleaseStatesDefinition,
)
from foodx_devops_tools.pipeline_config.exceptions import (
    PipelineConfigurationError,
)
from tests.ci.support.pipeline_config import MOCK_PATHS

log = logging.getLogger(__name__)


def test_mismatched_frames_raises1(mock_loads, mock_results):
    mock_results.frames = FramesDefinition.parse_obj(
        {
            "frames": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": [
                                {
                                    "resource_group": "a1_group",
                                    "name": "a1stp1",
                                    "mode": "Incremental",
                                },
                            ],
                        },
                        "folder": "some/path",
                    },
                },
            },
        }
    ).frames
    mock_results.puff_map = PuffMapGeneratedFiles.parse_obj(
        {
            "puff_map": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": {
                                "arm_parameters_files": {
                                    "r1": {
                                        "sub1": {
                                            "a1stp1": "some/path/puff1.json"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "f2": {
                        "applications": {
                            "a2": {
                                "arm_parameters_files": {
                                    "r1": {
                                        "sub1": {
                                            "a2stp1": "some/path/puff1.json"
                                        }
                                    }
                                }
                            }
                        }
                    },
                },
            },
        }
    ).puff_map
    mock_loads(mock_results)

    with pytest.raises(
        PipelineConfigurationError,
        match=r"Frame definitions mismatch between frames and puff map",
    ):
        PipelineConfiguration.from_files(MOCK_PATHS)


def test_mismatched_frames_raises2(mock_loads, mock_results):
    mock_results.frames = FramesDefinition.parse_obj(
        {
            "frames": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": [
                                {
                                    "resource_group": "a1_group",
                                    "name": "a1stp1",
                                    "mode": "Incremental",
                                },
                            ],
                        },
                        "folder": "some/path",
                    },
                    "f2": {
                        "applications": {
                            "a2": [
                                {
                                    "resource_group": "a2_group",
                                    "name": "a2stp1",
                                    "mode": "Incremental",
                                },
                            ],
                        },
                        "folder": "some/path",
                    },
                },
            },
        }
    ).frames
    mock_results.puff_map = PuffMapGeneratedFiles.parse_obj(
        {
            "puff_map": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": {
                                "arm_parameters_files": {
                                    "r1": {
                                        "sub1": {
                                            "a1stp1": "some/path/puff1.json"
                                        }
                                    }
                                }
                            }
                        }
                    },
                },
            },
        }
    ).puff_map
    mock_loads(mock_results)

    with pytest.raises(
        PipelineConfigurationError,
        match=r"Frame definitions mismatch between frames and puff map",
    ):
        PipelineConfiguration.from_files(MOCK_PATHS)


def test_mismatched_applications_raises1(mock_loads, mock_results):
    mock_results.frames = FramesDefinition.parse_obj(
        {
            "frames": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": [
                                {
                                    "resource_group": "a1_group",
                                    "name": "a1stp1",
                                    "mode": "Incremental",
                                },
                            ],
                        },
                        "folder": "some/path",
                    },
                },
            },
        }
    ).frames
    mock_results.puff_map = PuffMapGeneratedFiles.parse_obj(
        {
            "puff_map": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": {
                                "arm_parameters_files": {
                                    "r1": {
                                        "sub1": {
                                            "a1stp1": "some/path/puff1.json"
                                        }
                                    }
                                }
                            },
                            "a2": {
                                "arm_parameters_files": {
                                    "r1": {
                                        "sub1": {
                                            "a2stp1": "some/path/puff1.json"
                                        }
                                    }
                                }
                            },
                        }
                    },
                },
            },
        }
    ).puff_map
    mock_loads(mock_results)

    with pytest.raises(
        PipelineConfigurationError,
        match=r"Application definitions mismatch between frames and puff "
        r"map",
    ):
        PipelineConfiguration.from_files(MOCK_PATHS)


def test_mismatched_applications_raises2(mock_loads, mock_results):
    mock_results.frames = FramesDefinition.parse_obj(
        {
            "frames": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": [
                                {
                                    "resource_group": "a1_group",
                                    "name": "a1stp1",
                                    "mode": "Incremental",
                                },
                            ],
                            "a2": [
                                {
                                    "resource_group": "a2_group",
                                    "name": "a2stp1",
                                    "mode": "Incremental",
                                },
                            ],
                        },
                        "folder": "some/path",
                    },
                },
            },
        }
    ).frames
    mock_results.puff_map = PuffMapGeneratedFiles.parse_obj(
        {
            "puff_map": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": {
                                "arm_parameters_files": {
                                    "r1": {
                                        "sub1": {
                                            "a1stp1": "some/path/puff1.json"
                                        }
                                    }
                                }
                            },
                        }
                    },
                },
            },
        }
    ).puff_map
    mock_loads(mock_results)

    with pytest.raises(
        PipelineConfigurationError,
        match=r"Application definitions mismatch between frames and puff "
        r"map",
    ):
        PipelineConfiguration.from_files(MOCK_PATHS)


def test_bad_puff_map_release_state_raises(mock_loads, mock_results):
    mock_results.frames = FramesDefinition.parse_obj(
        {
            "frames": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": [
                                {
                                    "resource_group": "a1_group",
                                    "name": "a1stp1",
                                    "mode": "Incremental",
                                },
                            ],
                        },
                        "folder": "some/path",
                    },
                },
            },
        }
    ).frames
    mock_results.puff_map = PuffMapGeneratedFiles.parse_obj(
        {
            "puff_map": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": {
                                "arm_parameters_files": {
                                    "bad_state": {
                                        "sub1": {
                                            "a1stp1": "some/path/puff1.json"
                                        }
                                    }
                                }
                            },
                        }
                    },
                },
            },
        }
    ).puff_map
    mock_loads(mock_results)

    with pytest.raises(
        PipelineConfigurationError, match=r"Bad release state in puff map"
    ):
        PipelineConfiguration.from_files(MOCK_PATHS)


def test_bad_puff_map_subscription_raises(mock_loads, mock_results):
    mock_results.frames = FramesDefinition.parse_obj(
        {
            "frames": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": [
                                {
                                    "resource_group": "a1_group",
                                    "name": "a1stp1",
                                    "mode": "Incremental",
                                },
                            ],
                        },
                        "folder": "some/path",
                    },
                },
            },
        }
    ).frames
    mock_results.puff_map = PuffMapGeneratedFiles.parse_obj(
        {
            "puff_map": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": {
                                "arm_parameters_files": {
                                    "r1": {
                                        "bad_sub": {
                                            "a1stp1": "some/path/puff1.json"
                                        }
                                    }
                                }
                            },
                        }
                    },
                },
            },
        }
    ).puff_map
    mock_loads(mock_results)

    with pytest.raises(
        PipelineConfigurationError, match=r"Bad subscription in puff map"
    ):
        PipelineConfiguration.from_files(MOCK_PATHS)


def test_missing_application_step_raises1(mock_loads, mock_results):
    mock_results.frames = FramesDefinition.parse_obj(
        {
            "frames": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": [
                                {
                                    "resource_group": "a1_group",
                                    "name": "a1stp1",
                                    "mode": "Incremental",
                                },
                                {
                                    "resource_group": "a1_group",
                                    "name": "a1stp2",
                                    "mode": "Incremental",
                                },
                            ],
                        },
                        "folder": "some/path",
                    },
                },
            },
        }
    ).frames
    mock_results.puff_map = PuffMapGeneratedFiles.parse_obj(
        {
            "puff_map": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": {
                                "arm_parameters_files": {
                                    "r1": {
                                        "sub1": {
                                            "a1stp2": "some/path/puff1.json"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }
    ).puff_map
    mock_loads(mock_results)

    with pytest.raises(
        PipelineConfigurationError,
        match=r"Application step name mismatch between frames and puff map",
    ):
        PipelineConfiguration.from_files(MOCK_PATHS)


def test_missing_application_step_raises2(mock_loads, mock_results):
    mock_results.frames = FramesDefinition.parse_obj(
        {
            "frames": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": [
                                {
                                    "resource_group": "a1_group",
                                    "name": "a1stp2",
                                    "mode": "Incremental",
                                },
                            ],
                        },
                        "folder": "some/path",
                    },
                },
            },
        }
    ).frames
    mock_results.puff_map = PuffMapGeneratedFiles.parse_obj(
        {
            "puff_map": {
                "frames": {
                    "f1": {
                        "applications": {
                            "a1": {
                                "arm_parameters_files": {
                                    "r1": {
                                        "sub1": {
                                            "a1stp1": "some/path/puff1.json",
                                            "a1stp2": "some/path/puff2.json",
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }
    ).puff_map
    mock_loads(mock_results)

    with pytest.raises(
        PipelineConfigurationError,
        match=r"Application step name mismatch between frames and puff map",
    ):
        PipelineConfiguration.from_files(MOCK_PATHS)
