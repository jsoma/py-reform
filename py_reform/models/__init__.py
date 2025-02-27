"""
Models for document dewarping.
"""

from typing import Any, Dict

from py_reform.models.base import DewarpingModel
from py_reform.models.uvdoc_model import UVDocModel

# Registry of available models
MODEL_REGISTRY = {
    "uvdoc": UVDocModel,
    # Add more models here as they are implemented
    # "deep-learning": DeepLearningModel,
    # "opencv-contour": OpenCVContourModel,
    # "line-detection": LineDetectionModel,
}


def get_model(model_name: str, **model_params) -> DewarpingModel:
    """
    Factory function to get the appropriate dewarping model.

    Args:
        model_name: Name of the model to use
        **model_params: Parameters to pass to the model

    Returns:
        An instance of the requested dewarping model

    Raises:
        ValueError: If the requested model is not available
    """
    if model_name not in MODEL_REGISTRY:
        available_models = ", ".join(MODEL_REGISTRY.keys())
        raise ValueError(
            f"Model '{model_name}' not available. Choose from: {available_models}"
        )

    model_class = MODEL_REGISTRY[model_name]
    return model_class(**model_params)
