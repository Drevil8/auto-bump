import asyncio
from playwright.async_api import async_playwright
import os

# Pull credentials from environment variables (NEVER hardcode these)
SITE_URL = os.environ.get("SITE_URL")          # e.g. https://example.com/login
SITE_USERNAME = os.environ.get("SITE_USERNAME")
SITE_PASSWORD = os.environ.get("SITE_PASSWORD")

async def run_web_task():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1. Go to the login page
        await page.goto(SITE_URL)

        # 2. Fill in login form (update selectors to match YOUR site)
        await page.fill('input[name="username"]', SITE_USERNAME)
        await page.fill('input[name="password"]', SITE_PASSWORD)
        await page.click('button[type="submit"]')

        # 3. Wait for navigation after login
        await page.wait_for_load_state("networkidle")

        # 4. Perform your steps (customize these)
        # Example: click a button, scrape text, etc.
        # await page.click('a#some-link')
        # data = await page.inner_text('.some-class')

        result = "Task completed successfully"

        await browser.close()
        return result
