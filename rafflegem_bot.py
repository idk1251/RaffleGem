import discord
from discord.ext import commands
import json
import os

# Load configuration from config.json
with open('config.json', 'r') as f:
    config = json.load(f)

# Retrieve bot token from environment variable
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Check if token is set
if not DISCORD_TOKEN:
    print('Error: Discord token not found. Please set DISCORD_TOKEN environment variable.')
    exit(1)

# Initialize bot with specified prefix
bot = commands.Bot(command_prefix=config.get('prefix', '/'))

# Constants from config.json
GEM_RAFFLE_CHANNEL_ID = int(config.get('gem_raffle_channel_id', 1253431327588487243))
SERVER_ID = int(config.get('server_id', 1253407800302899220))

# Raffle information storage
raffle_info = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def raffle(ctx, reward: str, max_entries: int, max_per_member: int):
    # Ensure the command is executed only in the specified server
    if ctx.guild.id != SERVER_ID:
        return
    
    # Create a new text channel for the raffle
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
    }
    channel = await ctx.guild.create_text_channel(f'raffle-{reward}', overwrites=overwrites)
    
    # Add raffle information to the raffle_info dictionary
    raffle_id = len(raffle_info) + 1
    raffle_info[raffle_id] = {
        'reward': reward,
        'max_entries': max_entries,
        'max_per_member': max_per_member,
        'entries': 0,
        'creator': ctx.author,
        'channel': channel
    }
    
    # Send raffle information in the gem-raffle channel
    gem_channel = bot.get_channel(GEM_RAFFLE_CHANNEL_ID)
    if gem_channel:
        embed = discord.Embed(
            title="New Raffle!",
            description=f"**Reward:** {reward}\n**Max Entries:** {max_entries}\n**Max Tickets Per Member:** {max_per_member}\n\n*(Made by s6eg4se54g and ppiracy)*\n\nReact with 🎟️ to participate!"
        )
        msg = await gem_channel.send(embed=embed)
        await msg.add_reaction('🎟️')
    else:
        await ctx.send("The gem-raffle channel does not exist. Please check the channel ID.")

@bot.command()
async def purchase(ctx, raffle_id: int, num_tickets: int):
    if raffle_id not in raffle_info:
        await ctx.send("Invalid raffle ID.")
        return
    
    raffle = raffle_info[raffle_id]
    
    # Check if the raffle channel exists
    raffle_channel = bot.get_channel(raffle['channel'].id)
    if not raffle_channel:
        await ctx.send("The raffle channel does not exist. Please contact a moderator.")
        return
    
    # Create a new private channel for the ticket purchaser
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True),
        raffle['creator']: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
    }
    user_channel = await ctx.guild.create_text_channel(f'raffle-ticket-{ctx.author}', overwrites=overwrites)
    
    # Send ticket purchase confirmation
    await user_channel.send(f"You've purchased {num_tickets} ticket(s) for the raffle '{raffle['reward']}'.")

@bot.command()
async def permission(ctx, role: discord.Role):
    # Add permissions for the specified role to manage the raffle channels
    for raffle_id, raffle in raffle_info.items():
        raffle_channel = bot.get_channel(raffle['channel'].id)
        if raffle_channel:
            await raffle_channel.set_permissions(role, read_messages=True, manage_channels=True)

@bot.command()
async def stopraffle(ctx):
    # Check if the command is executed in a raffle channel
    if ctx.channel.id in [raffle['channel'].id for raffle_id, raffle in raffle_info.items()]:
        raffle_id = None
        for id, raffle in raffle_info.items():
            if raffle['channel'].id == ctx.channel.id:
                raffle_id = id
                break
        
        if raffle_id:
            raffle_channel = bot.get_channel(raffle_info[raffle_id]['channel'].id)
            await raffle_channel.delete()
            del raffle_info[raffle_id]
            await ctx.send("The raffle has been stopped and the channel deleted.")
    else:
        await ctx.send("You can only stop a raffle in its dedicated channel.")

bot.run(DISCORD_TOKEN)
