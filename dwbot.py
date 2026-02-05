import os
import discord
import datetime
import time
import atexit
import asyncio
import signal
import logging
from discord import app_commands, Intents, Permissions
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

# Enable necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

# Configuration - Moved to .env or a config file for better management
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # Using environment variable
GUILD_ID = os.getenv("GUILD_ID")  # Using environment variable
LAST_SEEN_FILE = "last_seen.txt"
ANNOUNCEMENT_CHANNEL_NAME = os.getenv("ANNOUNCEMENT_CHANNEL", "updates") # Generic channel name
PUBLIC_CHAT_CHANNEL_NAME = os.getenv("GAME_CHAT_CHANNEL", "game-chat")
BOT_CHAT_CHANNEL_NAME = os.getenv("BOT_SPAM_CHANNEL", "bot-spam")
MUTE_ROLE_NAME = "Punishment Role"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HiveMom")

class HiveMomBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False # Add a flag to track if slash commands are synced

    async def setup_hook(self):
        await super().setup_hook()
        # Ensure the guild ID is valid before attempting to sync
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            self.synced = True
            print(f"✅ Slash commands synced to guild ID: {GUILD_ID}.")
        else:
            print("⚠️ GUILD_ID is not set. Slash commands will not be synced.")

    async def close(self):
        # Save last seen on shutdown
        save_last_seen()
        await super().close()

bot = HiveMomBot()

# Save last seen timestamp
def save_last_seen():
    try:
        with open(LAST_SEEN_FILE, "w") as f:
            f.write(str(int(time.time())))
        logger.info("Last seen timestamp saved.")
    except Exception as e:
        logger.error(f"❌ Error in save_last_seen: {e}")

atexit.register(save_last_seen) # This is still needed

# Handle shutdown signals
def handle_shutdown(signum, frame):
    logger.info("Shutting down bot...")
    save_last_seen()
    asyncio.create_task(bot.close()) # Close bot properly

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# Role check for Admins
def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member):
            member = interaction.guild.get_member(interaction.user.id)

        if member is None:
            logger.warning("Member not found in guild.")
            return False

        # Fetch allowed roles from environment variables or a config file
        allowed_roles = os.getenv("ADMIN_ROLES", "R5 & R4,R5,R4,Admin,admin,R5/R4").split(",")
        allowed_roles = [role.strip() for role in allowed_roles]  # Clean up roles

        role_names = [role.name for role in member.roles]
        logger.debug(f"Roles for {member.name}: {role_names}")
        return any(role in role_names for role in allowed_roles)
    return app_commands.check(predicate)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
    else:
        logger.exception(f"App command error: {error}") # Log the full exception
        await interaction.response.send_message("❌ An error occurred while processing the command.", ephemeral=True)

# Scheduled tasks
@tasks.loop(minutes=1)
async def scheduled_reminders():
    try:
        now = datetime.datetime.utcnow().strftime("%H:%M")
        if now == "00:00": # UTC time
            if not GUILD_ID:
                logger.warning("GUILD_ID is not set, skipping scheduled reminders.")
                return

            guild = bot.get_guild(int(GUILD_ID))
            if guild:
                channel = discord.utils.get(guild.text_channels, name=ANNOUNCEMENT_CHANNEL_NAME)
                if channel and channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(
                            "⏰ Reset in 2 hours (00:00 Server Time)!\n"
                            "⚔️ Make sure you've completed all your daily tasks before reset! \n"
                            "✅ Sign into the game!\n"
                            "✅ 5x Zombie/Boomer kills\n"
                            "✅ Radar missions\n"
                            "✅ Daily free (Gold Ticket) Hero Recruitment\n"
                            "✅ Arena Battles\n"
                            "✅ Check Events tab for new events\n"
                            "✅ Alliance Donations & Missions"
                        )
                    except discord.Forbidden:
                        logger.error(f"Could not send scheduled reminder to #{ANNOUNCEMENT_CHANNEL_NAME} due to permissions.")
                    except Exception as e:
                        logger.exception(f"Exception while sending scheduled reminder: {e}") # Log full exception
                else:
                    logger.warning(f"Could not send scheduled reminder to #{ANNOUNCEMENT_CHANNEL_NAME} in guild {guild.name}.")
    except Exception as e:
        logger.error(f"❌ Error in scheduled_reminders: {e}")



@tasks.loop(minutes=1)
async def reset_reminder():
    try:
        now = datetime.datetime.utcnow().strftime("%H:%M")
        if now == "01:55":  # UTC time for 20:55 CST & 23:55 in-game server time
            if not GUILD_ID:
                logger.warning("GUILD_ID is not set, skipping reset reminder.")
                return

            guild = bot.get_guild(int(GUILD_ID))
            if guild:
                channel = discord.utils.get(guild.text_channels, name=ANNOUNCEMENT_CHANNEL_NAME)
                if channel and channel.permissions_for(guild.me).send_messages:
                    await channel.send(
                        "🕛 5 minutes until **Daily Reset!**\n"
                        "✅ Sign into the game now to receive your daily rewards and participate in new events!\n"
                        "🎯 New tasks and events have begun.\n"
                        "📦 Be sure to check the Events tab and Alliance Missions!"
                    )
                else:
                    logger.warning(f"Could not send reset reminder to #{ANNOUNCEMENT_CHANNEL_NAME} in guild {guild.name}.")
    except Exception as e:
        logger.error(f"❌ Error in reset_reminder: {e}")


@bot.event
async def on_member_join(member):
    # Private welcome DM
    welcome_dm = (
        f"👋 Welcome to the Discord server, {member.name}!\n\n"
        "We’re here to grow together and help each other thrive.\n"
        "We work through integrity, growth, and mutual respect.\n\n"
        "**Discord server in-game expectations:**\n"
        "> ✅ Build, grow, and prepare\n"
        "Thanks for joining the Discord and helping us in building a strong community in Dark War: Survival!"
    )
    try:
        await member.send(welcome_dm)
    except discord.Forbidden:
        logger.warning(f"❌ Could not send DM to {member.name}. They may have DMs disabled.")
    except Exception as e:
        logger.error(f"❌ Error sending DM to {member.name}: {e}")


# ---- Slash Commands ----

# Admin Commands
@is_admin()
@bot.tree.command(name="hey", description="Test the bot responsiveness.")
async def slash_hey(interaction: discord.Interaction):
    await interaction.response.send_message("Hey I'm working here! **Hello World**", ephemeral=True)


@is_admin()
@bot.tree.command(name="dm", description="Send a custom DM to a mentioned user.")
@app_commands.describe(
    user="The user to send a DM to",
    message="The message to send"
)
async def dm(interaction: discord.Interaction, user: discord.Member, message: str):
    try:
        await user.send(
            f"📩 Message from {interaction.user.display_name}:\n\n{message}"
        )
        await interaction.response.send_message(
            f"✅ DM sent to {user.display_name}.", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            f"❌ Could not send DM to {user.display_name}. They may have DMs disabled.",
            ephemeral=True
        )


# Admin V.S. Event Schedule

@is_admin()
@bot.tree.command(name="vsschedule", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_vsschedule(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**The :crossed_swords: V.S. (Dual) Event Schedule:** \n"
        "**📅 Day 1 – Shelter Expansion** \n"
        "👾**Save**: _Radars, Gears, Power Cores, Hero Equipment Lucky Chests, Prime Recruit (Gold Tickets), and ALL hero fragments_  \n\n"
        "🏗>> **Construction** – Upgrade and complete any structures in your settlement\n"
        "📜>> **Wisdom Medals** – Use to boost progression in Research Center Duel, Battle Strategy, etc.\n"
        "🔬>> **Research** – Start/Upgrade and finish tech trees. _Stack research with Wisdom Medals for a boost in points!_\n"
        "⚙️>> **Speedups** – Construction and Research ONLY for Day 1.\n"
        "💰>> **Resource Gathering** – ALL DAY send trucks out: wood, iron, electricity, and bonus points for mint/coin.",
        ephemeral=False
    )

    await interaction.followup.send(
        "**📅 Day 2 – Hero Initiative**\n"
        "👾**Save**: _Gears, Power Cores, Wisdom Medals and Hero Equipment Lucky Chests_  \n\n"
        "📡 **Radar Missions** – Quick and easy — finish as many as possible.\n"
        "🎖>> **Prime Recruit** – Use all your Golden Tickets today!  \n"
        "🧩>> **Hero Fragments** – Promote (Star Rise) heroes by spending fragments (especially orange/purple).  \n"
        "🎯>> **Exclusive Equipment** – Star-rise your best gear (be cautious with resources) - Gained from micro-purchase.\n\n"
        "💡 **Pro Tip** 💡: Before reset into day 3, start troop training to complete **AFTER** reset to get a boost in points.",
        ephemeral=False
    )

    await interaction.followup.send(
        "**📅 Day 3 – Keep Progressing**\n"
        "👾**Save**: _ Radars (for tomorrow), Energy (Rally tomorrow), Gears, Wisdom Medals, and both Construction and Research speed-ups_\n\n"
        "🚚>> **S-tier Escort/Cargo Trucks** – Do S-tier for points.\n"
        "🕶>> **S-tier (orange) Shadow Calls Missions** – Prioritize orange missions for massive point boosts.\n"
        "🔋>> **Power Cores** – Use to upgrade orange hero equipment.\n"
        "🎁>> **Hero Equipment Lucky Chests** – Use saved chests to boost power. _Enhance equipment or attach to heroes._\n"
        "⚙️>> **Speedups** – Troop Training **ONLY** for Day 3.\n"
        "🪖>> **Training** – Always be training troops. Train mid-tier troops in bulk. Use speedups if you're in a rush.\n"
        "🔧>> **Red Equipment** – Orange gear must be level 100 and enhanced to level 10 using Power Cores.",
        ephemeral=False
    )

    await interaction.followup.send(
        "**📅 Day 4 – Arms Expert**\n"
        "**Save**: _Wisdom Medals, Power Cores, and ALL speedups_ \n\n"
        "📡>> **Radar Missions** – Quick and easy — finish as many as possible. \n"
        "🔩>> **Gears/Alloy/Blueprints** – Upgrade trucks. Don’t blow everything at once—start saving for reset too. \n"
        "💥>> **Rallies** – Start rallies and prioritize higher lever. \n"
        "      - Level point tiers: 5–7, 8–10, 11–13, 14–16, 17–19, and 20. \n\n"
        "🧟>> **Kill Roamers** – Aim for higher-level ones for better return. Use stamina wisely.\n"
        "⚙️>> **Speedups** – Troops, Construction and Research.\n"
        "🔧>> **Precision Parts** - Used at level 30.",
        ephemeral=False
    )

    await interaction.followup.send(
        "**📅 Day 5 – Holistic Growth**\n"
        "🧰>> **All Prior Tasks** – A mix of Gear, Power Cores, Hero star upgrades, wisdom medals, etc. \n"
        "🔋>> **Power Cores** – Use to upgrade orange hero equipment. \n"
        "📜>> **Wisdom Medals & Speedups** – Clean up remaining medals and use short boosts. \n"
        "🧩>> **Hero Fragments** – Promote (Star Rise) heroes by spending fragments (especially orange/purple). \n"
        "🎯>> **Exclusive Equipment** – Star-rise your best gear (be cautious with resources). \n"
        "🔧>> **Red Equipment** – Orange gear must be level 100 and enhanced to level 10.\n\n"
        "💡 **Pro Tip** 💡: Use leftover items from earlier days to boost V.S. points.",
        ephemeral=False
    )

    await interaction.followup.send(
        "**📅 Day 6 – Enemy Buster**\n"
        "🚚>> **S-tier Escort/Cargo Trucks** – Do S-tier for points. \n"
        "🕶>> **S-tier (orange) Shadow Calls Missions** – Prioritize orange missions for massive point boosts. \n"
        "⚙️>> **Speedups** – Troops, Construction and Research. Start saving if you can get away with it. \n"
        "🎯>> **Defeat Enemies** – PvP in your state and any cross-server invaders. \n"
        "💀>> **Units Lost** – Sacrifices during battles or rallies contribute here (plan wisely).\n"
        "💡 **Pro Tip** 💡: If you do not plan on participating **SHIELD** and send out trucks for Truck-4-Truck to rack up passive points.\n",
        ephemeral=False
    )

@is_admin()
@bot.tree.command(name="vs0", description="View the 0-Day V.S. (Dual) Event task schedule with tips.")
async def slash_vs0(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Reminder: :crossed_swords: V.S. (Dual) Event Starts at reset!**\n"
        "**Pro Tip**: Send trucks out to gather wood, iron, electricity and especially mint/coin NOW to get a boost after reset.\n\n",
        ephemeral=False
    )

@is_admin()
@bot.tree.command(name="vs1", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_vs1(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**The :crossed_swords: V.S. (Dual) Event Schedule:** \n"
        "**📅 Day 1 – Shelter Expansion** \n"
        "👾**Save**: _Radars, Gears, Power Cores, Hero Equipment Lucky Chests, Prime Recruit (Gold Tickets), and ALL hero fragments_  \n\n"
        "🏗>> **Construction** – Upgrade and complete any structures in your settlement\n"
        "📜>> **Wisdom Medals** – Use to boost progression in Research Center Duel, Battle Strategy, etc.\n"
        "🔬>> **Research** – Start/Upgrade and finish tech trees. _Stack research with Wisdom Medals for a boost in points!_\n"
        "⚙️>> **Speedups** – Construction and Research ONLY for Day 1.\n"
        "💰>> **Resource Gathering** – ALL DAY send trucks out: wood, iron, electricity, and bonus points for mint/coin.",
        ephemeral=False
    )

@is_admin()
@bot.tree.command(name="vs2", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_vs2(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📅 Day 2 – Hero Initiative**\n"
        "👾**Save**: _Gears, Power Cores, Wisdom Medals and Hero Equipment Lucky Chests_  \n\n"
        "📡 **Radar Missions** – Quick and easy — finish as many as possible.\n"
        "🎖>> **Prime Recruit** – Use all your Golden Tickets today!  \n"
        "🧩>> **Hero Fragments** – Promote (Star Rise) heroes by spending fragments (especially orange/purple).  \n"
        "🎯>> **Exclusive Equipment** – Star-rise your best gear (be cautious with resources) - Gained from micro-purchase.\n\n"
        "💡 **Pro Tip** 💡: Before reset into day 3, start troop training to complete **AFTER** reset to get a boost in points.",
        ephemeral=False
    )

@is_admin()
@bot.tree.command(name="vs3", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_vs3(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📅 Day 3 – Keep Progressing**\n"
        "👾**Save**: _ Radars (for tomorrow), Energy (Rally tomorrow), Gears, Wisdom Medals, and both Construction and Research speed-ups_\n\n"
        "🚚>> **S-tier Escort/Cargo Trucks** – Do S-tier for points.\n"
        "🕶>> **S-tier (orange) Shadow Calls Missions** – Prioritize orange missions for massive point boosts.\n"
        "🔋>> **Power Cores** – Use to upgrade orange hero equipment.\n"
        "🎁>> **Hero Equipment Lucky Chests** – Use saved chests to boost power. _Enhance equipment or attach to heroes._\n"
        "⚙️>> **Speedups** – Troop Training **ONLY** for Day 3.\n"
        "🪖>> **Training** – Always be training troops. Train mid-tier troops in bulk. Use speedups if you're in a rush.\n"
        "🔧>> **Red Equipment** – Orange gear must be level 100 and enhanced to level 10 using Power Cores.",
        ephemeral=False
    )

@is_admin()
@bot.tree.command(name="vs4", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_vs4(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📅 Day 4 – Arms Expert**\n"
        "**Save**: _Wisdom Medals, Power Cores, and ALL speedups_ \n\n"
        "📡>> **Radar Missions** – Quick and easy — finish as many as possible. \n"
        "🔩>> **Gears/Alloy/Blueprints** – Upgrade trucks. Don’t blow everything at once—start saving for reset too. \n"
        "💥>> **Boomer Rallies** – Start rallies and prioritize boomers at levels: 5, 8, 11, 14, 17, and 20. \n"
        "      - Level point tiers: 5–7, 8–10, 11–13, 14–16, 17–19, and 20. \n\n"
        "🧟>> **Kill Roamers** – Aim for higher-level ones for better return. Use stamina wisely.\n"
        "⚙️>> **Speedups** – Troops, Construction and Research.\n"
        "🔧>> **Precision Parts** - Used at level 30.",
        ephemeral=False
    )

@is_admin()
@bot.tree.command(name="vs5", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_vs5(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📅 Day 5 – Holistic Growth**\n"
        "🧰>> **All Prior Tasks** – A mix of Gear, Power Cores, Hero star upgrades, wisdom medals, etc. \n"
        "🔋>> **Power Cores** – Use to upgrade orange hero equipment. \n"
        "📜>> **Wisdom Medals & Speedups** – Clean up remaining medals and use short boosts. \n"
        "🧩>> **Hero Fragments** – Promote (Star Rise) heroes by spending fragments (especially orange/purple). \n"
        "🎯>> **Exclusive Equipment** – Star-rise your best gear (be cautious with resources). \n"
        "🔧>> **Red Equipment** – Orange gear must be level 100 and enhanced to level 10.\n\n"
        "💡 **Pro Tip** 💡: Use leftover items from earlier days to boost V.S. points.",
        ephemeral=False
    )

@is_admin()
@bot.tree.command(name="vs6", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_vs6(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📅 Day 6 – Enemy Buster**\n"
        "🚚>> **S-tier Escort/Cargo Trucks** – Do S-tier for points. \n"
        "🕶>> **S-tier (orange) Shadow Calls Missions** – Prioritize orange missions for massive point boosts. \n"
        "⚙️>> **Speedups** – Troops, Construction and Research. Start saving if you can get away with it. \n"
        "🎯>> **Defeat Enemies** – PvP in your state and any cross-server invaders. \n"
        "💀>> **Units Lost** – Sacrifices during battles or rallies contribute here (plan wisely).\n"
        "💡 **Pro Tip** 💡: If you do not plan on participating **SHIELD** and send out trucks for Truck-4-Truck to rack up passive points.\n",
        ephemeral=False
    )

# END V.S. Event Schedule==============================

@is_admin()
@bot.tree.command(name="warn", description="Warn a user with a reason")
@app_commands.describe(
        user="User to warn",
        reason="Reason for the warning"
)
async def warn(interaction: discord.Interaction, user: discord.User, reason: str):
    try:
        await user.send(f"⚠️ You have been issued a warning in **{interaction.guild.name}**.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message(f"⚠️ Couldn't DM {user.mention}, but warning noted.", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ Warned {user.mention} for: {reason}", ephemeral=True)

@is_admin()
@bot.tree.command(name="mute", description="Temporarily mute a user in this channel.")
@app_commands.describe(
    user="The user to mute",
    reason="Reason for the mute",
    duration="Duration of the mute in seconds (default: 60)"
)
async def mute(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str = "No reason provided",
    duration: int = 60
):
    guild = interaction.guild
    channel = interaction.channel

    muted_role = discord.utils.get(guild.roles, name=MUTE_ROLE_NAME)

    # 🔧 Auto-create 'Muted' role if it doesn't exist
    if muted_role is None:
        muted_role = await guild.create_role(name=MUTE_ROLE_NAME, reason="Auto-created for mute command")
        for ch in guild.channels:
            try:
                await ch.set_permissions(
                    muted_role,
                    send_messages=False,
                    speak=False,
                    add_reactions=False,
                    send_messages_in_threads=False,
                )
            except discord.Forbidden:
                logger.warning(f"⚠️ Cannot modify permissions for channel: {ch.name}")

    # 🔒 Ensure current channel is locked for Muted role
    try:
        await channel.set_permissions(
            muted_role,
            send_messages=False,
            speak=False,
            add_reactions=False,
            send_messages_in_threads=False,
        )
    except discord.Forbidden:
        logger.error(f"❌ Missing permission to update permissions in {channel.name}")

    # ⛓️ Apply mute
    await user.add_roles(muted_role, reason=reason)
    await interaction.response.send_message(
        f"🔇 {user.mention} has been muted in {channel.mention} for **{duration} seconds**.\n📝 Reason: {reason}",
        ephemeral=True
    )

    # Public confirmation
    try:
        await channel.send(f"🔇 {user.mention} has been muted for **{duration} seconds**.\n📝 Reason: {reason}")
    except discord.Forbidden:
        logger.error("❌ Can't send mute notification in channel.")

    # ⏳ Wait for duration then unmute
    await asyncio.sleep(duration)

    await user.remove_roles(muted_role, reason="Mute duration expired")
    try:
        await channel.send(f"🔊 {user.mention} has been unmuted after **{duration} seconds** after {reason}.")
    except discord.Forbidden:
        logger.error("❌ Can't send unmute notification in channel.")

    try:
        await interaction.followup.send(
            f"{user.mention} has been unmuted.", ephemeral=True
        )
    except discord.HTTPException:
        pass

@is_admin()
@bot.command()
async def hivemom(ctx, *, message: str):
    await ctx.message.delete()  # Delete the user’s command message

    if not message.strip():
        await ctx.send("You didn't tell me what to say!")
        return

    await ctx.send(message)  # Bot sends the message you passed


# Members Commands

@bot.tree.command(name="v0", description="View the 0-Day V.S. (Dual) Event task schedule with tips.")
async def slash_v0(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Reminder: :crossed_swords: V.S. (Dual) Event Starts at reset!**\n"
        "**Pro Tip**: Send trucks out to gather wood, iron, electricity and especially mint/coin NOW to get a boost after reset.\n\n",
        ephemeral=True
    )


@bot.tree.command(name="v1", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_v1(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**The :crossed_swords: V.S. (Dual) Event Schedule:** \n"
        "**📅 Day 1 – Shelter Expansion** \n"
        "👾**Save**: _Radars, Gears, Power Cores, Hero Equipment Lucky Chests, Prime Recruit (Gold Tickets), and ALL hero fragments_  \n\n"
        "🏗>> **Construction** – Upgrade and complete any structures in your settlement\n"
        "📜>> **Wisdom Medals** – Use to boost progression in Research Center Duel, Battle Strategy, etc.\n"
        "🔬>> **Research** – Start/Upgrade and finish tech trees. _Stack research with Wisdom Medals for a boost in points!_\n"
        "⚙️>> **Speedups** – Construction and Research ONLY for Day 1.\n"
        "💰>> **Resource Gathering** – ALL DAY send trucks out: wood, iron, electricity, and bonus points for mint/coin.",
        ephemeral=True
    )


@bot.tree.command(name="v2", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_v2(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📅 Day 2 – Hero Initiative**\n"
        "👾**Save**: _Gears, Power Cores, Wisdom Medals and Hero Equipment Lucky Chests_  \n\n"
        "📡 **Radar Missions** – Quick and easy — finish as many as possible.\n"
        "🎖>> **Prime Recruit** – Use all your Golden Tickets today!  \n"
        "🧩>> **Hero Fragments** – Promote (Star Rise) heroes by spending fragments (especially orange/purple).  \n"
        "🎯>> **Exclusive Equipment** – Star-rise your best gear (be cautious with resources) - Gained from micro-purchase.\n\n"
        "💡 **Pro Tip** 💡: Before reset into day 3, start troop training to complete **AFTER** reset to get a boost in points.",
        ephemeral=True
    )


@bot.tree.command(name="v3", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_v3(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📅 Day 3 – Keep Progressing**\n"
        "👾**Save**: _ Radars (for tomorrow), Energy (Rally tomorrow), Gears, Wisdom Medals, and both Construction and Research speed-ups_\n\n"
        "🚚>> **S-tier Escort/Cargo Trucks** – Do S-tier for points.\n"
        "🕶>> **S-tier (orange) Shadow Calls Missions** – Prioritize orange missions for massive point boosts.\n"
        "🔋>> **Power Cores** – Use to upgrade orange hero equipment.\n"
        "🎁>> **Hero Equipment Lucky Chests** – Use saved chests to boost power. _Enhance equipment or attach to heroes._\n"
        "⚙️>> **Speedups** – Troop Training **ONLY** for Day 3.\n"
        "🪖>> **Training** – Always be training troops. Train mid-tier troops in bulk. Use speedups if you're in a rush.\n"
        "🔧>> **Red Equipment** – Orange gear must be level 100 and enhanced to level 10 using Power Cores.",
        ephemeral=True
    )


@bot.tree.command(name="v4", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_v4(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📅 Day 4 – Arms Expert**\n"
        "**Save**: _Wisdom Medals, Power Cores, and ALL speedups_ \n\n"
        "📡>> **Radar Missions** – Quick and easy — finish as many as possible. \n"
        "🔩>> **Gears/Alloy/Blueprints** – Upgrade trucks. Don’t blow everything at once—start saving for reset too. \n"
        "💥>> **Boomer Rallies** – Start rallies and prioritize boomers at levels: 5, 8, 11, 14, 17, and 20. \n"
        "      - Level point tiers: 5–7, 8–10, 11–13, 14–16, 17–19, and 20. \n\n"
        "🧟>> **Kill Roamers** – Aim for higher-level ones for better return. Use stamina wisely.\n"
        "⚙️>> **Speedups** – Troops, Construction and Research.\n"
        "🔧>> **Precision Parts** - Used at level 30.",
        ephemeral=True
    )


@bot.tree.command(name="v5", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_v5(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📅 Day 5 – Holistic Growth**\n"
        "🧰>> **All Prior Tasks** – A mix of Gear, Power Cores, Hero star upgrades, wisdom medals, etc. \n"
        "🔋>> **Power Cores** – Use to upgrade orange hero equipment. \n"
        "📜>> **Wisdom Medals & Speedups** – Clean up remaining medals and use short boosts. \n"
        "🧩>> **Hero Fragments** – Promote (Star Rise) heroes by spending fragments (especially orange/purple). \n"
        "🎯>> **Exclusive Equipment** – Star-rise your best gear (be cautious with resources). \n"
        "🔧>> **Red Equipment** – Orange gear must be level 100 and enhanced to level 10.\n\n"
        "💡 **Pro Tip** 💡: Use leftover items from earlier days to boost V.S. points.",
        ephemeral=True
    )


@bot.tree.command(name="v6", description="View the x-Day V.S. (Dual) Event task schedule with tips.")
async def slash_v6(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📅 Day 6 – Enemy Buster**\n"
        "🚚>> **S-tier Escort/Cargo Trucks** – Do S-tier for points. \n"
        "🕶>> **S-tier (orange) Shadow Calls Missions** – Prioritize orange missions for massive point boosts. \n"
        "⚙️>> **Speedups** – Troops, Construction and Research. Start saving if you can get away with it. \n"
        "🎯>> **Defeat Enemies** – PvP non-alliance in state 161 and any cross-server invaders. \n"
        "💀>> **Units Lost** – Sacrifices during battles or rallies contribute here (plan wisely).\n"
        "💡 **Pro Tip** 💡: If you do not plan on participating **SHIELD** and send out trucks for Truck-4-Truck to rack up passive points.\n",
        ephemeral=True
    )

@bot.tree.command(name="alliancetech", description="Reminder about Alliance Tech donations")
async def slash_alliancetech(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🔧 **Alliance Tech**\n\n"
        "Want to help power up the alliance and rack up task points and settlement standing faster?\n"
        "📍>> In-Game, Head to: `Alliance > Tech` and toss in whatever resources you can spare.\n\n"
        "🧱>> **Why it matters:**\n"
        "➡️>> Boosts our **Alliance-wide buffs** - faster construction, stronger troops, and more efficient gathering.\n"
        "➡️>> Every little bit counts. Even small donations build momentum for massive upgrades.\n"
        "➡️>> Helps you get **Alliance Task Points** (yay rewards!)\n\n"
        "💡 **Pro Tip** 💡: Drop in a few donations multiple times throughout the day—tech queues reset, and stacking progress helps everyone.\n\n",
        ephemeral=True
    )

@bot.tree.command(name="faction", description="Faction Tips")
async def slash_faction(interaction: discord.Interaction):
    await interaction.response.send_message(
        "⚔️ Faction Trials Info:\n"
        "Found in-game >>> **Events >>> Faction Trials**\n"
        "👉>> Fighter = Shooter frags\n"
        "👉>> Rider = Shooter frags\n"
        "👉>> Shooter = Fighter frags",
        ephemeral=True
    )

@bot.tree.command(name="wti", description="Industrial Watchtower Info")
async def slash_wti(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**??️ Industrial Watchtower Levels:**\n"
        "```"
        "?? Red 1 Requirements:\n"
        "• Watchtower:\n"
        "  Precision Parts: 180 × 5\n"
        "  Resources: 76.8m × 5\n\n"
        "?? Red 2 Requirements:\n"
        "• Watchtower:\n"
        "  Precision Parts: 220 × 5\n"
        "  Resources: 88m × 5\n"
        "• Shooter Camp:\n"
        "  Precision Parts: 90 × 5\n"
        "  Resources: 45.3m × 5\n"
        "• Alliance Hall:\n"
        "  Precision Parts: 50 × 5\n"
        "  Resources: 29.9m × 5\n\n"
        "?? Red 3 Requirements:\n"
        "• Watchtower:\n"
        "  Precision Parts: 260 × 5\n"
        "  Resources: 105.6m × 5\n"
        "• Rider Camp:\n"
        "  Precision Parts: 90 × 5\n"
        "  Resources: 46.6m × 5\n"
        "• Alliance Hall:\n"
        "  Precision Parts: 50 × 5\n"
        "  Resources: 30.8m × 5\n\n"
        "?? Red 4 Requirements:\n"
        "• Watchtower:\n"
        "  Precision Parts: 310 × 5\n"
        "  Resources: 111.1m × 5\n"
        "• Riders Camp:\n"
        "  Precision Parts: 130 × 5\n"
        "  Resources: 54.7m × 5\n"
        "• Fighters Camp:\n"
        "  Precision Parts: 130 × 5\n"
        "  Resources: 54.7m × 5\n\n"
        "?? Red 5 Requirements:\n"
        "• Watchtower:\n"
        "  Precision Parts: 370 × 5\n"
        "  Resources: 116.2m × 5\n"
        "• Alliance Hall:\n"
        "  Precision Parts: 90 × 5\n"
        "  Resources: 39m × 5\n"
        "• Shooters Camp:\n"
        "  Precision Parts: 160 × 5\n"
        "  Resources: 66.5m × 5\n"
        "```",
        ephemeral=True
    )

@bot.tree.command(name="frank", description="Bio-Mutant")
async def slash_frank(interaction: discord.Interaction):
    await interaction.response.send_message(
 	"Frankenstein (Bio-Mutant) ROE's\n"
        "👉>> Start with 1 rally and join others\n"
        "👉>> If all rallies troop capacity fill fast (happens at 1 minute left), start 2 rallies next time and join others.\n\n"
        "💡 **Pro Tip** 💡: Higher Alliance Plaza = stronger attacks\n"
        "✅ _Note_: If you're under Lv20 level or Alliance Plaza: **Join only**",
        ephemeral=True
    )


@bot.tree.command(name="chiprate", description="Chip Drop Rate for Modding Workshop")
async def slash_chiprate(interaction: discord.Interaction):
    await interaction.response.send_message(
        "# Chip Rate Drop # \n\n"
        "🟩 **Green Boxes** \n"
        "Gold chip rate - 0.2%\n"
        "Purple chip rate - 4.8%\n"
        "Blue chip rate - 30.0%\n"
        "Green chip rate - 65.0%\n\n"
        "🟦 **Blue Boxes**\n"
        "Gold chip rate - 0.2%\n"
        "Purple chip rate - 30.0%\n"
        "Blue chip rate - 68.0%\n\n"
        "🟪 **Purple Boxes**\n"
        "Gold chip rate - 15.0%\n"
        "Purple chip rate - 85.0%\n\n"
        "🟨 **Gold Boxes**\n"
        "Gold chip rate - 100.0%\n",
        ephemeral=True
    )

@bot.tree.command(name="powercores", description="Tips and info on Power Cores")
async def slash_powercores(interaction: discord.Interaction):
    await interaction.response.send_message(
        "⚡ **Power Cores – What Are Those!?**\n\n"
        "👾 Power Cores are an essential resource to boost your **heroes**, **gear**, and **war tech**. They're rare, so use them wisely!\n\n"
        "👾 **Best Uses for Power Cores:**\n"
        ">>👉 **Upgrading Hero Gear** – Stronger gear = higher stats.\n"
        ">>👉 **Boosting Tech Upgrades** – Gain power faster, lose fewer troops.\n"
        ">>👉 **Enhancing Rally Damage** – Bigger boom = quicker wins.\n\n"
        "👾 **How to Get Power Cores:**\n"
        ">>👉 🔹 **Events & Daily Missions** – Reliable source if you stay active.\n"
        ">>👉 🔹 **Store Purchases** – Growth Pass gives the best bang for your buck (no pressure to buy).\n"
        ">>👉 🔹 **Rally Participation** – Join attacks often = more loot, more cores.\n\n"
        "💡 **Pro Tip** 💡: Save Power Cores for **high-level tech and elite hero upgrades**. Don’t burn them on early-game gear or filler upgrades.\n\n"
        "- Let’s get powered up! 💥",
        ephemeral=True
    )

@bot.tree.command(name="daily", description="List all daily must-do tasks.")
async def slash_daily(interaction: discord.Interaction):
    await interaction.response.send_message(
        "⚔️ _Make sure you've completed all **daily** tasks to grow your settlement._\n"
        "✅>> 5x Zombie/Boomer kills\n"
        "✅>> Radar missions\n"
        "✅>> Daily free (Gold Ticket) Hero Recruitment\n"
        "✅>> Arena Battles\n"
        "✅>> Check Events tab for new events\n"
        "✅>> Alliance Donations & Missions",
        ephemeral=True
    )

@bot.tree.command(name="maxdmg", description="Tips for maximizing damage in rallies and events.")
async def slash_maxdmg(interaction: discord.Interaction):
    await interaction.response.send_message(
        "👾💡 **Pro Tips for Maximum Damage at your current level:💡👾** \n\n"
        ">>👉 **Use your strongest troops and heroes**\n"
	"      >>> Stack your truck formations with like class heros (Fighters, Shooters, Riders)\n"
	"      >>> Put in best truck formation(s) in rallies first, use your alt formations to join or gather resources. Prioritize power! \n"
        ">>👉 **Activate buffs and combat boosts** such as 'War Frenzy' *before* joining or starting rallies, and *before events* — they stack up big. \n"
        ">>👉 **Stay active** and keep joining team rallies. Every contribution adds up! \n"
        "⚔️ >>>> Don't forget to **enable Auto Team-Up** when you're offline so you're always helping and gaining resources. <<<<",
        ephemeral=True
    )


@bot.tree.command(name="micro", description="Micro Purchases?")
async def slash_micro(interaction: discord.Interaction):
    await interaction.response.send_message(
        "👾 If you're thinking about spending, DON’T waste money randomly. Go for:\n"
        " >>👉 Growth Pass – Best overall value.\n"
        " >>👉 Growth Pass – Best overall value.\n"
        "💡🤖Overall, Save your $$ and maximize what you get if you do decide to purchase something.",
        ephemeral=True
    )

@bot.tree.command(name="teamup", description="How to Auto-Join")
async def slash_teamup(interaction: discord.Interaction):
    await interaction.response.send_message(
        "👾 Not sure how to Auto Team-up (_formally Auto-Join_) when you are offline?\n"
        ">>👉Do This:\n"
        " In game click the **Alliance** Icon on the right (above your mailbox) → **Click Wars** → Click the **'Auto Team-up'** button. \n"
        "💡 **Pro Tip** 💡:_Auto Team-up expires after 8 hours, be sure to come back to game every so often if you are busy to re-enable_",
        ephemeral=True
    )

        "**:military_helmet: Alliance Rank Structure & Promotions**\n"
        "_All ranks are earned through strength, loyalty, contribution, and spirit._\n"
        "**Meritocracy-based. Effort and teamwork matter most.**\n\n"

        "**:arrow_up: Promotion Guidelines**\n"
        "🔹 **R1 → R2** – Reach CP goals, stay active, follow direction, contribute to the alliance.\n"
        "🔹 **R2 → R3** – Progress further in CP/ranks, show battlefield skills, help lead comms in events.\n"
        "🔹 **R3 → R4** – Trusted leadership. Requires R4 vouch + R5 approval.\n\n"

        "**:crossed_swords: Rank Titles**\n"
        "**R1 – Neophytes**: Fresh blood learning the ropes and showing potential.\n\n"
        "**R2 – Acolytes**: Proven members committed to the cause.\n"
        "**R3 – Revenants**: Hardened veterans leading in events and coordination.\n"
        "**R4 –  Elite loyalists and strategic commanders.\n"
        "**R5 – Primarch**: Leader of the Academy. Guides the alliance.\n"

        "**:scroll: Role Descriptions**\n\n"
        "**R1 – Neophytes**\n"
        "> Newly inducted members of the Academy. Neophytes are in their beginning stages of learning, loyalty, and proving their strength.\n\n"
        "**R2 – Acolytes**\n"
        "> Loyal servants of the cause. Acolytes have shown growth and dedication and are entrusted with greater responsibilities and missions.\n\n"
        "**R3 – Revenants**\n"
        "> Veterans who have fallen and risen stronger. Revenants are our hardened core — they carry the will of the Alliance and lead by power and experience.\n\n"
        "**R4 – Elite warriors sworn fully to the Alliance. They serve as the right hand of the Primarch, guiding and mentoring the Revenants and Acolytes below them.\n\n"
        "**R5 – Primarch**\n"
        "> The supreme leader of the Academy. The Primarch bears the eternal duty to lead, protect, and expand the might of our alliance.\n\n"
        "_If you’re ever unsure about your rank or how to grow, reach out to an R4 or the Primarch._\n",
        ephemeral=True
    )


@bot.tree.command(name="vsduel", description="View the 6-Day V.S. (Dual) Event task schedule with tips.")
async def slash_vsduel(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**:crossed_swords: V.S. (Dual) Event — 6 Day Task Guide**\n"
        "_Complete daily objectives to contribute and grow!_\n\n"
	"**Pro Tip**: Send trucks out to gather wood, iron, electricity and Especially mint/coin the day before V.S. Starts.\n",
        ephemeral=True
    )
    await interaction.followup.send(
        "**The :crossed_swords: V.S. (Dual) Event Schedule:** \n"
        "**📅 Day 1 – Shelter Expansion** \n"
        "👾**Save**: _Radars, Gears, Power Cores, Hero Equipment Lucky Chests, Prime Recruit (Gold Tickets), and ALL hero fragments_  \n\n"
        "🏗>> **Construction** – Upgrade and complete any structures in your settlement\n"
        "📜>> **Wisdom Medals** – Use to boost progression in Research Center Duel, Battle Strategy, etc.\n"
        "🔬>> **Research** – Start/Upgrade and finish tech trees. _Stack research with Wisdom Medals for a boost in points!_\n"
        "⚙️>> **Speedups** – Construction and Research ONLY for Day 1.\n"
        "💰>> **Resource Gathering** – ALL DAY send trucks out: wood, iron, electricity, and bonus points for mint/coin.",
        ephemeral=True
    )
    await interaction.followup.send(
        "**📅 Day 2 – Hero Initiative**\n"
        "👾**Save**: _Gears, Power Cores, Wisdom Medals and Hero Equipment Lucky Chests_  \n\n"
        "📡 **Radar Missions** – Quick and easy — finish as many as possible.\n"
        "🎖>> **Prime Recruit** – Use all your Golden Tickets today!  \n"
        "🧩>> **Hero Fragments** – Promote (Star Rise) heroes by spending fragments (especially orange/purple).  \n"
        "🎯>> **Exclusive Equipment** – Star-rise your best gear (be cautious with resources) - Gained from micro-purchase.\n\n"
        "💡 **Pro Tip** 💡: Before reset into day 3, start troop training to complete **AFTER** reset to get a boost in points.",
        ephemeral=True
    )
    await interaction.followup.send(
        "**📅 Day 3 – Keep Progressing**\n"
        "👾**Save**: _ Energy (Rally tomorrow), Gears, Wisdom Medals, and both Construction and Research speed-ups_\n\n"
        "🚚>> **S-tier Escort/Cargo Trucks** – Do S-tier for points.\n"
        "🕶>> **S-tier (orange) Shadow Calls Missions** – Prioritize orange missions for massive point boosts.\n"
        "🔋>> **Power Cores** – Use to upgrade orange hero equipment.\n"
        "🎁>> **Hero Equipment Lucky Chests** – Use saved chests to boost power. _Enhance equipment or attach to heroes._\n"
        "⚙️>> **Speedups** – Troop Training **ONLY** for Day 3.\n"
        "🪖>> **Training** – Always be training troops. Train mid-tier troops in bulk. Use speedups if you're in a rush.\n"
        "🔧>> **Red Equipment** – Orange gear must be level 100 and enhanced to level 10 using Power Cores.",
        ephemeral=True
    )
    await interaction.followup.send(
        "**📅 Day 4 – Arms Expert**\n"
        "**Save**: _Wisdom Medals, Power Cores, and ALL speedups_ \n\n"
        "📡>> **Radar Missions** – Quick and easy — finish as many as possible. \n"
        "🔩>> **Gears/Alloy/Blueprints** – Upgrade trucks. Don’t blow everything at once—start saving for reset too. \n"
        "💥>> **Boomer Rallies** – Start rallies and prioritize boomers at levels: 5, 8, 11, 14, 17, and 20. \n"
        "      - Level point tiers: 5–7, 8–10, 11–13, 14–16, 17–19, and 20. \n\n"
        "🧟>> **Kill Roamers** – Aim for higher-level ones for better return. Use stamina wisely.\n"
        "⚙️>> **Speedups** – Troops, Construction and Research.\n"
        "🔧>> **Precision Parts** - Used at level 30.",
        ephemeral=True
    )
    await interaction.followup.send(
        "**📅 Day 5 – Holistic Growth**\n"
        "🧰>> **All Prior Tasks** – A mix of Gear, Power Cores, Hero star upgrades, wisdom medals, etc. \n"
        "🔋>> **Power Cores** – Use to upgrade orange hero equipment. \n"
        "📜>> **Wisdom Medals & Speedups** – Clean up remaining medals and use short boosts. \n"
        "🧩>> **Hero Fragments** – Promote (Star Rise) heroes by spending fragments (especially orange/purple). \n"
        "🎯>> **Exclusive Equipment** – Star-rise your best gear (be cautious with resources). \n"
        "🔧>> **Red Equipment** – Orange gear must be level 100 and enhanced to level 10.\n\n"
        "💡 **Pro Tip** 💡: Use leftover items from earlier days to boost V.S. points.",
        ephemeral=True
    )
    await interaction.followup.send(
        "**📅 Day 6 – Enemy Buster**\n"
        "🚚>> **S-tier Escort/Cargo Trucks** – Do S-tier for points. \n"
        "🕶>> **S-tier (orange) Shadow Calls Missions** – Prioritize orange missions for massive point boosts. \n"
        "⚙️>> **Speedups** – Troops, Construction and Research. Start saving if you can get away with it. \n"
        "🎯>> **Defeat Enemies** – PvP non-alliance in state 161 and any cross-server invaders. \n"
        "💀>> **Units Lost** – Sacrifices during battles or rallies contribute here (plan wisely).\n"
        "💡 **Pro Tip** 💡: If you do not plan on participating **SHIELD** and send out trucks for Truck-4-Truck to rack up passive points.\n",
        ephemeral=True
    )

@bot.tree.command(name="helpme", description="List all HiveMom commands.")
async def slash_helpme(interaction: discord.Interaction):
    member = interaction.user
    if not isinstance(member, discord.Member):
        member = interaction.guild.get_member(interaction.user.id)

    # Fall back if member could not be resolved
    if member is None:
        await interaction.response.send_message(
            "❌ Unable to verify your roles. Please try again later.",
            ephemeral=True
        )
        return

    role_names = [role.name for role in member.roles]
    print(f"🔍 Roles for {member.name}: {role_names}")

    # Base user commands
    message = (
	"_in chatbox enter any commands below_\n"
        "_🧠__**HiveMom Commands:**__\n"
        "/alliancetech - Alliance Tech Upgrading and how-to\n"
        "/chiprate - Chip Drop Rate\n"
        "/daily – Checklist for daily ops\n"
        "/faction – Faction trial info\n"
        "/frank – Bio-Mutant rally tips\n"
        "/maxdmg - How to boost damage now\n"
        "/micro - in-Game micro purchases?\n"
        "/powercores - Powercores, What are those!?\n"
        "/ranking - View Alliance rank structure.\n"
        "/teamup - How to Auto Join Rallies?\n"
        "/wti - Industrial Watchtower\n"
        "/v0 , /v1 , /v2 , /v3 , /v4 , /v5 , /v6 - V.S. Duel Daily Guides\n"
	"/vsduel - All Daily breakout V.S. Duel guides.\n"
    )

    # Show admin-only commands if user is in an allowed role
    allowed_roles = os.getenv("ADMIN_ROLES", "R5 & R4,R5,R4,Admin,admin,R5/R4").split(",")
    allowed_roles = [role.strip() for role in allowed_roles]

    if any(role in role_names for role in allowed_roles):
        message += (
            "\n🛡️__**Admin Commands:**__\n"
            "/dm - To quickly get into others' DMs\n"
            "/hey – admin - Bot responsiveness\n"
            "/mute – Mute a user in chat\n"
            "/warn – Warn a user with a reason\n"
	    "/vs0 , /vs1 , /vs2 , /vs3 , /vs4 , /vs5 , /vs6 - V.S. Duel Daily Guides\n"
	    "/vsschedule - The entire V.S. Schedule sent to ALL\n"
        )

    await interaction.response.send_message(message, ephemeral=True)

# ---- Run the bot with token ----
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if TOKEN is None:
    raise ValueError("❌ DISCORD_BOT_TOKEN is not set in environment variables.")
bot.run(TOKEN)

