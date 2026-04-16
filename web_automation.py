import os
import shutil
from playwright.async_api import async_playwright
from captcha_solver import detect_and_solve_captcha

SITE_URL = os.environ.get("SITE_URL", "")
SITE_USERNAME = os.environ.get("SITE_USERNAME", "")
SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")


import subprocess


def find_chromium_path() -> str:
    """Find the system-installed Chromium binary by searching everywhere."""
    # 1. Try common locations and PATH
    candidates = [
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/nix/var/nix/profiles/default/bin/chromium",
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            print(f"[Chromium] Found at: {path}")
            return path

    # 2. Search the Nix store (Railway uses Nix)
    try:
        result = subprocess.run(
            ["find", "/nix", "-name", "chromium", "-type", "f"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().split("\n"):
            if line and os.path.isfile(line) and os.access(line, os.X_OK):
                print(f"[Chromium] Found in Nix store: {line}")
                return line
    except Exception as e:
        print(f"[Chromium] Nix search failed: {e}")

    # 3. Try 'which' via shell as a last resort
    try:
        result = subprocess.run(
            ["bash", "-lc", "which chromium || which chromium-browser"],
            capture_output=True, text=True, timeout=5
        )
        path = result.stdout.strip()
        if path and os.path.isfile(path):
            print(f"[Chromium] Found via shell: {path}")
            return path
    except Exception:
        pass

    # 4. Let Playwright try its own default (no executable_path)
    print("[Chromium] Not found anywhere, will let Playwright try its default")
    return None


class WebAutomation:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def ensure_browser(self):
        """Start browser using system-installed Chromium."""
        if not self.browser or not self.browser.is_connected():
            self.playwright = await async_playwright().start()
            chromium_path = find_chromium_path()
            launch_args = {
                "headless": True,
                "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            }
            if chromium_path:
                launch_args["executable_path"] = chromium_path
            self.browser = await self.playwright.chromium.launch(**launch_args)
            self.page = await self.browser.new_page(
                viewport={"width": 1280, "height": 800}
            )

    async def screenshot(self, label: str = "screenshot") -> str:
        """Take a screenshot and return the file path."""
        path = f"/tmp/{label}.png"
        await self.page.screenshot(path=path, full_page=False)
        return path

    async def solve_captcha(self) -> str:
        """Detect and solve any captcha on the current page."""
        return await detect_and_solve_captcha(self.page)

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

        # Step 3: Solve captcha if present
        captcha_result = await self.solve_captcha()

        # Step 4: Click the login/submit button
        await self.page.click('button[type="submit"]')

        # Step 5: Wait for the page to load after login
        await self.page.wait_for_load_state("networkidle", timeout=15000)

        return f"Login complete. Captcha: {captcha_result}"

    async def run_full_task(self) -> str:
        """
        Full automated task: login then do your steps.
        Customize the steps below for YOUR use case.
        """
        await self.run_login()

        # --- ADD YOUR STEPS HERE ---
        # await self.page.click('text=Dashboard')
        # await self.page.wait_for_load_state("networkidle")

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
