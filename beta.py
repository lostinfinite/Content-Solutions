import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import json
import os
import re
from dotenv import load_dotenv
import sqlite3
from discord import option
from collections import defaultdict
from datetime import datetime, timedelta
from discord import SlashCommandOptionType
from config import (
    STAFF_ROLE_ID, 
    QUARANTINE_ROLE_ID, 
    UNDER_INVESTIGATION_ROLE_ID, 
    STAFF_CHAT_CHANNEL_ID, 
    OWNERSHIP_ROLE_ID
)
from config import STAFF_ROLE_ID, QUARANTINE_ROLE_ID, UNDER_INVESTIGATION_ROLE_ID
from utils import validate_role_dict
from utils import assign_role
from config import QUARANTINE_ROLE_ID
from config import SI_BAN_LIST
from utils import ban_user
from config import SI_BAN_LIST
from utils import ban_user, has_staff_role
from utils import start_heartbeat_task
from config import QUARANTINE_ROLE_ID






# Load environment variables
load_dotenv()

# Intents setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

# Constants
DB_FILE = "user_activity.db"
LOG_FILE = "moderation_log.json"




OWNER_NAME = "ContentLTD"
OWNER_SITE = "https://contentltd.net"
WHITELISTED_CHANNELS = [HIDDEN]  # Replace with your channel IDs



ALLOWED_DOMAINS = [
    "tenor.com",
    "google.com",
    "discord.com",
    "discord.gg",
    "contentltd.net",
    "discohook.app",
    "circlebot.xyz",
    "dyno.gg",
    "sapph.xyz",
    "securitybot.gg",
    "trident.bot",
    "wickbot.com"
]

ALLOWED_PATTERNS = [
    r"(https?://.*\.gif)",  # Allow GIF links from any domain
]

# List of scam phrases
SCAM_PHRASES = [
    "congratulations, you've won", "you are our lucky winner", "claim your prize now",
    "you've inherited a fortune", "your account has been locked", "verify your identity",
    "urgent: your account will be suspended", "free discord nitro", "claim your free nitro",
    "reset your password now", "click here to track your order", "call our toll-free number",
    "send 1 bitcoin, and i’ll send back 2", "pay us in gift cards", "your subscription is expiring",
    "limited-time offer expires soon", "your account has been flagged", "i accidentally reported you",
    "click here to resolve the issue", "your payment failed", "redeem your free nitro",
    "call our support team now", "we detected unusual activity in your account"
]

# Load blacklisted items from files
blacklisted_domains = set()
blacklisted_ips = set()

# Process files
file_paths = [
    "links/abuse.txt",
    "links/adobe.txt",
    "links/ads.txt",
    "links/fraud.txt",
    "links/malware.ip",
    "links/malware.txt",
    "links/porn.txt",
    "links/scam.txt",
    "links/tracking.ip",
    "links/tracking.txt"
]

for file_path in file_paths:
    with open(file_path, "r") as file:
        for i, line in enumerate(file):
            # Ignore lines 1-15
            if i < 15:
                continue
            line = line.strip()
            if line.startswith("0.0.0.0"):
                # Extract domain
                domain = line.split("0.0.0.0")[-1].strip()
                blacklisted_domains.add(domain)
            elif ".ip" in file_path:
                # Add IP directly for .ip files
                blacklisted_ips.add(line)
            else:
                # Add domain for other files
                blacklisted_domains.add(line)

# Function to check for emojis
def is_emoji(s):
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]"
    )
    return bool(emoji_pattern.search(s))

# Mass-ping detection parameters
MASS_PING_THRESHOLD = 5
PING_WINDOW_SECONDS = 60
ping_tracker = defaultdict(list)  # Tracks @everyone pings by user


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    await start_heartbeat_task()  # Start the heartbeat task


@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return

    # Ignore messages from staff members
    if any(role.id == STAFF_ROLE_ID for role in message.author.roles):
        return

    # Remove emojis from the message content
    content = re.sub(r"[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]", "", message.content.lower())

    # Check for blacklisted links and IPs
    for domain in blacklisted_domains:
        if domain in content and "tenor.com" not in content:  # Allow Tenor links
            await message.delete()
            staff_channel = bot.get_channel(STAFF_CHAT_CHANNEL_ID)
            if staff_channel:
                await staff_channel.send(
                    f"⚠️ Blacklisted link detected in {message.channel.mention} by {message.author.mention}: `{domain}`"
                )
            return

    for ip in blacklisted_ips:
        if ip in content:
            await message.delete()
            staff_channel = bot.get_channel(STAFF_CHAT_CHANNEL_ID)
            if staff_channel:
                await staff_channel.send(
                    f"⚠️ Blacklisted IP detected in {message.channel.mention} by {message.author.mention}: `{ip}`"
                )
            return

@bot.event
async def on_message(message):
    # Skip bot messages
    if message.author.bot:
        return

    # Mass-ping detection
    if "@everyone" in message.content:
        now = datetime.utcnow()
        ping_tracker[message.author.id].append(now)
        ping_tracker[message.author.id] = [
            ping_time for ping_time in ping_tracker[message.author.id]
            if now - ping_time <= timedelta(seconds=PING_WINDOW_SECONDS)
        ]

        if len(ping_tracker[message.author.id]) >= MASS_PING_THRESHOLD:
            await message.channel.send(
                f"⚠️ {message.author.mention}, you are mass-pinging @everyone! This is not allowed."
            )
            await message.delete()
            return

    # Scam phrase detection
    message_content_lower = message.content.lower()
    for phrase in SCAM_PHRASES:
        if phrase in message_content_lower:
            await message.channel.send(
                f"🚨 {message.author.mention}, your message contains potentially malicious content and has been flagged."
            )
            await message.delete()
            return

    # Link detection
    if re.search(r"(https?://[^\s]+)", message.content):
        for phrase in SCAM_PHRASES:
            if phrase in message_content_lower:
                await message.channel.send(
                    f"🔗 {message.author.mention}, suspicious link detected! Your message has been removed."
                )
                await message.delete()
                return

    # Gift card/code detection
    if re.search(r"\b(?:gift card|code)\b", message_content_lower):
        await message.channel.send(
            f"🎁 {message.author.mention}, mentioning gift cards or codes can be suspicious. Please avoid sharing sensitive information."
        )
        await message.delete()
        return

# Database setup
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS moderation_logs (
    action TEXT,
    user_id INTEGER,
    moderator_id INTEGER,
    timestamp TEXT,
    details TEXT
)
""")
conn.commit()
def owner_only(interaction: discord.Interaction):
    role = discord.utils.get(interaction.user.roles, id=OWNERSHIP_ROLE_ID)
    return role is not None
# Helper functions
def log_action(action, user_id, moderator_id, details):
    now = datetime.utcnow().isoformat()
    cursor.execute("""
    INSERT INTO moderation_logs (action, user_id, moderator_id, timestamp, details)
    VALUES (?, ?, ?, ?, ?)
    """, (action, user_id, moderator_id, now, details))
    conn.commit()

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as file:
            logs = json.load(file)
    else:
        logs = []
    logs.append({"action": action, "user_id": user_id, "moderator_id": moderator_id, "timestamp": now, "details": details})
    with open(LOG_FILE, "w") as file:
        json.dump(logs, file, indent=4)

async def is_staff(member):
    staff_role = discord.utils.get(member.guild.roles, id=STAFF_ROLE_ID)
    return staff_role in member.roles

async def assign_role(member, role_id):
    role = member.guild.get_role(role_id)
    if role:
        await member.add_roles(role)

async def send_to_staff_chat(guild, message):
    staff_chat = guild.get_channel(STAFF_CHAT_CHANNEL_ID)
    if staff_chat:
        await staff_chat.send(message)

# Commands



@bot.slash_command(name="siban", description="Ban everyone on the Security Intelligence ban list.")
async def siban(ctx):
    if not has_staff_role(ctx):
        await ctx.respond("❌ You don't have the required role to use this command!", ephemeral=True)
        return

    guild = ctx.guild
    if guild is None:
        await ctx.respond("This command cannot be used outside a guild.", ephemeral=True)
        return

    if not SI_BAN_LIST:
        await ctx.respond("The SI ban list is empty.", ephemeral=True)
        return

    await ctx.respond("🚀 Starting SI ban operation. This may take a moment...", ephemeral=True)

    banned_count = 0
    failed_count = 0

    for user_id in SI_BAN_LIST:
        try:
            # Use discord.Object to represent the user for banning
            user_object = discord.Object(id=user_id)
            await guild.ban(user_object, reason="SI Ban")
            print(f"DEBUG: Successfully banned user_id={user_id}")
            banned_count += 1
        except discord.Forbidden:
            print(f"DEBUG: Insufficient permissions to ban user_id={user_id}.")
            failed_count += 1
        except discord.HTTPException as e:
            print(f"DEBUG: HTTP error while banning user_id={user_id}: {e}")
            failed_count += 1
        except Exception as e:
            print(f"DEBUG: Unexpected error banning user_id={user_id}: {e}")
            failed_count += 1

    print(f"DEBUG: SI ban operation completed. Banned {banned_count} users, failed to ban {failed_count} users.")

    await ctx.send_followup(
        f"✅ SI ban operation complete. Banned {banned_count} users. Failed to ban {failed_count} users.",
        ephemeral=True
    )



@bot.slash_command(name="massban", description="Ban multiple users by IDs.")
async def massban(ctx, user_ids: str, reason: str = "No reason provided"):
    if not has_staff_role(ctx):
        await ctx.respond("You do not have permission.", ephemeral=True)
        return

    ids = user_ids.split()
    for user_id in ids:
        try:
            user = await ctx.guild.fetch_member(int(user_id))
            await user.ban(reason=reason)
            log_action("Mass Ban", user.id, ctx.author.id, reason)
        except Exception as e:
            await ctx.respond(f"Failed to ban user ID {user_id}: {e}", ephemeral=True)
    await ctx.respond("🚨 Users have been banned.", ephemeral=True)


@bot.slash_command(name="test_quarantine")
async def test_quarantine(ctx):
    # For testing, no staff check here, but you can add if needed:
    # if not has_staff_role(ctx):
    #     await ctx.respond("❌ You don't have the required role to use this command!", ephemeral=True)
    #     return

    member = ctx.author
    guild_id = ctx.guild.id
    role_id = QUARANTINE_ROLE_ID.get(guild_id)
    if role_id is None:
        await ctx.respond("No quarantine role configured for this guild.", ephemeral=True)
        return
    await assign_role(member, role_id)
    await ctx.respond("Test quarantine role applied (if role exists).", ephemeral=True)


@bot.slash_command(name="remove_ban", description="Unban a user by their user ID.")
@discord.option("user_id", int, description="The ID of the user to unban")
async def remove_ban(ctx, user_id: int):
    if not has_staff_role(ctx):
        await ctx.respond("You do not have permission.", ephemeral=True)
        return

    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    log_action("Unban", user_id, ctx.author.id, "Ban removed")
    await ctx.respond(f"✅ Unbanned `{user}`.", ephemeral=True)


@bot.slash_command(name="under_investigation", description="Mark a user as under investigation.")
@discord.option("member", discord.Member, description="The member to mark as under investigation")
async def under_investigation(ctx, member: discord.Member):
    if not has_staff_role(ctx):
        await ctx.respond("❌ You don't have the required role to use this command!", ephemeral=True)
        return

    guild_id = member.guild.id
    role_id = UNDER_INVESTIGATION_ROLE_ID.get(guild_id)
    if role_id is None:
        await ctx.respond("No 'Under Investigation' role configured for this guild.", ephemeral=True)
        return
    await assign_role(member, role_id)
    log_action("Under Investigation", member.id, ctx.author.id, "Marked under investigation")
    await ctx.respond(f"🔍 `{member.name}` is now under investigation.", ephemeral=True)


@bot.slash_command(name="quarantine", description="Quarantine a user.")
@discord.option("member", discord.Member, description="The member to quarantine")
async def quarantine(ctx, member: discord.Member):
    if not has_staff_role(ctx):
        await ctx.respond("❌ You don't have the required role to use this command!", ephemeral=True)
        return

    guild_id = member.guild.id
    role_id = QUARANTINE_ROLE_ID.get(guild_id)
    if role_id is None:
        await ctx.respond("No quarantine role configured for this guild.", ephemeral=True)
        return
    await assign_role(member, role_id)
    await ctx.respond(f"⚠️ `{member.display_name}` has been quarantined.", ephemeral=True)


@bot.slash_command(name="timeout", description="Timeout a user for a specific duration (in minutes).")
@discord.option("member", discord.Member, description="The member to timeout")
@discord.option("duration", int, description="Duration of the timeout in minutes")
@discord.option("reason", str, description="Reason for the timeout", required=False, default="No reason provided")
async def timeout(ctx, member: discord.Member, duration: int, reason: str):
    if not has_staff_role(ctx):
        await ctx.respond("You do not have permission.", ephemeral=True)
        return

    timeout_duration = timedelta(minutes=duration)
    until = datetime.utcnow() + timeout_duration

    try:
        await member.edit(communication_disabled_until=until, reason=reason)
        log_action("Timeout", member.id, ctx.author.id, f"Timeout for {duration} minutes: {reason}")
        await ctx.respond(f"🚨 User `{member.name}` has been timed out for {duration} minutes.", ephemeral=True)
    except discord.Forbidden:
        await ctx.respond("❌ Permission denied to timeout this user.", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    scam_patterns = [r"free nitro", r"click this link", r"giveaway"]
    slur_patterns = [r"slur1", r"slur2"]  # Add real slurs here

    if any(re.search(pattern, message.content, re.IGNORECASE) for pattern in scam_patterns + slur_patterns):
        await message.delete()
        await send_to_staff_chat(message.guild, f"🚨 Detected prohibited content from `{message.author}`: {message.content}")
        log_action("Filtered Message", message.author.id, None, "Prohibited content")
    await bot.process_commands(message)
    
def has_staff_role(ctx):
    role_id = STAFF_ROLE_ID.get(ctx.guild.id)
    if role_id is None:
        return False
    return any(role.id == role_id for role in ctx.author.roles)


# Ban command
@bot.slash_command(name="ping", description="Check the bot's latency.")
async def ping(ctx: discord.ApplicationContext):
    """Check the bot's current latency."""
    # If you want only staff to be able to use this command, enable the check below:
    # if not has_staff_role(ctx):
    #     await ctx.respond("❌ You don't have the required role to use this command!", ephemeral=True)
    #     return

    latency = round(bot.latency * 1000, 2)
    await ctx.respond(f"Pong! Latency: {latency}ms", ephemeral=True)


@bot.slash_command(name="ban", description="Ban a member from the server.")
@discord.option("member", discord.Member, description="The member to ban")
@discord.option("reason", str, description="Reason for the ban", required=False, default="No reason provided")
async def ban(ctx: discord.ApplicationContext, member: discord.Member, reason: str):
    """Ban a member from the server."""
    if not has_staff_role(ctx):
        await ctx.respond("❌ You don't have the required role to use this command!", ephemeral=True)
        return

    try:
        await member.ban(reason=reason)
        await ctx.respond(f"🔨 {member} has been banned for: {reason}", ephemeral=True)
    except discord.Forbidden:
        await ctx.respond("❌ I don't have permission to ban this user.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"❌ An error occurred: {e}", ephemeral=True)


@bot.slash_command(name="kick", description="Kick a member from the server.")
@discord.option("member", discord.Member, description="The member to kick")
@discord.option("reason", str, description="Reason for the kick", required=False, default="No reason provided")
async def kick(ctx: discord.ApplicationContext, member: discord.Member, reason: str):
    """Kick a member from the server."""
    if not has_staff_role(ctx):
        await ctx.respond("❌ You don't have the required role to use this command!", ephemeral=True)
        return

    try:
        await member.kick(reason=reason)
        await ctx.respond(f"👢 {member} has been kicked for: {reason}", ephemeral=True)
    except discord.Forbidden:
        await ctx.respond("❌ I don't have permission to kick this user.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"❌ An error occurred: {e}", ephemeral=True)

@bot.slash_command(name="info", description="Provides bot and creator information.")
async def info(ctx: discord.ApplicationContext):
    """Show bot and creator details."""
    embed = discord.Embed(
        title="Bot Information",
        description="Details about this bot and its creator.",
        color=discord.Color.blue()
    )
    embed.add_field(name="Bot Name", value="Content Solutions", inline=False)
    embed.add_field(name="Owner", value=OWNER_NAME, inline=False)
    embed.add_field(name="Website", value=OWNER_SITE, inline=False)
    embed.set_footer(text="Made with ❤️ by ContentLTD")
    await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name="bugs", description="Show known bugs.")
async def bugs(ctx: discord.ApplicationContext):
    """Show known bugs details."""
    embed = discord.Embed(
        title="Known Bugs",
        description="As we know currently, some Gifs may not work and may be deleted. The reason of deletion sent to staff may be wrong or invalid. We are working as fast as we can.",
        color=discord.Color.blue()
    )
    embed.add_field(name="Version 1.0.0", value="As we know currently, some Gifs may not work and may be deleted. The reason of deletion sent to staff may be wrong or invalid. We are working as fast as we can.", inline=False)
    embed.add_field(name="Version 1.1.0", value="Some commands may not be executed because you dont have the role needed when you do. This hasnt been observed since release but it may happen. Contact support if such bug is observed", inline=False)
    embed.set_footer(text="Made with ❤️ by ContentLTD")
    await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name="secinfo", description="Information on the latest Security Intelligence Update.")
async def secinfo(ctx: discord.ApplicationContext):
    """Show SI (Security Intelligence) update details."""
    embed = discord.Embed(
        title="SI Information",
        description="Details about the latest SI update.",
        color=discord.Color.blue()
    )
    embed.add_field(name="Last Updated", value="12/11/2024", inline=False)
    embed.add_field(name="Version", value="1.1.0", inline=False)
    embed.add_field(name="Patch Notes", value="Added a Security Intelligence ban list and command, use /siban to automatically ban everyone on said list.", inline=False)
    embed.set_footer(text="Made with ❤️ by ContentLTD")
    await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name="mute", description="Timeout a member for a specified duration.")
@discord.option("member", discord.Member, description="The member to timeout")
@discord.option("duration", int, description="Timeout duration in seconds")
@discord.option("reason", str, description="Reason for the timeout", required=False, default="No reason provided")
async def mute(ctx: discord.ApplicationContext, member: discord.Member, duration: int, reason: str):
    """Timeout a member for a specified duration (in seconds)."""
    if not has_staff_role(ctx):
        await ctx.respond("❌ You don't have the required role to use this command!", ephemeral=True)
        return

    try:
        timeout_duration = discord.utils.utcnow() + discord.timedelta(seconds=duration)
        await member.edit(timeout=timeout_duration)
        await ctx.respond(f"⏱️ {member} has been timed out for {duration} seconds for: {reason}", ephemeral=True)
    except discord.Forbidden:
        await ctx.respond("❌ I don't have permission to timeout this user.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"❌ An error occurred: {e}", ephemeral=True)

# Link remover event
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id in WHITELISTED_CHANNELS:
        await bot.process_application_commands(message)
        return

    # Regex pattern to detect links
    link_pattern = r"(https?://[^\s]+)"
    found_links = re.findall(link_pattern, message.content)

    for link in found_links:
        domain_allowed = any(domain in link for domain in ALLOWED_DOMAINS)
        matches_allowed_pattern = any(re.search(pattern, link) for pattern in ALLOWED_PATTERNS)

        if domain_allowed or matches_allowed_pattern:
            await bot.process_application_commands(message)
            return

    if found_links:
        try:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, links are not allowed here.")
        except discord.Forbidden:
            await message.channel.send("❌ I don't have permission to delete messages.")

    await bot.process_application_commands(message) 



bot.run('REDACTED -- REPLACE WITH REAL TOKEN')