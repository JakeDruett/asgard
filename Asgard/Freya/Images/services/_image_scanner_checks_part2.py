"""
Freya Image Optimization Scanner checks - part 2.

Oversized, srcset, and composite check functions extracted from _image_scanner_checks.py.
"""

from typing import List, Optional

from Asgard.Freya.Images.models.image_models import (
    ImageConfig,
    ImageFormat,
    ImageInfo,
    ImageIssue,
    ImageIssueSeverity,
    ImageIssueType,
)
from Asgard.Freya.Images.services._image_scanner_checks import (
    check_alt_text,
    check_dimensions,
    check_format,
    check_lazy_loading,
)


def estimate_size_savings(
    natural_width: int, natural_height: int,
    display_width: int, display_height: int,
) -> int:
    """Estimate bytes saved by resizing."""
    if not natural_height or not display_height:
        return 0
    natural_pixels = natural_width * natural_height
    display_pixels = display_width * display_height
    bytes_per_pixel = 0.5
    natural_bytes = natural_pixels * bytes_per_pixel
    display_bytes = display_pixels * bytes_per_pixel
    return int(natural_bytes - display_bytes)


def check_oversized(image: ImageInfo, oversized_threshold: float) -> Optional[ImageIssue]:
    """Check for oversized images."""
    if not image.natural_width or not image.display_width:
        return None
    if image.display_width == 0:
        return None

    ratio = image.natural_width / image.display_width

    if ratio > oversized_threshold:
        wasted_pixels = image.natural_width - image.display_width
        estimated_savings = estimate_size_savings(
            image.natural_width, image.natural_height or 0,
            image.display_width, image.display_height or 0,
        )
        return ImageIssue(
            issue_type=ImageIssueType.OVERSIZED_IMAGE,
            severity=ImageIssueSeverity.WARNING,
            image_src=image.src,
            description=(
                f"Image is {ratio:.1f}x larger than displayed size "
                f"({image.natural_width}x{image.natural_height} displayed at "
                f"{image.display_width}x{image.display_height})"
            ),
            suggested_fix=(
                f"Resize image to match display size or use srcset. "
                f"Could save ~{estimated_savings // 1024}KB"
            ),
            wcag_reference=None,
            impact=f"~{wasted_pixels}px of unnecessary width being downloaded",
            element_html=image.element_html,
            css_selector=image.css_selector,
        )
    return None


def check_srcset(image: ImageInfo, min_srcset_width: int) -> Optional[ImageIssue]:
    """Check for missing srcset on responsive images."""
    if (image.display_width or 0) < min_srcset_width:
        return None
    if not image.has_srcset:
        return ImageIssue(
            issue_type=ImageIssueType.MISSING_SRCSET,
            severity=ImageIssueSeverity.INFO,
            image_src=image.src,
            description="Large image missing srcset for responsive images",
            suggested_fix=(
                "Add srcset attribute with multiple image sizes "
                "for different screen resolutions"
            ),
            wcag_reference=None,
            impact="Mobile users may download unnecessarily large images",
            element_html=image.element_html,
            css_selector=image.css_selector,
        )
    return None


def check_image(image: ImageInfo, config: ImageConfig) -> List[ImageIssue]:
    """Check a single image for issues."""
    issues: List[ImageIssue] = []

    if image.is_background_image:
        if config.check_formats:
            format_issue = check_format(image, config.skip_svg)
            if format_issue:
                issues.append(format_issue)
        return issues

    if config.check_alt_text:
        alt_issue = check_alt_text(image)
        if alt_issue:
            issues.append(alt_issue)

    if config.check_lazy_loading:
        lazy_issue = check_lazy_loading(image)
        if lazy_issue:
            issues.append(lazy_issue)

    if config.check_formats:
        format_issue = check_format(image, config.skip_svg)
        if format_issue:
            issues.append(format_issue)

    if config.check_dimensions:
        dim_issue = check_dimensions(image)
        if dim_issue:
            issues.append(dim_issue)

    if config.check_oversized:
        oversized_issue = check_oversized(image, config.oversized_threshold)
        if oversized_issue:
            issues.append(oversized_issue)

    if config.check_srcset:
        srcset_issue = check_srcset(image, config.min_srcset_width)
        if srcset_issue:
            issues.append(srcset_issue)

    return issues
