# HiveMom Bot: Dark War Survival Assistant

This repository contains the full source code and deployment configuration for the HiveMom Discord bot, specifically tailored for Dark War: Survival (State 161).

##  Identified Tasks (TODO)

The following items should be addressed by the new maintainer:

1.  **Fix Orphaned Logic**: Move the welcome DM block (lines 169-183) into a proper \on_member_join\ event handler.
2.  **Rich Embeds**: Upgrade guide commands (\/vsduel\, \/alliancetech\, etc.) to use \discord.Embed\ messages.
3.  **Unified Roles**: Standardize admin role checks across the bot using the \ADMIN_ROLES\ environment variable.

---

##  Setup & Deployment Instructions (Linux)

###  Prerequisites
- **Python 3.11+**
- **Docker & Docker Compose**
- **Discord Bot Token**: Ensure \SERVER MEMBERS\, \PRESENCE\, and \MESSAGE CONTENT\ intents are enabled in the [Discord Developer Portal](https://discord.com/developers/applications).

###  Environment Configuration
Create a \.env\ file in the root directory:
\\\env
DISCORD_BOT_TOKEN=your_token_here
GUILD_ID=your_server_id
DISCORD_WEBHOOK_URL=your_webhook_url
ADMIN_ROLES=R5 & R4,R5,R4,Admin,admin,R5/R4
\\\

###  Deploying with Docker
\\\ash
# Build and start the container
docker compose up -d --build

# Monitor bot logs
docker compose logs -f
\\\

###  Manual Deployment (No Docker)
\\\ash
pip install -r requirements.txt
python dwbot.py
\\\

---

##  File Manifest
- \dwbot.py\: Main logic & slash commands.
- \equirements.txt\: Python dependencies.
- \docker-compose.yml\ & \Dockerfile\: Containerization setup.
- \last_seen.txt\: Internal state tracking.
- \data/\: Local storage for persistence.
