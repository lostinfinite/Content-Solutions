import discord
from config import *
from config import SI_BAN_LIST
import json
import os
from datetime import datetime
import asyncio
import requests

# URL for the BetterStack Uptime heartbeat
HEARTBEAT_URL = "hidden"

async def send_heartbeat():
    """
    Sends a POST request to the BetterStack Uptime heartbeat URL every 2 hours.
    """
    while True:
        try:
            # Send the POST request
            response = requests.post(HEARTBEAT_URL)
            
            # Log the response status
            if response.status_code == 200:
                print("✅ Heartbeat sent successfully.")
            else:
                print(f"⚠️ Failed to send heartbeat. Status code: {response.status_code}. Response: {response.text}")
        except Exception as e:
            print(f"❌ An error occurred while sending the heartbeat: {e}")
        
        # Wait for 2 hours before the next request
        await asyncio.sleep(2 * 60 * 60)

# Ensure the heartbeat function starts when the bot starts
async def start_heartbeat_task():
    """
    Starts the heartbeat task when the bot runs.
    """
    asyncio.create_task(send_heartbeat())

def has_staff_role(ctx):
    print("DEBUG: guild_id =", ctx.guild.id)
    print("DEBUG: staff_role_id =", STAFF_ROLE_ID.get(ctx.guild.id))
    print("DEBUG: user_roles =", [role.id for role in ctx.author.roles])
    
    role_id = STAFF_ROLE_ID.get(ctx.guild.id)
    if role_id is None:
        return False
    return any(role.id == role_id for role in ctx.author.roles)

def log_action(action, user_id, moderator_id, details):
    now = datetime.utcnow().isoformat()
    LOG_FILE = "moderation_log.json"

    # Load existing logs if file exists, otherwise start with an empty list
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as file:
            logs = json.load(file)
    else:
        logs = []

    # Add the new log entry
    entry = {
        "action": action,
        "user_id": user_id,
        "moderator_id": moderator_id,
        "timestamp": now,
        "details": details
    }
    logs.append(entry)

    # Write updated logs back to the file
    with open(LOG_FILE, "w") as file:
        json.dump(logs, file, indent=4)

async def assign_role(member: discord.Member, role_id: int):
    print("DEBUG: member =", member, type(member))
    print("DEBUG: member.guild =", member.guild, type(member.guild))
    print("DEBUG: role_id =", role_id, type(role_id))

    if not isinstance(role_id, int):
        print("ERROR: role_id is not an integer:", role_id, type(role_id))
        return

    role = member.guild.get_role(role_id)
    print("DEBUG: role =", role, type(role))

    if role:
        await member.add_roles(role)
    else:
        print(f"DEBUG: No role found for role_id {role_id} in guild {member.guild.id}")

async def ban_user(guild: discord.Guild, user_id: int, moderator_id: int, reason: str = "SI Ban"):
    try:
        user = await guild.fetch_member(user_id)
        await guild.ban(user, reason=reason)
        log_action("SI Ban", user_id, moderator_id, reason)  # Ensure log_action is defined
        return True
    except discord.NotFound:
        # User not found in this guild
        return False
    except discord.Forbidden:
        # Bot lacks permission
        return False
    except Exception as e:
        print(f"Error banning user {user_id}: {e}")
        return False

def has_staff_role(ctx):
    # Get staff roles for the current guild
    staff_roles_for_guild = STAFF_ROLE_ID.get(ctx.guild.id, [])
    return any(role.id in staff_roles_for_guild for role in ctx.author.roles)


# utils.py
def validate_role_dict(d):
    if not isinstance(d, dict):
        raise ValueError("Role dict is not a dict")
    for k, v in d.items():
        if not isinstance(k, int):
            raise ValueError(f"Guild ID {k} not an int")
        if not isinstance(v, int):
            raise ValueError(f"Value for guild {k} must be an int, got {type(v)}")


validate_role_dict(QUARANTINE_ROLE_ID)