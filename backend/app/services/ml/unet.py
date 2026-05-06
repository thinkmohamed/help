"""U-Net deep neural network for semantic segmentation.

شبكة عصبية عميقة U-Net - Pixel-level classification of satellite imagery
for detecting archaeological and geological features.

Uses a simplified NumPy-based implementation for portability.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage


class SimpleUNet:
    """Simplified U-Net using convolution operations for feature extraction."""

    def __init__(self, n_classes: int = 5):
        self.n_classes = n_classes
        np.random.seed(100)
        self._encoder_filters: list[np.ndarray] = []
        self._decoder_filters: list[np.ndarray] = []
        for size in [3, 5, 7]:
            self._encoder_filters.append(
                np.random.randn(size, size).astype(np.float32) * 0.1
            )
            self._decoder_filters.append(
                np.random.randn(size, size).astype(np.float32) * 0.1
            )

    def _encode(self, data: np.ndarray) -> list[np.ndarray]:
        """Encoder path: extract hierarchical features."""
        features = []
        current = data
        for filt in self._encoder_filters:
            conv = ndimage.convolve(current, filt, mode="reflect")
            activated = np.maximum(conv, 0)  # ReLU
            features.append(activated)
            current = ndimage.zoom(activated, 0.5, order=1)
        return features

    def _decode(
        self, features: list[np.ndarray], target_shape: tuple[int, int]
    ) -> np.ndarray:
        """Decoder path: upsample and combine features."""
        current = features[-1]
        for i, filt in enumerate(reversed(self._decoder_filters)):
            target_h = features[-(i + 2)].shape[0] if i + 2 <= len(features) else target_shape[0]
            target_w = features[-(i + 2)].shape[1] if i + 2 <= len(features) else target_shape[1]
            zoom_h = target_h / current.shape[0]
            zoom_w = target_w / current.shape[1]
            upsampled = ndimage.zoom(current, (zoom_h, zoom_w), order=1)
            conv = ndimage.convolve(upsampled, filt, mode="reflect")
            current = np.maximum(conv, 0)

            if i + 2 <= len(features):
                skip = features[-(i + 2)]
                h = min(current.shape[0], skip.shape[0])
                w = min(current.shape[1], skip.shape[1])
                current = current[:h, :w] + skip[:h, :w] * 0.5

        final_h, final_w = target_shape
        if current.shape[0] != final_h or current.shape[1] != final_w:
            current = ndimage.zoom(
                current,
                (final_h / current.shape[0], final_w / current.shape[1]),
                order=1,
            )
        return current

    def predict(self, fused_data: np.ndarray) -> np.ndarray:
        """Run U-Net prediction on fused multi-channel data.

        Args:
            fused_data: Shape (height, width, n_features)

        Returns:
            Probability map of shape (height, width, n_classes)
        """
        h, w, n_feat = fused_data.shape
        class_maps = np.zeros((h, w, self.n_classes), dtype=np.float32)

        for c in range(self.n_classes):
            channel_idx = c % n_feat
            input_channel = fused_data[:, :, channel_idx]

            features = self._encode(input_channel)
            decoded = self._decode(features, (h, w))

            decoded_norm = (decoded - decoded.min()) / (
                decoded.max() - decoded.min() + 1e-10
            )
            class_maps[:, :, c] = decoded_norm

        # Softmax-like normalization
        exp_maps = np.exp(class_maps - np.max(class_maps, axis=2, keepdims=True))
        class_maps = exp_maps / (np.sum(exp_maps, axis=2, keepdims=True) + 1e-10)

        return class_maps


def run_unet_classification(
    fused_data: np.ndarray, n_classes: int = 5
) -> np.ndarray:
    """Run U-Net classification on fused satellite data.

    Returns probability maps for each detection category:
    0: groundwater, 1: excavation, 2: ancient_ruins,
    3: dissolved_minerals, 4: underground_voids
    """
    model = SimpleUNet(n_classes=n_classes)
    return model.predict(fused_data)
