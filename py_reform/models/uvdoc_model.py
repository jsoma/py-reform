"""
UVDoc model for document dewarping.

This implementation is based on the UVDoc paper and code:
https://github.com/tanguymagne/UVDoc/ (MIT License)

Citation:
@inproceedings{UVDoc,
title={{UVDoc}: Neural Grid-based Document Unwarping},
author={Floor Verhoeven and Tanguy Magne and Olga Sorkine-Hornung},
booktitle = {SIGGRAPH ASIA, Technical Papers},
year = {2023},
url={https://doi.org/10.1145/3610548.3618174}
}
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
import PIL.Image
from PIL import ImageOps

from py_reform.models.base import DewarpingModel

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

# Default model parameters
DEFAULT_IMG_SIZE = [488, 712]  # Width, Height
DEFAULT_GRID_SIZE = [45, 31]  # Width, Height
DEFAULT_MODEL_PATH = Path(__file__).parent / "weights" / "best_model.pkl"


def conv3x3(in_channels, out_channels, kernel_size, stride=1):
    """3x3 convolution with padding"""
    return nn.Conv2d(
        in_channels,
        out_channels,
        kernel_size=kernel_size,
        stride=stride,
        padding=kernel_size // 2,
    )


def dilated_conv_bn_act(in_channels, out_channels, act_fn, BatchNorm, dilation):
    """Dilated convolution with batch normalization and activation"""
    model = nn.Sequential(
        nn.Conv2d(
            in_channels,
            out_channels,
            bias=False,
            kernel_size=3,
            stride=1,
            padding=dilation,
            dilation=dilation,
        ),
        BatchNorm(out_channels),
        act_fn,
    )
    return model


def dilated_conv(in_channels, out_channels, kernel_size, dilation, stride=1):
    """Dilated convolution"""
    model = nn.Sequential(
        nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=dilation * (kernel_size // 2),
            dilation=dilation,
        )
    )
    return model


class ResidualBlockWithDilation(nn.Module):
    """Residual block with dilation"""

    def __init__(
        self,
        in_channels,
        out_channels,
        BatchNorm,
        kernel_size,
        stride=1,
        downsample=None,
        is_activation=True,
        is_top=False,
    ):
        super(ResidualBlockWithDilation, self).__init__()
        self.stride = stride
        self.downsample = downsample
        self.is_activation = is_activation
        self.is_top = is_top
        if self.stride != 1 or self.is_top:
            self.conv1 = conv3x3(in_channels, out_channels, kernel_size, self.stride)
            self.conv2 = conv3x3(out_channels, out_channels, kernel_size)
        else:
            self.conv1 = dilated_conv(
                in_channels, out_channels, kernel_size, dilation=3
            )
            self.conv2 = dilated_conv(
                out_channels, out_channels, kernel_size, dilation=3
            )

        self.bn1 = BatchNorm(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.bn2 = BatchNorm(out_channels)

    def forward(self, x):
        residual = x
        if self.downsample is not None:
            residual = self.downsample(x)

        out1 = self.relu(self.bn1(self.conv1(x)))
        out2 = self.bn2(self.conv2(out1))

        out2 += residual
        out = self.relu(out2)
        return out


class ResnetStraight(nn.Module):
    """ResNet backbone for UVDoc"""

    def __init__(
        self,
        num_filter,
        map_num,
        BatchNorm,
        block_nums=[3, 4, 6, 3],
        block=ResidualBlockWithDilation,
        kernel_size=5,
        stride=[1, 1, 2, 2],
    ):
        super(ResnetStraight, self).__init__()
        self.in_channels = num_filter * map_num[0]
        self.stride = stride
        self.relu = nn.ReLU(inplace=True)
        self.block_nums = block_nums
        self.kernel_size = kernel_size

        self.layer1 = self.blocklayer(
            block,
            num_filter * map_num[0],
            self.block_nums[0],
            BatchNorm,
            kernel_size=self.kernel_size,
            stride=self.stride[0],
        )
        self.layer2 = self.blocklayer(
            block,
            num_filter * map_num[1],
            self.block_nums[1],
            BatchNorm,
            kernel_size=self.kernel_size,
            stride=self.stride[1],
        )
        self.layer3 = self.blocklayer(
            block,
            num_filter * map_num[2],
            self.block_nums[2],
            BatchNorm,
            kernel_size=self.kernel_size,
            stride=self.stride[2],
        )

    def blocklayer(
        self, block, out_channels, block_nums, BatchNorm, kernel_size, stride=1
    ):
        downsample = None
        if (stride != 1) or (self.in_channels != out_channels):
            downsample = nn.Sequential(
                conv3x3(
                    self.in_channels,
                    out_channels,
                    kernel_size=kernel_size,
                    stride=stride,
                ),
                BatchNorm(out_channels),
            )

        layers = []
        layers.append(
            block(
                self.in_channels,
                out_channels,
                BatchNorm,
                kernel_size,
                stride,
                downsample,
                is_top=True,
            )
        )
        self.in_channels = out_channels
        for i in range(1, block_nums):
            layers.append(
                block(
                    out_channels,
                    out_channels,
                    BatchNorm,
                    kernel_size,
                    is_activation=True,
                    is_top=False,
                )
            )

        return nn.Sequential(*layers)

    def forward(self, x):
        out1 = self.layer1(x)
        out2 = self.layer2(out1)
        out3 = self.layer3(out2)
        return out3


class UVDocNet(nn.Module):
    """UVDoc neural network for document dewarping"""

    def __init__(self, num_filter, kernel_size=5):
        super(UVDocNet, self).__init__()
        self.num_filter = num_filter
        self.in_channels = 3
        self.kernel_size = kernel_size
        self.stride = [1, 2, 2, 2]

        BatchNorm = nn.BatchNorm2d
        act_fn = nn.ReLU(inplace=True)
        map_num = [1, 2, 4, 8, 16]

        self.resnet_head = nn.Sequential(
            nn.Conv2d(
                self.in_channels,
                self.num_filter * map_num[0],
                bias=False,
                kernel_size=self.kernel_size,
                stride=2,
                padding=self.kernel_size // 2,
            ),
            BatchNorm(self.num_filter * map_num[0]),
            act_fn,
            nn.Conv2d(
                self.num_filter * map_num[0],
                self.num_filter * map_num[0],
                bias=False,
                kernel_size=self.kernel_size,
                stride=2,
                padding=self.kernel_size // 2,
            ),
            BatchNorm(self.num_filter * map_num[0]),
            act_fn,
        )

        self.resnet_down = ResnetStraight(
            self.num_filter,
            map_num,
            BatchNorm,
            block_nums=[3, 4, 6, 3],
            block=ResidualBlockWithDilation,
            kernel_size=self.kernel_size,
            stride=self.stride,
        )

        map_num_i = 2
        self.bridge_1 = nn.Sequential(
            dilated_conv_bn_act(
                self.num_filter * map_num[map_num_i],
                self.num_filter * map_num[map_num_i],
                act_fn,
                BatchNorm,
                dilation=1,
            )
        )

        self.bridge_2 = nn.Sequential(
            dilated_conv_bn_act(
                self.num_filter * map_num[map_num_i],
                self.num_filter * map_num[map_num_i],
                act_fn,
                BatchNorm,
                dilation=2,
            )
        )

        self.bridge_3 = nn.Sequential(
            dilated_conv_bn_act(
                self.num_filter * map_num[map_num_i],
                self.num_filter * map_num[map_num_i],
                act_fn,
                BatchNorm,
                dilation=5,
            )
        )

        self.bridge_4 = nn.Sequential(
            *[
                dilated_conv_bn_act(
                    self.num_filter * map_num[map_num_i],
                    self.num_filter * map_num[map_num_i],
                    act_fn,
                    BatchNorm,
                    dilation=d,
                )
                for d in [8, 3, 2]
            ]
        )

        self.bridge_5 = nn.Sequential(
            *[
                dilated_conv_bn_act(
                    self.num_filter * map_num[map_num_i],
                    self.num_filter * map_num[map_num_i],
                    act_fn,
                    BatchNorm,
                    dilation=d,
                )
                for d in [12, 7, 4]
            ]
        )

        self.bridge_6 = nn.Sequential(
            *[
                dilated_conv_bn_act(
                    self.num_filter * map_num[map_num_i],
                    self.num_filter * map_num[map_num_i],
                    act_fn,
                    BatchNorm,
                    dilation=d,
                )
                for d in [18, 12, 6]
            ]
        )

        self.bridge_concat = nn.Sequential(
            nn.Conv2d(
                self.num_filter * map_num[map_num_i] * 6,
                self.num_filter * map_num[2],
                bias=False,
                kernel_size=1,
                stride=1,
                padding=0,
            ),
            BatchNorm(self.num_filter * map_num[2]),
            act_fn,
        )

        self.out_point_positions2D = nn.Sequential(
            nn.Conv2d(
                self.num_filter * map_num[2],
                self.num_filter * map_num[0],
                bias=False,
                kernel_size=self.kernel_size,
                stride=1,
                padding=self.kernel_size // 2,
                padding_mode="reflect",
            ),
            BatchNorm(self.num_filter * map_num[0]),
            nn.PReLU(),
            nn.Conv2d(
                self.num_filter * map_num[0],
                2,
                kernel_size=self.kernel_size,
                stride=1,
                padding=self.kernel_size // 2,
                padding_mode="reflect",
            ),
        )

        self.out_point_positions3D = nn.Sequential(
            nn.Conv2d(
                self.num_filter * map_num[2],
                self.num_filter * map_num[0],
                bias=False,
                kernel_size=self.kernel_size,
                stride=1,
                padding=self.kernel_size // 2,
                padding_mode="reflect",
            ),
            BatchNorm(self.num_filter * map_num[0]),
            nn.PReLU(),
            nn.Conv2d(
                self.num_filter * map_num[0],
                3,
                kernel_size=self.kernel_size,
                stride=1,
                padding=self.kernel_size // 2,
                padding_mode="reflect",
            ),
        )

        self._initialize_weights()

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.xavier_normal_(m.weight, gain=0.2)
            if isinstance(m, nn.ConvTranspose2d):
                assert m.kernel_size[0] == m.kernel_size[1]
                nn.init.xavier_normal_(m.weight, gain=0.2)

    def forward(self, x):
        resnet_head = self.resnet_head(x)
        resnet_down = self.resnet_down(resnet_head)
        bridge_1 = self.bridge_1(resnet_down)
        bridge_2 = self.bridge_2(resnet_down)
        bridge_3 = self.bridge_3(resnet_down)
        bridge_4 = self.bridge_4(resnet_down)
        bridge_5 = self.bridge_5(resnet_down)
        bridge_6 = self.bridge_6(resnet_down)
        bridge_concat = torch.cat(
            [bridge_1, bridge_2, bridge_3, bridge_4, bridge_5, bridge_6], dim=1
        )
        bridge = self.bridge_concat(bridge_concat)

        out_point_positions2D = self.out_point_positions2D(bridge)
        out_point_positions3D = self.out_point_positions3D(bridge)

        return out_point_positions2D, out_point_positions3D


def bilinear_unwarping(warped_img, point_positions, img_size):
    """
    Utility function that unwarps an image.
    Unwarp warped_img based on the 2D grid point_positions with a size img_size.

    Args:
        warped_img: torch.Tensor of shape BxCxHxW (dtype float)
        point_positions: torch.Tensor of shape Bx2xGhxGw (dtype float)
        img_size: tuple of int [w, h]
    """
    upsampled_grid = F.interpolate(
        point_positions,
        size=(img_size[1], img_size[0]),
        mode="bilinear",
        align_corners=True,
    )
    unwarped_img = F.grid_sample(
        warped_img, upsampled_grid.transpose(1, 2).transpose(2, 3), align_corners=True
    )

    return unwarped_img


class UVDocModel(DewarpingModel):
    """
    UVDoc model for document dewarping.

    This model uses a deep learning approach to predict UV maps for document dewarping.
    """

    def __init__(
        self,
        device: Optional[str] = None,
        model_path: Optional[Union[str, Path]] = None,
        img_size: Optional[Tuple[int, int]] = None,
        **kwargs,
    ):
        """
        Initialize the UVDoc model.

        Args:
            device: Device to run the model on ('cpu' or 'cuda'). If None, will use CUDA if available.
            model_path: Path to a pre-trained model file
            img_size: Input size for the model (width, height)
            **kwargs: Additional parameters
        """
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch is required for the UVDoc model. "
                "Install it with 'pip install torch'."
            )

        # Set device to CUDA if available and not explicitly set to CPU
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Convert model_path to Path if it's a string
        if model_path is not None:
            self.model_path = Path(model_path)
        else:
            self.model_path = DEFAULT_MODEL_PATH

        self.img_size = img_size or DEFAULT_IMG_SIZE

        # Initialize the model
        logger.info(f"Initializing UVDoc model from {self.model_path} on {self.device}")
        self._load_model()

    def _load_model(self):
        """Load the UVDoc model from the specified path."""
        device = torch.device(self.device)

        # Create the model
        self.model = UVDocNet(num_filter=32, kernel_size=5)

        # Load the weights
        try:
            checkpoint = torch.load(
                self.model_path, map_location=device, weights_only=True
            )

            # Handle different checkpoint formats
            if isinstance(checkpoint, dict) and "model_state" in checkpoint:
                state_dict = checkpoint["model_state"]
            elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]
            else:
                # Assume the checkpoint is the state dict itself
                state_dict = checkpoint

            self.model.load_state_dict(state_dict)
            self.model.to(device)
            self.model.eval()
            logger.info(f"Successfully loaded UVDoc model from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load UVDoc model: {e}")
            raise RuntimeError(f"Failed to load UVDoc model: {e}")

    def process(self, image: PIL.Image.Image) -> PIL.Image.Image:
        """
        Process an image to dewarp it using the UVDoc model.

        Args:
            image: The input image to dewarp

        Returns:
            The dewarped image
        """
        device = torch.device(self.device)

        # Convert PIL image to numpy array
        img_np = np.array(image)

        # Convert to RGB if grayscale or RGBA
        if len(img_np.shape) == 2:  # Grayscale
            # Convert grayscale to RGB using PIL
            image = image.convert("RGB")
            img_np = np.array(image)
        elif img_np.shape[2] == 4:  # RGBA
            # Convert RGBA to RGB using PIL
            image = image.convert("RGB")
            img_np = np.array(image)

        # Normalize to [0, 1]
        img_np = img_np.astype(np.float32) / 255.0

        # Resize for model input using PIL
        pil_resized = image.resize((self.img_size[0], self.img_size[1]), PIL.Image.Resampling.BILINEAR)
        inp_np = np.array(pil_resized).astype(np.float32) / 255.0
        inp = torch.from_numpy(inp_np.transpose(2, 0, 1)).unsqueeze(0).to(device)

        # Make prediction
        with torch.no_grad():
            point_positions2D, _ = self.model(inp)

        # Unwarp the image
        size = img_np.shape[:2][::-1]  # (width, height)
        img_tensor = torch.from_numpy(img_np.transpose(2, 0, 1)).unsqueeze(0).to(device)

        unwarped = bilinear_unwarping(
            warped_img=img_tensor,
            point_positions=torch.unsqueeze(point_positions2D[0], dim=0),
            img_size=size,
        )

        # Convert back to PIL image
        unwarped_np = (
            unwarped[0].detach().cpu().numpy().transpose(1, 2, 0) * 255
        ).astype(np.uint8)
        unwarped_pil = PIL.Image.fromarray(unwarped_np)

        return unwarped_pil
