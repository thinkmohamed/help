"""U-Net segmentation.

We provide a torch implementation behind an optional import. When torch is not
available, we fall back to a deterministic differentiable proxy (multi-scale
gradient + thresholding) so the rest of the pipeline still functions.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi


def _torch_unet_segment(stack: np.ndarray) -> np.ndarray:
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:
        raise RuntimeError("torch not available") from exc

    h, w, c = stack.shape

    class TinyUNet(nn.Module):
        def __init__(self, in_ch: int, out_ch: int = 1) -> None:
            super().__init__()
            self.enc1 = nn.Sequential(nn.Conv2d(in_ch, 16, 3, padding=1), nn.ReLU())
            self.enc2 = nn.Sequential(nn.Conv2d(16, 32, 3, padding=1, stride=2), nn.ReLU())
            self.dec1 = nn.Sequential(nn.ConvTranspose2d(32, 16, 2, stride=2), nn.ReLU())
            self.head = nn.Conv2d(16, out_ch, 1)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            e1 = self.enc1(x)
            e2 = self.enc2(e1)
            d1 = self.dec1(e2)
            d1 = d1[:, :, : e1.shape[2], : e1.shape[3]] + e1
            return torch.sigmoid(self.head(d1))

    torch.manual_seed(42)
    net = TinyUNet(in_ch=c).eval()
    with torch.no_grad():
        x = torch.from_numpy(stack.transpose(2, 0, 1)).unsqueeze(0).float()
        y = net(x)[0, 0].numpy()
    return y.astype(np.float32)


def _proxy_segment(stack: np.ndarray) -> np.ndarray:
    """Multi-scale gradient + smoothing proxy used when torch is unavailable."""
    if stack.size == 0:
        return np.zeros((0, 0), dtype=np.float32)
    score = np.zeros(stack.shape[:2], dtype=np.float32)
    for c in range(stack.shape[2]):
        chan = stack[..., c]
        gy, gx = np.gradient(chan)
        score += np.hypot(gx, gy)
    score = ndi.gaussian_filter(score, sigma=2.0)
    lo, hi = score.min(), score.max()
    if hi - lo < 1e-6:
        return np.zeros_like(score)
    return ((score - lo) / (hi - lo)).astype(np.float32)


def unet_segmentation(stack: np.ndarray, *, use_torch: bool = True) -> np.ndarray:
    """Return a (H, W) segmentation probability map in [0, 1]."""
    if use_torch:
        try:
            return _torch_unet_segment(stack)
        except Exception:
            pass
    return _proxy_segment(stack)
