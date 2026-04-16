# Discord Web Automation Bot

A Discord bot with an interactive debug mode that lets you control a headless browser through Discord commands. Navigate websites, inspect elements, click buttons, fill forms — all while seeing screenshots of what the bot sees. Then export your steps as a ready-to-use automation script.

## Setup

### 1. Discord Developer Portal
1. Go to https://discord.com/developers/applications
2. Create a new application → go to **Bot** tab → **Add Bot**
3. Enable **Message Content Intent** under Privileged Gateway Intents
4. Copy the **Bot Token**
5. Go to **OAuth2 → URL Generator**, select `bot` scope + permissions (Send Messages, Attach Files, Read Message History)
6. Use the generated URL to invite the bot to your server

### 2. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/my-discord-bot.git
git branch -M main
git push -u origin main
```

### 3. Deploy on Railway
1. Go to https://railway.app and sign in with GitHub
2. New Project → Deploy from GitHub Repo → select this repo
3. Add environment variable: `DISCORD_TOKEN` = your bot token
4. Deploy — Railway will install Chromium and Playwright automatically

## Usage

### Interactive Debug Mode
```
!debug https://example.com/login
```
This opens a browser, navigates to the URL, and sends you a screenshot.

### Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!debug <url>` | Start a session | `!debug https://example.com` |
| `!screenshot` | See current page | `!screenshot` |
| `!buttons` | List all buttons | `!buttons` |
| `!inputs` | List all input fields | `!inputs` |
| `!links` | List all links | `!links` |
| `!all` | List all interactive elements | `!all` |
| `!click <selector>` | Click an element | `!click #login-btn` |
| `!type <sel> \| text` | Type into a field | `!type input[name='email'] \| me@test.com` |
| `!select <sel> \| val` | Select dropdown option | `!select #country \| US` |
| `!hover <selector>` | Hover over element | `!hover .dropdown` |
| `!scroll <dir>` | Scroll up or down | `!scroll down` |
| `!text <selector>` | Get element's text | `!text .welcome-msg` |
| `!url` | Show current URL | `!url` |
| `!html` | Dump page HTML | `!html` |
| `!wait <sec>` | Wait N seconds | `!wait 3` |
| `!goto <url>` | Navigate to new URL | `!goto https://example.com/dashboard` |
| `!export` | Export steps as Python code | `!export` |
| `!stop` | End session | `!stop` |

### Workflow
1. `!debug https://site.com/login` — see the login page
2. `!inputs` — find the form fields and their selectors
3. `!type input[name='email'] | myemail@test.com` — fill in email
4. `!type input[name='password'] | mypassword` — fill in password
5. `!buttons` — find the submit button
6. `!click #submit` — click it
7. `!screenshot` — verify you're logged in
8. `!export` — get a Python script of everything you just did
9. `!stop` — close the browser

## Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | Yes | Your Discord bot token |
