# HiveMom Bot: Dark War Survival Assistant

This repository contains the full source code and deployment configuration for the HiveMom Discord bot, specifically tailored for Dark War: Survival (DWSI - https://discord.com/channels/1321252815515156620/).

## Identified Tasks (TODO)

The following are latest updates:
-  **Fixed Orphaned Logic**: Moved the welcome DM block (lines 169-183) into a proper \on_member_join\ event handler.

Future updates:
-  **Rich Embeds**: Upgrade guide commands (\/vsduel\, \/alliancetech\, etc.) to use \discord.Embed\ messages.
- **Unified Roles**: Standardize admin role checks across the bot using the \ADMIN_ROLES\ environment variable.

---
# HiveMom Bot: Dark War Survival Assistant

HiveMom is a specialized Discord bot designed to assist "Dark War: Survival" communities with event schedules, daily task reminders, and server moderation.

This bot was originally created for the **DWSI community server** ([Visit DWSI](https://discord.com/channels/1321252815515156620)). It is now available as a template for other server owners to deploy for their own Alliances.

---

## 🚀 Getting Started

### 1. Discord Developer Portal Setup

To run this bot, you first need to create a Bot application:

1.  Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2.  Click **"New Application"** and give it a name (e.g., "Alliance Assistant").
3.  On the left sidebar, click **"Bot"**.
4.  **Crucial: Enable Gateway Intents**. Under the "Privileged Gateway Intents" section, toggle **ON**:
    - [x] Presence Intent
    - [x] Server Members Intent
    - [x] Message Content Intent
5.  Click **"Reset Token"** (or "Copy Token") to get your `DISCORD_BOT_TOKEN`. Keep this secret!
6.  Go to **"OAuth2" -> "URL Generator"**:
    - Select Scopes: `bot`, `applications.commands`.
    - Select Bot Permissions: `Administrator` (or specific permissions like `Manage Roles`, `Manage Channels`, `Send Messages`).
    - Copy the generated URL and paste it into your browser to invite the bot to your server.

### 2. Physical Setup (Linux/Pi)

#### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (Recommended)

#### Environment Configuration

Create a `.env` file in the root directory and fill in your details:

| Variable               | Description                          | How to get it                                 |
| :--------------------- | :----------------------------------- | :-------------------------------------------- |
| `DISCORD_BOT_TOKEN`    | Your unique bot token.               | Discord Dev Portal (Bot tab).                 |
| `GUILD_ID`             | Your Discord Server ID.              | Right-click Server Name -> "Copy Server ID"\* |
| `DISCORD_WEBHOOK_URL`  | (Optional) For specialized logging.  | Server Settings -> Integrations -> Webhooks.  |
| `ADMIN_ROLES`          | Comma-separated list of admin roles. | e.g. `R5,R4,Admin`                            |
| `ANNOUNCEMENT_CHANNEL` | Channel for daily reminders.         | Use the exact name (e.g., `announcements`).   |

_\*Note: You must have "Developer Mode" enabled in Discord User Settings -> Advanced._

---

## 🛠 Deployment

### Option A: Using Docker (Recommended)

This is the easiest way to ensure all dependencies are handled correctly.

```bash
# Build and start the container
docker compose up -d --build

# View logs to confirm connection
docker compose logs -f
```

### Option B: Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python dwbot.py
```
---
## 📂 File Manifest

- `dwbot.py`: Main bot logic and splash command definitions.
- `requirements.txt`: Python libraries required.
- `docker-compose.yml` & `Dockerfile`: Environment containerization.
- `data/`: Local directory for database/state persistence.

---

## 🛡️ Credits & Support

Developed for the **Dark War: Survival** community.
Special thanks to the **DWSI** team and my original State #161 for the original concept and idea.
