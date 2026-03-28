"""
Freya Color Contrast - page interaction helpers.

Playwright page interaction methods extracted from color_contrast.py.
"""

from typing import Any, Dict, List, Optional, cast

from playwright.async_api import Page


async def get_text_elements(page: Page) -> List[dict]:
    """Get all text elements from the page."""
    selectors = [
        "p", "span", "div", "h1", "h2", "h3", "h4", "h5", "h6",
        "a", "button", "label", "li", "td", "th", "caption",
        "figcaption", "blockquote", "cite", "q", "em", "strong",
        "small", "mark", "del", "ins", "sub", "sup", "time",
    ]

    elements = []

    for selector in selectors:
        found = await page.query_selector_all(selector)
        for elem in found[:50]:
            try:
                has_text = await elem.evaluate("""
                    el => {
                        const text = el.innerText || el.textContent;
                        return text && text.trim().length > 0;
                    }
                """)

                if has_text:
                    box = await elem.bounding_box()
                    if box and box["width"] > 0 and box["height"] > 0:
                        styles = await get_element_styles(page, elem)
                        elements.append({
                            "element": elem,
                            "selector": selector,
                            "styles": styles,
                        })
            except Exception:
                continue

    return elements


async def get_element_styles(page: Page, element) -> dict:
    """Get computed styles for an element."""
    try:
        styles = await page.evaluate("""
            (element) => {
                const computed = getComputedStyle(element);
                return {
                    color: computed.color,
                    backgroundColor: computed.backgroundColor,
                    fontSize: computed.fontSize,
                    fontWeight: computed.fontWeight,
                    lineHeight: computed.lineHeight,
                };
            }
        """, element)
        return cast(Dict[Any, Any], styles)
    except Exception:
        return {
            "color": "rgb(0, 0, 0)",
            "backgroundColor": "rgb(255, 255, 255)",
            "fontSize": "16px",
            "fontWeight": "400",
        }


async def get_effective_background(page: Page, element) -> str:
    """Get effective background color including parent elements."""
    try:
        bg_color = await page.evaluate("""
            (element) => {
                let current = element;
                while (current) {
                    const computed = getComputedStyle(current);
                    const bg = computed.backgroundColor;

                    // Skip transparent backgrounds
                    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                        return bg;
                    }
                    current = current.parentElement;
                }
                return 'rgb(255, 255, 255)';  // Default to white
            }
        """, element)
        return cast(str, bg_color)
    except Exception:
        return "rgb(255, 255, 255)"


async def get_unique_selector(page: Page, element) -> Optional[str]:
    """Generate a unique CSS selector for an element."""
    try:
        selector = await page.evaluate("""
            (element) => {
                if (element.id) {
                    return '#' + element.id;
                }

                const path = [];
                let current = element;

                while (current && current.nodeType === Node.ELEMENT_NODE) {
                    let selector = current.nodeName.toLowerCase();

                    if (current.id) {
                        selector = '#' + current.id;
                        path.unshift(selector);
                        break;
                    }

                    if (current.className && typeof current.className === 'string') {
                        const classes = current.className.trim().split(/\\s+/).slice(0, 2);
                        if (classes.length > 0 && classes[0]) {
                            selector += '.' + classes.join('.');
                        }
                    }

                    path.unshift(selector);
                    current = current.parentNode;
                }

                return path.slice(-3).join(' > ');
            }
        """, element)
        return cast(Optional[str], selector)
    except Exception:
        return None
