"""
Freya Screen Reader check functions - part 2.

Link, button, and accessible name checks extracted from _screen_reader_checks.py.
"""

from typing import Optional, cast

from playwright.async_api import Page

from Asgard.Freya.Accessibility.models.accessibility_models import (
    ScreenReaderIssue,
    ScreenReaderIssueType,
    ViolationSeverity,
)
from Asgard.Freya.Accessibility.services._screen_reader_checks import (
    get_selector,
)


async def get_accessible_name(page: Page, element) -> Optional[str]:
    """Get the computed accessible name for an element."""
    try:
        name = await page.evaluate("""
            (element) => {
                // Check aria-labelledby
                const labelledby = element.getAttribute('aria-labelledby');
                if (labelledby) {
                    const labels = labelledby.split(' ')
                        .map(id => document.getElementById(id))
                        .filter(el => el)
                        .map(el => el.textContent.trim());
                    if (labels.length > 0) return labels.join(' ');
                }

                // Check aria-label
                const ariaLabel = element.getAttribute('aria-label');
                if (ariaLabel && ariaLabel.trim()) return ariaLabel.trim();

                // Check for label element
                const id = element.id;
                if (id) {
                    const label = document.querySelector(`label[for="${id}"]`);
                    if (label && label.textContent.trim()) {
                        return label.textContent.trim();
                    }
                }

                // Check parent label
                const parentLabel = element.closest('label');
                if (parentLabel) {
                    const text = parentLabel.textContent.trim();
                    if (text) return text;
                }

                // Check title attribute
                const title = element.getAttribute('title');
                if (title && title.trim()) return title.trim();

                // Check text content (for buttons, links)
                const text = element.textContent || element.innerText;
                if (text && text.trim()) return text.trim();

                // Check value (for inputs)
                const value = element.value;
                if (value && value.trim()) return value.trim();

                // Check placeholder (last resort)
                const placeholder = element.getAttribute('placeholder');
                if (placeholder && placeholder.trim()) return placeholder.trim();

                // Check for images with alt text inside element
                const img = element.querySelector('img[alt]');
                if (img) {
                    const alt = img.getAttribute('alt');
                    if (alt && alt.trim()) return alt.trim();
                }

                return null;
            }
        """, element)
        return cast(Optional[str], name)
    except Exception:
        return None


async def check_links(page: Page) -> tuple[list[ScreenReaderIssue], tuple[int, int]]:
    """Check links for accessible names."""
    issues = []
    labeled = 0
    total = 0

    try:
        links = await page.query_selector_all("a[href]")

        for link in links:
            total += 1
            accessible_name = await get_accessible_name(page, link)

            if accessible_name:
                labeled += 1
            else:
                selector = await get_selector(page, link)
                href = await link.get_attribute("href")
                issues.append(ScreenReaderIssue(
                    issue_type=ScreenReaderIssueType.EMPTY_LINK,
                    element_selector=selector,
                    description=f"Link has no accessible name: {href[:50] if href else 'unknown'}",
                    severity=ViolationSeverity.SERIOUS,
                    wcag_reference="2.4.4",
                    suggested_fix="Add descriptive text content or aria-label",
                ))

    except Exception:
        pass

    return issues, (labeled, total)


async def check_buttons(page: Page) -> tuple[list[ScreenReaderIssue], tuple[int, int]]:
    """Check buttons for accessible names."""
    issues = []
    labeled = 0
    total = 0

    try:
        buttons = await page.query_selector_all(
            "button, input[type='submit'], input[type='button'], [role='button']"
        )

        for button in buttons:
            total += 1
            accessible_name = await get_accessible_name(page, button)

            if accessible_name:
                labeled += 1
            else:
                selector = await get_selector(page, button)
                issues.append(ScreenReaderIssue(
                    issue_type=ScreenReaderIssueType.EMPTY_BUTTON,
                    element_selector=selector,
                    description="Button has no accessible name",
                    severity=ViolationSeverity.CRITICAL,
                    wcag_reference="4.1.2",
                    suggested_fix="Add text content, aria-label, or value attribute",
                ))

    except Exception:
        pass

    return issues, (labeled, total)
