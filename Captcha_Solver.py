import httpx
import asyncio
import os

CAPSOLVER_API_KEY = os.environ.get("CAPSOLVER_API_KEY", "")
CAPSOLVER_API = "https://api.capsolver.com"


async def solve_recaptcha_v2(site_url: str, site_key: str) -> str:
    """
    Solve a reCAPTCHA v2 challenge via CapSolver.
    Returns the g-recaptcha-response token.
    """
    async with httpx.AsyncClient(timeout=120) as client:
        # Step 1: Create the task
        resp = await client.post(f"{CAPSOLVER_API}/createTask", json={
            "clientKey": CAPSOLVER_API_KEY,
            "task": {
                "type": "ReCaptchaV2TaskProxyLess",
                "websiteURL": site_url,
                "websiteKey": site_key,
            }
        })
        data = resp.json()
        if data.get("errorId", 1) != 0:
            raise Exception(f"CapSolver createTask error: {data.get('errorDescription', data)}")

        task_id = data["taskId"]

        # Step 2: Poll for the result
        for _ in range(60):  # poll for up to ~2 minutes
            await asyncio.sleep(2)
            resp = await client.post(f"{CAPSOLVER_API}/getTaskResult", json={
                "clientKey": CAPSOLVER_API_KEY,
                "taskId": task_id,
            })
            result = resp.json()
            if result.get("status") == "ready":
                return result["solution"]["gRecaptchaResponse"]
            elif result.get("status") == "processing":
                continue
            else:
                raise Exception(f"CapSolver error: {result.get('errorDescription', result)}")

        raise Exception("CapSolver timed out after 2 minutes")


async def solve_hcaptcha(site_url: str, site_key: str) -> str:
    """
    Solve an hCaptcha challenge via CapSolver.
    Returns the h-captcha-response token.
    """
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{CAPSOLVER_API}/createTask", json={
            "clientKey": CAPSOLVER_API_KEY,
            "task": {
                "type": "HCaptchaTaskProxyLess",
                "websiteURL": site_url,
                "websiteKey": site_key,
            }
        })
        data = resp.json()
        if data.get("errorId", 1) != 0:
            raise Exception(f"CapSolver createTask error: {data.get('errorDescription', data)}")

        task_id = data["taskId"]

        for _ in range(60):
            await asyncio.sleep(2)
            resp = await client.post(f"{CAPSOLVER_API}/getTaskResult", json={
                "clientKey": CAPSOLVER_API_KEY,
                "taskId": task_id,
            })
            result = resp.json()
            if result.get("status") == "ready":
                return result["solution"]["gRecaptchaResponse"]
            elif result.get("status") == "processing":
                continue
            else:
                raise Exception(f"CapSolver error: {result.get('errorDescription', result)}")

        raise Exception("CapSolver timed out after 2 minutes")


async def inject_captcha_token(page, token: str, captcha_type: str = "recaptcha"):
    """
    Inject the solved captcha token into the page so the form can submit.
    """
    if captcha_type == "recaptcha":
        await page.evaluate(f"""
            () => {{
                document.querySelector('#g-recaptcha-response').value = "{token}";
                // Also set in textarea if hidden
                const ta = document.querySelector('textarea[name="g-recaptcha-response"]');
                if (ta) ta.value = "{token}";
                // Trigger the callback if one exists
                if (typeof ___grecaptcha_cfg !== 'undefined') {{
                    const clients = ___grecaptcha_cfg.clients;
                    for (const key in clients) {{
                        const client = clients[key];
                        if (client && client.callback) client.callback("{token}");
                    }}
                }}
            }}
        """)
    elif captcha_type == "hcaptcha":
        await page.evaluate(f"""
            () => {{
                const resp = document.querySelector('[name="h-captcha-response"]');
                if (resp) resp.value = "{token}";
                const iframe = document.querySelector('iframe[src*="hcaptcha"]');
                if (iframe) {{
                    iframe.setAttribute('data-hcaptcha-response', "{token}");
                }}
            }}
        """)


async def detect_and_solve_captcha(page) -> str:
    """
    Auto-detect which captcha is on the page, solve it, and inject the token.
    Returns a status message.
    """
    url = page.url

    # Check for reCAPTCHA v2
    recaptcha_key = await page.evaluate("""
        () => {
            const el = document.querySelector('.g-recaptcha');
            return el ? el.getAttribute('data-sitekey') : null;
        }
    """)
    if recaptcha_key:
        token = await solve_recaptcha_v2(url, recaptcha_key)
        await inject_captcha_token(page, token, "recaptcha")
        return f"Solved reCAPTCHA v2 (sitekey: {recaptcha_key[:12]}...)"

    # Check for hCaptcha
    hcaptcha_key = await page.evaluate("""
        () => {
            const el = document.querySelector('.h-captcha');
            return el ? el.getAttribute('data-sitekey') : null;
        }
    """)
    if hcaptcha_key:
        token = await solve_hcaptcha(url, hcaptcha_key)
        await inject_captcha_token(page, token, "hcaptcha")
        return f"Solved hCaptcha (sitekey: {hcaptcha_key[:12]}...)"

    return "No captcha detected on this page."
