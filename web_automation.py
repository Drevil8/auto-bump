import asyncio
from playwright.async_api import async_playwright
import os

SCREENSHOT_PATH = "/tmp/debug_screenshot.png"


class WebAutomation:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.steps = []  # Records every action for export

    async def start(self):
        """Launch the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        self.page = await self.browser.new_page(viewport={"width": 1280, "height": 800})

    async def stop(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.browser = None
        self.page = None
        self.playwright = None

    async def screenshot(self):
        """Take a screenshot and return the file path."""
        await self.page.screenshot(path=SCREENSHOT_PATH, full_page=False)
        return SCREENSHOT_PATH

    async def goto(self, url):
        """Navigate to a URL."""
        await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(1)  # Let dynamic content load
        self.steps.append({"action": "goto", "url": url})
        return await self.screenshot()

    async def click(self, selector):
        """Click an element by selector."""
        await self.page.click(selector, timeout=10000)
        await asyncio.sleep(1)
        self.steps.append({"action": "click", "selector": selector})
        return await self.screenshot()

    async def type_text(self, selector, text):
        """Type text into an input field."""
        await self.page.fill(selector, text)
        await asyncio.sleep(0.5)
        self.steps.append({"action": "type", "selector": selector, "text": text})
        return await self.screenshot()

    async def scroll(self, direction="down"):
        """Scroll the page up or down."""
        distance = 500 if direction == "down" else -500
        await self.page.evaluate(f"window.scrollBy(0, {distance})")
        await asyncio.sleep(0.5)
        self.steps.append({"action": "scroll", "direction": direction})
        return await self.screenshot()

    async def hover(self, selector):
        """Hover over an element."""
        await self.page.hover(selector, timeout=10000)
        await asyncio.sleep(0.5)
        self.steps.append({"action": "hover", "selector": selector})
        return await self.screenshot()

    async def select_option(self, selector, value):
        """Select a dropdown option."""
        await self.page.select_option(selector, value, timeout=10000)
        await asyncio.sleep(0.5)
        self.steps.append({"action": "select", "selector": selector, "value": value})
        return await self.screenshot()

    async def get_text(self, selector):
        """Get the text content of an element."""
        element = await self.page.query_selector(selector)
        if element:
            return await element.inner_text()
        return "(element not found)"

    async def get_url(self):
        """Get the current page URL."""
        return self.page.url

    async def get_html(self):
        """Get the page HTML."""
        return await self.page.content()

    async def list_elements(self, selector):
        """List all elements matching a selector with useful info."""
        elements = await self.page.query_selector_all(selector)
        results = []
        for el in elements[:30]:  # Limit to 30 elements
            try:
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                el_id = await el.get_attribute("id") or ""
                el_class = await el.get_attribute("class") or ""
                el_name = await el.get_attribute("name") or ""
                el_type = await el.get_attribute("type") or ""
                el_href = await el.get_attribute("href") or ""
                el_text = (await el.inner_text()).strip()[:50] if tag not in ["input", "textarea"] else ""
                el_placeholder = await el.get_attribute("placeholder") or ""
                el_value = await el.get_attribute("value") or ""
                el_aria = await el.get_attribute("aria-label") or ""

                # Build a readable description
                parts = [f"<{tag}"]
                if el_id:
                    parts.append(f'id="{el_id}"')
                if el_name:
                    parts.append(f'name="{el_name}"')
                if el_type:
                    parts.append(f'type="{el_type}"')
                if el_placeholder:
                    parts.append(f'placeholder="{el_placeholder}"')
                if el_value:
                    parts.append(f'value="{el_value[:30]}"')
                if el_aria:
                    parts.append(f'aria-label="{el_aria[:30]}"')
                if el_class:
                    short_class = " ".join(el_class.split()[:3])
                    parts.append(f'class="{short_class}"')
                if el_href:
                    parts.append(f'href="{el_href[:50]}"')
                parts.append(">")
                if el_text:
                    parts.append(f' "{el_text}"')

                # Add suggested selector
                if el_id:
                    parts.append(f'  → use: #{el_id}')
                elif el_name:
                    parts.append(f"  → use: {tag}[name='{el_name}']")
                elif el_text:
                    safe = el_text[:30].replace('"', '\\"')
                    parts.append(f'  → use: text={safe}')

                results.append(" ".join(parts))
            except:
                continue
        return results

    def export_code(self):
        """Export recorded steps as a standalone Python automation script."""
        lines = [
            'import asyncio',
            'from playwright.async_api import async_playwright',
            'import os',
            '',
            '',
            'async def run_automation():',
            '    async with async_playwright() as p:',
            '        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])',
            '        page = await browser.new_page(viewport={"width": 1280, "height": 800})',
            '',
        ]

        for step in self.steps:
            if step["action"] == "goto":
                lines.append(f'        await page.goto("{step["url"]}", wait_until="domcontentloaded")')
                lines.append(f'        await asyncio.sleep(1)')
            elif step["action"] == "click":
                lines.append(f'        await page.click("{step["selector"]}")')
                lines.append(f'        await asyncio.sleep(1)')
            elif step["action"] == "type":
                # Check if text looks like it should be an env var (passwords etc)
                text_val = step["text"]
                if any(word in step["selector"].lower() for word in ["password", "pass", "secret", "token"]):
                    lines.append(f'        await page.fill("{step["selector"]}", os.environ.get("SITE_PASSWORD", ""))')
                elif any(word in step["selector"].lower() for word in ["user", "email", "login"]):
                    lines.append(f'        await page.fill("{step["selector"]}", os.environ.get("SITE_USERNAME", ""))')
                else:
                    lines.append(f'        await page.fill("{step["selector"]}", "{text_val}")')
                lines.append(f'        await asyncio.sleep(0.5)')
            elif step["action"] == "scroll":
                dist = 500 if step["direction"] == "down" else -500
                lines.append(f'        await page.evaluate("window.scrollBy(0, {dist})")')
                lines.append(f'        await asyncio.sleep(0.5)')
            elif step["action"] == "hover":
                lines.append(f'        await page.hover("{step["selector"]}")')
                lines.append(f'        await asyncio.sleep(0.5)')
            elif step["action"] == "select":
                lines.append(f'        await page.select_option("{step["selector"]}", "{step["value"]}")')
                lines.append(f'        await asyncio.sleep(0.5)')
            lines.append('')

        lines.extend([
            '        # Add any final actions here',
            '        result = "Automation completed successfully"',
            '        await browser.close()',
            '        return result',
            '',
            '',
            'if __name__ == "__main__":',
            '    result = asyncio.run(run_automation())',
            '    print(result)',
        ])

        return "\n".join(lines)
