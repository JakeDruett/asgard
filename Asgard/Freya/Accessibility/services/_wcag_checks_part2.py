"""
Freya WCAG check methods - part 2.

Link, language, and ARIA checks extracted from _wcag_checks.py.
"""

from typing import List, Optional, Tuple

from playwright.async_api import Page

from Asgard.Freya.Accessibility.models.accessibility_models import (
    AccessibilityCategory,
    AccessibilityViolation,
    ViolationSeverity,
)
from Asgard.Freya.Accessibility.services._wcag_checks import (
    generate_id,
    get_element_html,
)


async def check_links(
    page: Page,
    include_element_html: bool,
) -> Tuple[List[AccessibilityViolation], int]:
    """Check link accessibility."""
    violations = []
    passed = 0

    links = await page.query_selector_all("a[href]")

    for link in links:
        text = await link.inner_text()
        aria_label = await link.get_attribute("aria-label")
        href = await link.get_attribute("href")

        images = await link.query_selector_all("img[alt]")
        img_alts = []
        for img in images:
            alt = await img.get_attribute("alt")
            if alt:
                img_alts.append(alt)

        accessible_name = (text.strip() if text else "") or aria_label or " ".join(img_alts)

        if not accessible_name:
            element_html = await get_element_html(link, include_element_html)
            violations.append(AccessibilityViolation(
                id=generate_id("link-name", href or "unknown"),
                wcag_reference="2.4.4",
                category=AccessibilityCategory.LINKS,
                severity=ViolationSeverity.SERIOUS,
                description="Link has no accessible name",
                element_selector=f'a[href="{href}"]',
                element_html=element_html,
                suggested_fix="Add descriptive text content or aria-label to the link",
                impact="Screen reader users cannot understand where the link leads",
            ))
        else:
            passed += 1

        if accessible_name and accessible_name.lower() in ["click here", "here", "read more", "learn more", "more"]:
            element_html = await get_element_html(link, include_element_html)
            violations.append(AccessibilityViolation(
                id=generate_id("link-purpose", href or "unknown"),
                wcag_reference="2.4.4",
                category=AccessibilityCategory.LINKS,
                severity=ViolationSeverity.MODERATE,
                description=f'Link text "{accessible_name}" is not descriptive',
                element_selector=f'a[href="{href}"]',
                element_html=element_html,
                suggested_fix="Use descriptive link text that indicates the destination or purpose",
                impact="Users cannot understand the link purpose without surrounding context",
            ))

    return violations, passed


async def check_language(
    page: Page,
) -> Tuple[List[AccessibilityViolation], int]:
    """Check language attributes."""
    violations = []
    passed = 0

    html_lang = await page.evaluate("() => document.documentElement.lang")

    if not html_lang or html_lang.strip() == "":
        violations.append(AccessibilityViolation(
            id=generate_id("lang", "html"),
            wcag_reference="3.1.1",
            category=AccessibilityCategory.LANGUAGE,
            severity=ViolationSeverity.SERIOUS,
            description="Page is missing language attribute",
            element_selector="html",
            suggested_fix='Add lang attribute to the html element (e.g., lang="en")',
            impact="Screen readers may not use correct pronunciation",
        ))
    else:
        passed += 1

    return violations, passed


async def check_aria_basic(
    page: Page,
    include_element_html: bool,
) -> Tuple[List[AccessibilityViolation], int]:
    """Basic ARIA checks (full validation in ARIAValidator)."""
    violations = []
    passed = 0

    valid_roles = {
        "alert", "alertdialog", "application", "article", "banner", "button",
        "cell", "checkbox", "columnheader", "combobox", "complementary",
        "contentinfo", "definition", "dialog", "directory", "document", "feed",
        "figure", "form", "grid", "gridcell", "group", "heading", "img",
        "link", "list", "listbox", "listitem", "log", "main", "marquee",
        "math", "menu", "menubar", "menuitem", "menuitemcheckbox",
        "menuitemradio", "meter", "navigation", "none", "note", "option",
        "presentation", "progressbar", "radio", "radiogroup", "region",
        "row", "rowgroup", "rowheader", "scrollbar", "search", "searchbox",
        "separator", "slider", "spinbutton", "status", "switch", "tab",
        "table", "tablist", "tabpanel", "term", "textbox", "timer",
        "toolbar", "tooltip", "tree", "treegrid", "treeitem",
    }

    aria_elements = await page.query_selector_all("[role]")

    for elem in aria_elements:
        role = await elem.get_attribute("role")

        if role and role.lower() not in valid_roles:
            element_html = await get_element_html(elem, include_element_html)
            violations.append(AccessibilityViolation(
                id=generate_id("aria-role", role),
                wcag_reference="4.1.2",
                category=AccessibilityCategory.ARIA,
                severity=ViolationSeverity.SERIOUS,
                description=f'Invalid ARIA role: "{role}"',
                element_selector=f'[role="{role}"]',
                element_html=element_html,
                suggested_fix="Use a valid ARIA role from the WAI-ARIA specification",
                impact="Assistive technologies may not interpret the element correctly",
            ))
        else:
            passed += 1

    return violations, passed
