"""Freya Color Contrast Checker - validates contrast ratios against WCAG 2.1."""

from datetime import datetime
from typing import List, Optional, Tuple

from playwright.async_api import async_playwright, Page

from Asgard.Freya.Accessibility.models.accessibility_models import (
    AccessibilityConfig,
    ContrastReport,
    ContrastResult,
    ContrastIssue,
    TextSize,
    WCAGLevel,
)
from Asgard.Freya.Accessibility.services._color_contrast_math import (
    parse_color,
    calculate_contrast_ratio,
    calculate_relative_luminance,
    parse_font_size,
    darken_to_ratio,
    rgb_to_hex,
)
from Asgard.Freya.Accessibility.services._color_contrast_page import (
    get_effective_background,
    get_text_elements,
    get_unique_selector,
)


CONTRAST_REQUIREMENTS = {
    WCAGLevel.A: {TextSize.NORMAL: 3.0, TextSize.LARGE: 3.0},
    WCAGLevel.AA: {TextSize.NORMAL: 4.5, TextSize.LARGE: 3.0},
    WCAGLevel.AAA: {TextSize.NORMAL: 7.0, TextSize.LARGE: 4.5},
}


class ColorContrastChecker:
    """Color contrast ratio checker for WCAG compliance."""

    def __init__(self, config: AccessibilityConfig):
        self.config = config

    async def check(self, url: str) -> ContrastReport:
        """Check color contrast on a page and return ContrastReport."""
        results = []
        issues = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                text_elements = await get_text_elements(page)

                for element_data in text_elements:
                    result = await self._analyze_element_contrast(page, element_data)
                    if result:
                        results.append(result)
                        if not result.is_passing:
                            issues.append(self._create_issue(result))
            finally:
                await browser.close()

        passing_count = sum(1 for r in results if r.is_passing)
        failing_count = len(results) - passing_count
        avg_contrast = sum(r.contrast_ratio for r in results) / len(results) if results else 0.0

        return ContrastReport(
            url=url,
            wcag_level=self.config.wcag_level.value,
            tested_at=datetime.now().isoformat(),
            total_elements=len(results),
            passing_count=passing_count,
            failing_count=failing_count,
            results=results,
            issues=issues,
            average_contrast=avg_contrast,
        )

    async def check_colors(
        self, foreground: str, background: str,
        font_size_px: float = 16.0, font_weight: str = "400"
    ) -> ContrastResult:
        """Check contrast between two specific colors."""
        fg_rgb = parse_color(foreground)
        bg_rgb = parse_color(background)
        if fg_rgb is None:
            fg_rgb = (0, 0, 0)
        if bg_rgb is None:
            bg_rgb = (255, 255, 255)

        contrast_ratio = calculate_contrast_ratio(fg_rgb, bg_rgb)
        text_size = self._categorize_text_size(font_size_px, font_weight)

        required_aa = CONTRAST_REQUIREMENTS[WCAGLevel.AA][text_size]
        required_aaa = CONTRAST_REQUIREMENTS[WCAGLevel.AAA][text_size]
        required = CONTRAST_REQUIREMENTS[self.config.wcag_level][text_size]

        return ContrastResult(
            element_selector="direct-check",
            foreground_color=foreground,
            background_color=background,
            contrast_ratio=contrast_ratio,
            required_ratio=required,
            text_size=text_size,
            font_size_px=font_size_px,
            font_weight=font_weight,
            is_passing=contrast_ratio >= required,
            wcag_aa_pass=contrast_ratio >= required_aa,
            wcag_aaa_pass=contrast_ratio >= required_aaa,
        )

    async def _analyze_element_contrast(self, page: Page, element_data: dict) -> Optional[ContrastResult]:
        """Analyze contrast for a single element."""
        try:
            element = element_data["element"]
            styles = element_data["styles"]
            selector = element_data["selector"]

            fg_color = styles.get("color", "rgb(0, 0, 0)")
            bg_color = await get_effective_background(page, element)

            fg_rgb = parse_color(fg_color)
            bg_rgb = parse_color(bg_color)
            if fg_rgb is None or bg_rgb is None:
                return None

            contrast_ratio = calculate_contrast_ratio(fg_rgb, bg_rgb)
            font_size_str = styles.get("fontSize", "16px")
            font_size_px = parse_font_size(font_size_str)
            font_weight = styles.get("fontWeight", "400")
            text_size = self._categorize_text_size(font_size_px, font_weight)

            required_aa = CONTRAST_REQUIREMENTS[WCAGLevel.AA][text_size]
            required_aaa = CONTRAST_REQUIREMENTS[WCAGLevel.AAA][text_size]
            required = CONTRAST_REQUIREMENTS[self.config.wcag_level][text_size]
            unique_selector = await get_unique_selector(page, element)

            return ContrastResult(
                element_selector=unique_selector or selector,
                foreground_color=fg_color,
                background_color=bg_color,
                contrast_ratio=round(contrast_ratio, 2),
                required_ratio=required,
                text_size=text_size,
                font_size_px=font_size_px,
                font_weight=font_weight,
                is_passing=contrast_ratio >= required,
                wcag_aa_pass=contrast_ratio >= required_aa,
                wcag_aaa_pass=contrast_ratio >= required_aaa,
            )
        except Exception:
            return None

    def _categorize_text_size(self, font_size_px: float, font_weight: str) -> TextSize:
        """Categorize text as normal or large per WCAG."""
        is_bold = font_weight in ["bold", "700", "800", "900"] or (
            font_weight.isdigit() and int(font_weight) >= 700
        )
        if font_size_px >= 24:
            return TextSize.LARGE
        elif font_size_px >= 18.5 and is_bold:
            return TextSize.LARGE
        else:
            return TextSize.NORMAL

    def _create_issue(self, result: ContrastResult) -> ContrastIssue:
        """Create a ContrastIssue from a failing result."""
        fg_suggested, bg_suggested = self._suggest_fixes(
            result.foreground_color, result.background_color, result.required_ratio,
        )
        return ContrastIssue(
            element_selector=result.element_selector,
            foreground_color=result.foreground_color,
            background_color=result.background_color,
            contrast_ratio=result.contrast_ratio,
            required_ratio=result.required_ratio,
            suggested_foreground=fg_suggested,
            suggested_background=bg_suggested,
        )

    def _suggest_fixes(
        self, foreground: str, background: str, required_ratio: float
    ) -> Tuple[Optional[str], Optional[str]]:
        """Suggest color fixes to meet contrast requirements."""
        fg_rgb = parse_color(foreground)
        bg_rgb = parse_color(background)
        if fg_rgb is None or bg_rgb is None:
            return None, None

        fg_luminance = calculate_relative_luminance(fg_rgb)
        bg_luminance = calculate_relative_luminance(bg_rgb)

        if fg_luminance < bg_luminance:
            darker_rgb = darken_to_ratio(fg_rgb, bg_luminance, required_ratio)
            return rgb_to_hex(darker_rgb), None
        else:
            darker_rgb = darken_to_ratio(bg_rgb, fg_luminance, required_ratio)
            return None, rgb_to_hex(darker_rgb)
