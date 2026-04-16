import os
from playwright.async_api import async_playwright

SITE_URL = os.environ.get("SITE_URL", "")
SITE_USERNAME = os.environ.get("SITE_USERNAME", "")
SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")


class WebAutomation:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def ensure_browser(self):
        """Start browser if not already running."""
        if not self.browser or not self.browser.is_connected():
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            self.page = await self.browser.new_page(
                viewport={"width": 1280, "height": 800}
            )

    async def screenshot(self, label: str = "screenshot") -> str:
        """Take a screenshot and return the file path."""
        path = f"/tmp/{label}.png"
        await self.page.screenshot(path=path, full_page=False)
        return path

    async def run_login(self) -> str:
        """
        Automated login sequence.
        Customize the selectors below to match YOUR target website.
        """
        await self.ensure_browser()
        await self.page.goto(SITE_URL, wait_until="networkidle", timeout=30000)

        # --- CUSTOMIZE THESE SELECTORS ---
        # Step 1: Fill in username/email
        await self.page.fill('input[name="username"]', SITE_USERNAME)

        # Step 2: Fill in password
        await self.page.fill('input[name="password"]', SITE_PASSWORD)

        # Step 3: Click the login/submit button
        await self.page.click('button[type="submit"]')

        # Step 4: Wait for the page to load after login
        await self.page.wait_for_load_state("networkidle", timeout=15000)

        return "Login complete."

    async def run_full_task(self) -> str:
        """
        Full automated task: login then do your steps.
        Customize the steps below for YOUR use case.
        """
        # Login first
        await self.run_login()

        # --- ADD YOUR STEPS HERE ---
        # Examples:
        #
        # Click a navigation link:
        #   await self.page.click('text=Dashboard')
        #   await self.page.wait_for_load_state("networkidle")
        #
        # Click a button by ID:
        #   await self.page.click('#submit-order')
        #
        # Select a dropdown option:
        #   await self.page.select_option('select#plan', 'premium')
        #
        # Wait for a specific element to appear:
        #   await self.page.wait_for_selector('.success-message', timeout=10000)
        #
        # Read text from the page:
        #   text = await self.page.inner_text('.result-panel')

        return "Full task completed."

    async def close(self):
        """Shut down the browser."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
