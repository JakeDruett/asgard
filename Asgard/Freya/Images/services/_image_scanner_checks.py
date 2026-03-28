"""
Freya Image Optimization Scanner checks.

Individual image check functions extracted from image_optimization_scanner.py.
"""

from typing import List, Optional
from urllib.parse import urlparse

from Asgard.Freya.Images.models.image_models import (
    ImageFormat,
    ImageInfo,
    ImageIssue,
    ImageIssueSeverity,
    ImageIssueType,
)


def detect_format(src: str) -> ImageFormat:
    """Detect image format from URL."""
    if not src:
        return ImageFormat.UNKNOWN

    src_lower = src.lower()

    for fmt in ImageFormat:
        if fmt == ImageFormat.UNKNOWN:
            continue
        if f".{fmt.value}" in src_lower:
            return fmt

    if "webp" in src_lower:
        return ImageFormat.WEBP
    if "avif" in src_lower:
        return ImageFormat.AVIF

    return ImageFormat.UNKNOWN


def parse_int(value) -> Optional[int]:
    """Safely parse an integer value."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def build_image_info(data: dict) -> ImageInfo:
    """Build ImageInfo from extracted data."""
    src = data.get("src", "")
    format_type = detect_format(src)

    is_decorative = (
        data.get("role") == "presentation" or
        data.get("ariaHidden") == "true" or
        (data.get("hasAlt") and data.get("alt") == "")
    )

    return ImageInfo(
        src=src,
        alt=data.get("alt"),
        has_alt=data.get("hasAlt", False),
        width=parse_int(data.get("width")),
        height=parse_int(data.get("height")),
        has_dimensions=bool(data.get("width") and data.get("height")),
        loading=data.get("loading"),
        has_lazy_loading=data.get("loading") == "lazy",
        srcset=data.get("srcset"),
        has_srcset=bool(data.get("srcset")),
        sizes=data.get("sizes"),
        format=format_type,
        natural_width=data.get("naturalWidth"),
        natural_height=data.get("naturalHeight"),
        display_width=data.get("displayWidth"),
        display_height=data.get("displayHeight"),
        is_above_fold=data.get("isAboveFold", False),
        element_html=data.get("html"),
        css_selector=data.get("cssSelector"),
        is_decorative=is_decorative,
        is_background_image=data.get("type") == "background",
    )


def appears_decorative(image: ImageInfo) -> bool:
    """Heuristic to detect if image appears decorative."""
    src_lower = image.src.lower()

    decorative_patterns = [
        "icon", "logo", "spacer", "dot", "bullet",
        "divider", "separator", "border", "shadow",
        "gradient", "pattern", "texture", "background",
        "arrow", "chevron", "caret",
    ]

    for pattern in decorative_patterns:
        if pattern in src_lower:
            return True

    if image.display_width and image.display_height:
        if image.display_width < 24 and image.display_height < 24:
            return True

    return False


def check_alt_text(image: ImageInfo) -> Optional[ImageIssue]:
    """Check for alt text issues."""
    if image.is_decorative and image.has_alt and image.alt == "":
        return None

    if not image.has_alt:
        return ImageIssue(
            issue_type=ImageIssueType.MISSING_ALT,
            severity=ImageIssueSeverity.CRITICAL,
            image_src=image.src,
            description="Image is missing alt attribute",
            suggested_fix=(
                "Add an alt attribute describing the image content. "
                "For decorative images, use alt=\"\""
            ),
            wcag_reference="WCAG 1.1.1 (Non-text Content)",
            impact="Screen reader users will not know what the image contains",
            element_html=image.element_html,
            css_selector=image.css_selector,
        )

    if image.alt == "" and not image.is_decorative:
        if appears_decorative(image):
            return None

        return ImageIssue(
            issue_type=ImageIssueType.EMPTY_ALT,
            severity=ImageIssueSeverity.WARNING,
            image_src=image.src,
            description="Image has empty alt text but may contain meaningful content",
            suggested_fix=(
                "If the image conveys information, add descriptive alt text. "
                "If purely decorative, empty alt is correct."
            ),
            wcag_reference="WCAG 1.1.1 (Non-text Content)",
            impact="Screen reader users may miss important information",
            element_html=image.element_html,
            css_selector=image.css_selector,
        )

    return None


def check_lazy_loading(image: ImageInfo) -> Optional[ImageIssue]:
    """Check for lazy loading issues."""
    if image.is_above_fold and image.has_lazy_loading:
        return ImageIssue(
            issue_type=ImageIssueType.MISSING_LAZY_LOADING,
            severity=ImageIssueSeverity.INFO,
            image_src=image.src,
            description="Above-fold image has lazy loading which may delay LCP",
            suggested_fix=(
                "Remove loading=\"lazy\" from above-fold images "
                "to improve Largest Contentful Paint"
            ),
            wcag_reference=None,
            impact="May negatively impact Core Web Vitals (LCP)",
            element_html=image.element_html,
            css_selector=image.css_selector,
        )

    if not image.is_above_fold and not image.has_lazy_loading:
        return ImageIssue(
            issue_type=ImageIssueType.MISSING_LAZY_LOADING,
            severity=ImageIssueSeverity.WARNING,
            image_src=image.src,
            description="Below-fold image does not have lazy loading",
            suggested_fix="Add loading=\"lazy\" to defer loading until needed",
            wcag_reference=None,
            impact=(
                "Images load immediately, increasing initial page weight "
                "and slowing page load"
            ),
            element_html=image.element_html,
            css_selector=image.css_selector,
        )

    return None


def check_format(image: ImageInfo, skip_svg: bool) -> Optional[ImageIssue]:
    """Check for non-optimized format."""
    if skip_svg and image.format == ImageFormat.SVG:
        return None

    modern_formats = [ImageFormat.WEBP, ImageFormat.AVIF, ImageFormat.SVG]

    if image.format not in modern_formats and image.format != ImageFormat.UNKNOWN:
        return ImageIssue(
            issue_type=ImageIssueType.NON_OPTIMIZED_FORMAT,
            severity=ImageIssueSeverity.WARNING,
            image_src=image.src,
            description=(
                f"Image uses {image.format.value.upper()} format "
                f"instead of modern WebP/AVIF"
            ),
            suggested_fix=(
                "Convert to WebP or AVIF format for better compression. "
                "Use <picture> element for fallback support."
            ),
            wcag_reference=None,
            impact="Modern formats can reduce file size by 25-50% without quality loss",
            element_html=image.element_html,
            css_selector=image.css_selector,
        )

    return None


def check_dimensions(image: ImageInfo) -> Optional[ImageIssue]:
    """Check for missing width/height attributes."""
    if not image.has_dimensions:
        return ImageIssue(
            issue_type=ImageIssueType.MISSING_DIMENSIONS,
            severity=ImageIssueSeverity.WARNING,
            image_src=image.src,
            description="Image is missing width and/or height attributes",
            suggested_fix=(
                "Add explicit width and height attributes to prevent "
                "Cumulative Layout Shift (CLS)"
            ),
            wcag_reference=None,
            impact="Browser cannot reserve space, causing layout shifts when image loads",
            element_html=image.element_html,
            css_selector=image.css_selector,
        )

    return None


