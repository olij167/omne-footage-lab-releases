from __future__ import annotations

from dataclasses import dataclass

MIN_ZOOM = 0.25
MAX_ZOOM = 8.0


@dataclass(frozen=True)
class PreviewTransform:
    scale: float
    display_size: tuple[int, int]
    offset: tuple[int, int]


def clamp_zoom(value: float) -> float:
    return max(MIN_ZOOM, min(MAX_ZOOM, float(value)))


def _fit_scale(source: tuple[int, int], viewport: tuple[int, int]) -> float:
    sw, sh = max(1, int(source[0])), max(1, int(source[1]))
    vw, vh = max(1, int(viewport[0])), max(1, int(viewport[1]))
    return min(vw / sw, vh / sh)


def compute_preview_transform(
    source: tuple[int, int],
    viewport: tuple[int, int],
    *,
    mode: str = "fit",
    zoom: float = 1.0,
    pan: tuple[float, float] = (0.0, 0.0),
) -> PreviewTransform:
    """Return display-only scaling and bounded pan for the preview surface.

    ``fit`` is allowed to upscale a reduced preview proxy because this never
    alters source/rendered media; it only controls how the decoded preview is
    painted in the UI. ``actual`` is exact proxy pixel size. ``zoom`` is a
    bounded multiplier relative to Fit so it behaves consistently across
    differently sized preview cells.
    """
    sw, sh = max(1, int(source[0])), max(1, int(source[1]))
    vw, vh = max(1, int(viewport[0])), max(1, int(viewport[1]))
    fit = _fit_scale((sw, sh), (vw, vh))
    if mode == "fit":
        scale = fit
    elif mode == "actual":
        scale = 1.0
    elif mode == "zoom":
        scale = fit * clamp_zoom(zoom)
    else:
        raise ValueError(f"Unknown preview mode: {mode}")

    dw = max(1, int(round(sw * scale)))
    dh = max(1, int(round(sh * scale)))
    max_x = max(0, (dw - vw) // 2)
    max_y = max(0, (dh - vh) // 2)
    px = int(round(max(-max_x, min(max_x, float(pan[0]))))) if max_x else 0
    py = int(round(max(-max_y, min(max_y, float(pan[1]))))) if max_y else 0
    return PreviewTransform(scale=scale, display_size=(dw, dh), offset=(px, py))
