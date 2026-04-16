import discord
from discord.ext import commands
import os
import asyncio
from web_automation import WebAutomation

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Store active debug sessions per channel
sessions = {}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command(name="debug")
async def debug_mode(ctx, url: str = None):
    """Start an interactive debug session. Usage: !debug https://example.com"""
    if not url:
        await ctx.send("Please provide a URL. Usage: `!debug https://example.com`")
        return

    await ctx.send(f"🔧 Starting debug session for: `{url}`\nLaunching browser...")

    session = WebAutomation()
    sessions[ctx.channel.id] = session

    try:
        await session.start()
        screenshot_path = await session.goto(url)
        await ctx.send(
            "✅ Browser launched and page loaded! Here's what I see:",
            file=discord.File(screenshot_path)
        )
        await ctx.send(
            "**Debug commands you can use now:**\n"
            "```\n"
            "!click <selector>        - Click an element\n"
            "!type <selector> | text  - Type text into a field\n"
            "!goto <url>              - Navigate to a new URL\n"
            "!screenshot              - Take a fresh screenshot\n"
            "!html                    - Dump page HTML (truncated)\n"
            "!buttons                 - List all clickable buttons\n"
            "!inputs                  - List all input fields\n"
            "!links                   - List all links on the page\n"
            "!all                     - List buttons, inputs, and links\n"
            "!wait <seconds>          - Wait before next action\n"
            "!scroll <up|down>        - Scroll the page\n"
            "!select <selector> | val - Select dropdown option\n"
            "!hover <selector>        - Hover over an element\n"
            "!text <selector>         - Get text content of element\n"
            "!url                     - Show current page URL\n"
            "!export                  - Export recorded steps as code\n"
            "!stop                    - End the debug session\n"
            "```"
        )
    except Exception as e:
        await ctx.send(f"❌ Failed to start: {e}")
        await session.stop()
        sessions.pop(ctx.channel.id, None)


@bot.command(name="click")
async def click_element(ctx, *, selector: str):
    """Click an element. Examples: !click #submit  |  !click text=Login"""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    try:
        screenshot_path = await session.click(selector)
        await ctx.send(
            f"🖱️ Clicked `{selector}`. Here's what happened:",
            file=discord.File(screenshot_path)
        )
    except Exception as e:
        await ctx.send(f"❌ Click failed: {e}")
        screenshot_path = await session.screenshot()
        await ctx.send("Current page state:", file=discord.File(screenshot_path))


@bot.command(name="type")
async def type_text(ctx, *, args: str):
    """Type into a field. Usage: !type input[name='email'] | hello@test.com"""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    if "|" not in args:
        await ctx.send("Usage: `!type <selector> | <text>`\nExample: `!type input[name='email'] | hello@test.com`")
        return

    selector, text = args.split("|", 1)
    selector = selector.strip()
    text = text.strip()

    try:
        screenshot_path = await session.type_text(selector, text)
        await ctx.send(
            f"⌨️ Typed into `{selector}`. Here's the result:",
            file=discord.File(screenshot_path)
        )
    except Exception as e:
        await ctx.send(f"❌ Type failed: {e}")


@bot.command(name="goto")
async def goto_url(ctx, url: str):
    """Navigate to a URL. Usage: !goto https://example.com/dashboard"""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    try:
        screenshot_path = await session.goto(url)
        await ctx.send(
            f"🌐 Navigated to `{url}`:",
            file=discord.File(screenshot_path)
        )
    except Exception as e:
        await ctx.send(f"❌ Navigation failed: {e}")


@bot.command(name="screenshot")
async def take_screenshot(ctx):
    """Take a screenshot of the current page."""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    screenshot_path = await session.screenshot()
    await ctx.send("📸 Current page:", file=discord.File(screenshot_path))


@bot.command(name="html")
async def dump_html(ctx):
    """Dump the page HTML (truncated to fit Discord)."""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    html = await session.get_html()
    # Truncate to fit Discord's 2000 char message limit
    if len(html) > 1900:
        html = html[:1900] + "\n... (truncated)"
    await ctx.send(f"```html\n{html}\n```")


@bot.command(name="buttons")
async def list_buttons(ctx):
    """List all clickable buttons on the page."""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    elements = await session.list_elements("button, input[type='submit'], input[type='button'], [role='button']")
    if not elements:
        await ctx.send("No buttons found on this page.")
        return

    msg = "**🔘 Buttons found:**\n```\n"
    for el in elements[:25]:
        msg += f"  {el}\n"
    msg += "```"
    if len(msg) > 2000:
        msg = msg[:1950] + "\n... (truncated)```"
    await ctx.send(msg)


@bot.command(name="inputs")
async def list_inputs(ctx):
    """List all input fields on the page."""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    elements = await session.list_elements("input, textarea, select")
    if not elements:
        await ctx.send("No input fields found on this page.")
        return

    msg = "**📝 Input fields found:**\n```\n"
    for el in elements[:25]:
        msg += f"  {el}\n"
    msg += "```"
    if len(msg) > 2000:
        msg = msg[:1950] + "\n... (truncated)```"
    await ctx.send(msg)


@bot.command(name="links")
async def list_links(ctx):
    """List all links on the page."""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    elements = await session.list_elements("a[href]")
    if not elements:
        await ctx.send("No links found on this page.")
        return

    msg = "**🔗 Links found:**\n```\n"
    for el in elements[:25]:
        msg += f"  {el}\n"
    msg += "```"
    if len(msg) > 2000:
        msg = msg[:1950] + "\n... (truncated)```"
    await ctx.send(msg)


@bot.command(name="all")
async def list_all(ctx):
    """List all interactive elements on the page."""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    buttons = await session.list_elements("button, input[type='submit'], input[type='button'], [role='button']")
    inputs = await session.list_elements("input:not([type='submit']):not([type='button']):not([type='hidden']), textarea, select")
    links = await session.list_elements("a[href]")

    msg = ""
    if buttons:
        msg += "**🔘 Buttons:**\n```\n"
        for el in buttons[:10]:
            msg += f"  {el}\n"
        msg += "```\n"
    if inputs:
        msg += "**📝 Inputs:**\n```\n"
        for el in inputs[:10]:
            msg += f"  {el}\n"
        msg += "```\n"
    if links:
        msg += "**🔗 Links:**\n```\n"
        for el in links[:10]:
            msg += f"  {el}\n"
        msg += "```\n"

    if not msg:
        msg = "No interactive elements found."

    if len(msg) > 2000:
        msg = msg[:1950] + "\n... (truncated)```"
    await ctx.send(msg)


@bot.command(name="wait")
async def wait_seconds(ctx, seconds: float = 2):
    """Wait a number of seconds. Usage: !wait 3"""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    await ctx.send(f"⏳ Waiting {seconds} seconds...")
    await asyncio.sleep(seconds)
    screenshot_path = await session.screenshot()
    await ctx.send(f"Done waiting. Current page:", file=discord.File(screenshot_path))


@bot.command(name="scroll")
async def scroll_page(ctx, direction: str = "down"):
    """Scroll the page. Usage: !scroll down  or  !scroll up"""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    screenshot_path = await session.scroll(direction)
    await ctx.send(f"📜 Scrolled {direction}:", file=discord.File(screenshot_path))


@bot.command(name="hover")
async def hover_element(ctx, *, selector: str):
    """Hover over an element. Usage: !hover .menu-item"""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    try:
        screenshot_path = await session.hover(selector)
        await ctx.send(f"🎯 Hovering over `{selector}`:", file=discord.File(screenshot_path))
    except Exception as e:
        await ctx.send(f"❌ Hover failed: {e}")


@bot.command(name="select")
async def select_option(ctx, *, args: str):
    """Select a dropdown option. Usage: !select select#country | US"""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    if "|" not in args:
        await ctx.send("Usage: `!select <selector> | <value>`")
        return

    selector, value = args.split("|", 1)
    try:
        screenshot_path = await session.select_option(selector.strip(), value.strip())
        await ctx.send(f"✅ Selected `{value.strip()}` in `{selector.strip()}`:", file=discord.File(screenshot_path))
    except Exception as e:
        await ctx.send(f"❌ Select failed: {e}")


@bot.command(name="text")
async def get_text(ctx, *, selector: str):
    """Get the text content of an element. Usage: !text .header-title"""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    try:
        text = await session.get_text(selector)
        if len(text) > 1900:
            text = text[:1900] + "... (truncated)"
        await ctx.send(f"📄 Text from `{selector}`:\n```\n{text}\n```")
    except Exception as e:
        await ctx.send(f"❌ Failed to get text: {e}")


@bot.command(name="url")
async def current_url(ctx):
    """Show the current page URL."""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    url = await session.get_url()
    await ctx.send(f"🌐 Current URL: `{url}`")


@bot.command(name="export")
async def export_steps(ctx):
    """Export all recorded steps as a ready-to-use Python script."""
    session = sessions.get(ctx.channel.id)
    if not session:
        await ctx.send("No active session. Start one with `!debug <url>`")
        return

    code = session.export_code()
    if len(code) > 1900:
        # Save to file and upload instead
        with open("/tmp/exported_automation.py", "w") as f:
            f.write(code)
        await ctx.send(
            "📦 Exported automation script (too long for message):",
            file=discord.File("/tmp/exported_automation.py")
        )
    else:
        await ctx.send(f"📦 **Exported automation script:**\n```python\n{code}\n```")


@bot.command(name="stop")
async def stop_session(ctx):
    """End the debug session and close the browser."""
    session = sessions.pop(ctx.channel.id, None)
    if not session:
        await ctx.send("No active session to stop.")
        return

    await session.stop()
    await ctx.send("🛑 Debug session ended. Browser closed.")


# Cleanup on bot shutdown
@bot.event
async def on_disconnect():
    for session in sessions.values():
        try:
            await session.stop()
        except:
            pass
    sessions.clear()


bot.run(TOKEN)
