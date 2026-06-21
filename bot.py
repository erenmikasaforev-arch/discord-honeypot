import os
import discord
from discord.ext import commands
from datetime import timedelta

TOKEN = os.getenv("DISCORD_TOKEN)

HONEYPOT_CHANNEL_ID = 1518086228744867900
MOD_LOG_CHANNEL_ID = 1488836888382144552

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    channel = bot.get_channel(HONEYPOT_CHANNEL_ID)

    embed = discord.Embed(
        title="⚠️ DO NOT SEND ANY MESSAGES HERE",
        description=(
            "**This channel is a security trap to catch compromised/hacked accounts.**\n\n"
            "Compromised accounts often spam fake giveaways, scam links, "
            "and malicious advertisements across the server.\n\n"
            "**Any message sent here will result in an automatic 7-day timeout "
            "and removal of recent messages.**\n\n"
            "If this action was triggered unintentionally, secure your account, "
            "change your password, and enable 2FA."
        ),
        color=discord.Color.red()
    )

    msg = await channel.send(
        content="@everyone",
        embed=embed
    )

    await msg.pin()

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id != HONEYPOT_CHANNEL_ID:
        await bot.process_commands(message)
        return

    guild = message.guild
    member = message.author

    deleted_count = 0

    try:
        await message.delete()
    except Exception as e:
        print(f"Failed to delete trigger message: {e}")

    try:
        timeout_until = discord.utils.utcnow() + timedelta(days=7)

        await member.timeout(
            timeout_until,
            reason="Triggered honeypot channel"
        )

        print(f"Timed out {member}")

    except Exception as e:
        print(f"Timeout failed: {e}")

    cutoff = discord.utils.utcnow() - timedelta(days=7)

    for channel in guild.text_channels:

        perms = channel.permissions_for(guild.me)

        if not (
            perms.read_message_history
            and perms.manage_messages
        ):
            continue

        try:
            async for msg in channel.history(
                limit=None,
                after=cutoff
            ):
                if msg.author.id == member.id:
                    try:
                        await msg.delete()
                        deleted_count += 1
                    except:
                        pass

        except Exception as e:
            print(
                f"Failed scanning {channel.name}: {e}"
            )

    log_channel = guild.get_channel(
        MOD_LOG_CHANNEL_ID
    )

    if log_channel:
        await log_channel.send(
            f"🚨 Honeypot Triggered\n"
            f"User: {member.mention}\n"
            f"Timeout: 7 Days\n"
            f"Messages Deleted: {deleted_count}"
        )

    await bot.process_commands(message)


bot.run(TOKEN)
