import discord
from discord.ext import commands
import os
from web_automation import WebAutomation

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Persistent browser session so you can interact step-by-step
web = WebAutomation()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command(name="goto")
async def goto(ctx, url: str):
    """Navigate to a URL and screenshot it. Usage: !goto https://example.com"""
    await ctx.send(f"Navigating to `{url}`...")
    try:
        await web.ensure_browser()
        await web.page.goto(url, wait_until="networkidle", timeout=30000)
        path = await web.screenshot("goto")
        await ctx.send(
            f"Loaded: **{await web.page.title()}**",
            file=discord.File(path),
        )
    except Exception as e:
        await ctx.send(f"Error: {e}")


@bot.command(name="screenshot")
async def screenshot(ctx):
    """Take a screenshot of what the bot currently sees."""
    if not web.page:
        await ctx.send("No browser open yet. Use `!goto <url>` first.")
        return
    try:
        path = await web.screenshot("current")
        title = await web.page.title()
        url = web.page.url
        await ctx.send(
            f"**Current page:** {title}\n**URL:** {url}",
            file=discord.File(path),
        )
    except Exception as e:
        await ctx.send(f"Error taking screenshot: {e}")


@bot.command(name="click")
async def click(ctx, *, selector: str):
    """Click an element. Usage: !click #submit-btn  OR  !click text=Log In"""
    if not web.page:
        await ctx.send("No browser open yet. Use `!goto <url>` first.")
        return
    try:
        await web.page.click(selector, timeout=10000)
        await web.page.wait_for_load_state("networkidle", timeout=15000)
        path = await web.screenshot("after_click")
        await ctx.send(
            f"Clicked `{selector}`. Here's the result:",
            file=discord.File(path),
        )
    except Exception as e:
        await ctx.send(f"Could not click `{selector}`: {e}")


@bot.command(name="type")
async def type_text(ctx, selector: str, *, text: str):
    """Type into a field. Usage: !type input[name=email] myemail@test.com"""
    if not web.page:
        await ctx.send("No browser open yet. Use `!goto <url>` first.")
        return
    try:
        await web.page.fill(selector, text)
        path = await web.screenshot("after_type")
        await ctx.send(
            f"Typed into `{selector}`. Here's the result:",
            file=discord.File(path),
        )
    except Exception as e:
        await ctx.send(f"Could not type into `{selector}`: {e}")


@bot.command(name="html")
async def html(ctx):
    """Dump the current page's key elements (buttons, links, inputs) so you know what selectors to use."""
    if not web.page:
        await ctx.send("No browser open yet. Use `!goto <url>` first.")
        return
    try:
        elements = await web.page.evaluate("""
            () => {
                const results = [];
                const selectors = 'a, button, input, select, textarea, [role="button"]';
                document.querySelectorAll(selectors).forEach((el, i) => {
                    if (i > 50) return;  // cap at 50 elements
                    const tag = el.tagName.toLowerCase();
                    const id = el.id ? `#${el.id}` : '';
                    const name = el.name ? `[name="${el.name}"]` : '';
                    const cls = el.className && typeof el.className === 'string'
                        ? '.' + el.className.trim().split(/\s+/).join('.')
                        : '';
                    const text = el.innerText?.trim().substring(0, 50) || '';
                    const type = el.type ? `[type="${el.type}"]` : '';
                    const href = el.href ? ` → ${el.href.substring(0, 80)}` : '';
                    const placeholder = el.placeholder ? ` placeholder="${el.placeholder}"` : '';
                    results.push(
                        `<${tag}${id}${name}${type}${cls}${placeholder}> "${text}"${href}`
                    );
                });
                return results;
            }
        """)
        if not elements:
            await ctx.send("No interactive elements found on this page.")
            return

        msg = "**Interactive elements on this page:**\n```\n"
        msg += "\n".join(elements)
        msg += "\n```"

        # Discord has a 2000 char limit
        if len(msg) > 1900:
            msg = msg[:1900] + "\n... (truncated)```"

        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"Error reading elements: {e}")


@bot.command(name="login")
async def login(ctx):
    """Run the automated login using SITE_URL, SITE_USERNAME, SITE_PASSWORD env vars."""
    await ctx.send("Starting login sequence...")
    try:
        result = await web.run_login()
        path = await web.screenshot("after_login")
        await ctx.send(result, file=discord.File(path))
    except Exception as e:
        await ctx.send(f"Login failed: {e}")


@bot.command(name="run")
async def run_task(ctx):
    """Run the full automated task (login + steps). Customize web_automation.py for this."""
    await ctx.send("Running full task...")
    try:
        result = await web.run_full_task()
        path = await web.screenshot("final")
        await ctx.send(result, file=discord.File(path))
    except Exception as e:
        await ctx.send(f"Task failed: {e}")


@bot.command(name="close")
async def close_browser(ctx):
    """Close the browser session."""
    await web.close()
    await ctx.send("Browser closed.")


@bot.command(name="captcha")
async def solve_captcha(ctx):
    """Detect and solve a captcha on the current page."""
    if not web.page:
        await ctx.send("No browser open yet. Use `!goto <url>` first.")
        return
    try:
        await ctx.send("Detecting captcha... this may take up to 2 minutes.")
        result = await web.solve_captcha()
        path = await web.screenshot("after_captcha")
        await ctx.send(f"{result}", file=discord.File(path))
    except Exception as e:
        await ctx.send(f"Captcha solving failed: {e}")


@bot.command(name="help_bot")
async def help_bot(ctx):
    """Show all available commands."""
    help_text = """
**Available Commands:**
`!goto <url>` — Open a URL and screenshot it
`!screenshot` — See what the bot currently sees
`!html` — List all clickable elements and input fields on the page
`!click <selector>` — Click an element (e.g. `!click #login-btn` or `!click text=Submit`)
`!type <selector> <text>` — Type into a field (e.g. `!type input[name=email] me@test.com`)
`!captcha` — Detect and solve a captcha on the current page
`!login` — Run the automated login sequence
`!run` — Run the full automated task
`!close` — Close the browser
    """
    await ctx.send(help_text)


bot.run(TOKEN)
