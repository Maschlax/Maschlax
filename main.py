import asyncio
import os
import random
from contextlib import suppress

import discord
from discord import components
from discord.ext import commands, tasks

import config
from discord.ui import Button, button, View

from server import stay_alive
import datetime

intents = discord.Intents.default()
intents.message_content = True

# prefix

bot = commands.Bot(command_prefix='+', intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('Wish Attack 3'))

    print('')
    print('------------------------------')
    print('Connected to: {}'.format(bot.user.name))
    print('------------------------------')
    print('')

#help

@bot.command()
@commands.has_role("Admin")
async def info(ctx):
  embed = discord.Embed(title="**Help**", description="**Prefix :** + \n**info :** Send this message \n**SCmsg :** Send message in channel \n**SUmsg <user> <message> :** Send User message\n**SCEmb :** Send Embed in channel \n**SCnEmb :** Send Embed without title \n**mute <user> <reason> :** Mute someone (with reason) \n**unmute <user> :** Unmute someone \n**clear <amount> :** Clear <amount> messages in channel", color=discord.Color.yellow())
  await ctx.send(embed=embed)


# sendchannelmsg


@bot.command()
@commands.has_role("Admin")
async def SCmsg(ctx, *, message):
  message = message
  await ctx.send(message)

# sendusermsg


@bot.command()
@commands.has_role("Admin")
async def SUmsg(ctx, user: discord.User, *, message):
  if ctx.author.bot:
    return

  try:
    await user.send(message)
    await ctx.send(f'Nachricht an {user.mention} gesendet.')

  except discord.Forbidden:
    await ctx.send(
        f'Ich kann {user.mention} keine Nachricht senden, da sie private Nachrichten von Servermitgliedern deaktiviert haben oder ich keine Berechtigung dazu habe.'
    )


# sendEmb


@bot.command()
@commands.has_role("Admin")
async def SCEmb(ctx, title, *, text):
  embed = discord.Embed(title=title,
                        description=text,
                        color=discord.Color.brand_green())

  await ctx.send(embed=embed)


# sendEmbNoTitle


@bot.command()
@commands.has_role("Admin")
async def SCnEmb(ctx, *, text):
  embed = discord.Embed(description=text, color=discord.Color.brand_green())
  await ctx.send(embed=embed)


# mute


@bot.command()
@commands.has_any_role('Admin', 'Moderator')
async def mute(ctx, user: discord.Member, reason=None):
  mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
  if not mute_role:
    mute_role = await ctx.guild.create_role(name="Muted")
  username = ctx.author.mention
  await user.add_roles(mute_role)
  if mute_role not in user.roles:
    if reason:
      embed = discord.Embed(
          description=
          f'{user.mention} got muted by {username}. Reason: {reason}',
          color=discord.Color.red())
      await ctx.send(embed=embed)
      await user.send(
          f'*You got muted in* "{ctx.guild.name}" \n **Reason:** {reason}')
    else:
      embed = discord.Embed(
          description=f'{user.mention} got muted by {username}.',
          color=discord.Color.red())
      await ctx.send(embed=embed)
  else:
    embed = discord.Embed(description="This user is already muted.",
                          color=discord.Color.dark_red())
    await ctx.send(embed=embed)


# unmute


@bot.command(pass_context=True)
@commands.has_any_role("Admin", "Moderator")
async def unmute(ctx, user: discord.Member):
  mute_role = discord.utils.get(ctx.guild.roles, name="Muted")

  if mute_role in user.roles:
    embed = discord.Embed(
        description=f"{user.mention} has been unmuted by {ctx.author.mention}",
        color=discord.Color.blue())
    await user.remove_roles(mute_role)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(description="This user isn't muted.",
                          color=discord.Color.dark_red())
    await ctx.send(embed=embed)


#clear


@bot.command()
@commands.has_any_role("Admin", "Moderator")
async def clear(ctx, amount: int):
  if ctx.author.guild_permissions.manage_messages:
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"{amount} Messages deleted.", delete_after=3)
  else:
    await ctx.send("You don't have the permission to do that.")


#ticketsystem

class CreateButton(View):
  def __init__(self):
    super().__init__(timeout=None)

  @button(label="Create Ticket", style=discord.ButtonStyle.blurple, emoji="🎫", custom_id="ticketopen")
  async def ticket(self, interaction: discord.Interaction, button: Button):
    await interaction.response.defer(ephemeral=True)
    category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=1106705352583553126)
    for ch in category.channels:
      if ch.topic == f"{interaction.user.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL!":
        await interaction.followup.send("You already have a ticket in {0}".format(ch.mention), ephemeral=True)
        return

    r1 : discord.Role = interaction.guild.get_role(1150498038138273802)
    overwrites = {
      interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
      r1: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
      interaction.user: discord.PermissionOverwrite(read_messages = True, send_messages=True),
      interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    channel = await category.create_text_channel(
      name=interaction.user.name,
      topic=f"{interaction.user.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL!",
      overwrites=overwrites
    )
    await channel.send(
      embed=discord.Embed(
        title="Ticket Created!",
        description="Just wait a little bit. We'll be here soon!",
        color = discord.Color.teal()
      )
    )
    await interaction.followup.send(
      embed= discord.Embed(
        description = "Created your ticket in {0}".format(channel.mention),
        color = discord.Color.green()
      )
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def ticket(ctx):
  await ctx.send(
    embed = discord.Embed(
      description="Press the button to create a new ticket!"
    ),
    view = CreateButton()
  )

#giveaway

@bot.command()
@commands.has_role("Admin")
async def giveaway(ctx):
    # Giveaway command requires the user to have a "Admin" role to function properly

    # Stores the questions that the bot will ask the user to answer in the channel that the command was made
    # Stores the answers for those questions in a different list
    giveaway_questions = ['Which channel will I host the giveaway in?', 'What is the prize?', 'How long should the giveaway run for (in seconds)?',]
    giveaway_answers = []

    # Checking to be sure the author is the one who answered and in which channel
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    # Askes the questions from the giveaway_questions list 1 by 1
    # Times out if the host doesn't answer within 30 seconds
    for question in giveaway_questions:
        await ctx.send(question)
        try:
            message = await bot.wait_for('message', timeout= 30.0, check= check)
        except asyncio.TimeoutError:
            await ctx.send('You didn\'t answer in time. Please try again and be sure to send your answer within 30 seconds of the question.')
            return
        else:
            giveaway_answers.append(message.content)

    # Grabbing the channel id from the giveaway_questions list and formatting is properly
    # Displays an exception message if the host fails to mention the channel correctly
    try:
        c_id = int(giveaway_answers[0][2:-1])
    except:
        await ctx.send(f'You failed to mention the channel correctly. Please do it like this: {ctx.channel.mention}')
        return
    
    # Storing the variables needed to run the rest of the commands
    channel = bot.get_channel(c_id)
    prize = str(giveaway_answers[1])
    time = int(giveaway_answers[2])

    # Sends a message to let the host know that the giveaway was started properly
    await ctx.send(f'The giveaway for {prize} will begin shortly.\nPlease direct your attention to {channel.mention}, this giveaway will end in {time} seconds.')

    # Giveaway embed message
    give = discord.Embed(color = 0x2ecc71)
    give.set_author(name = f'GIVEAWAY TIME!', icon_url = 'https://i.imgur.com/VaX0pfM.png')
    give.add_field(name= f'{ctx.author.name} is giving away: {prize}!', value = f'React with 🎉 to enter!\n Ends in {round(time/60, 2)} minutes!', inline = False)
    end = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)
    give.set_footer(text = f'Giveaway ends at {end.strftime("%m/%d/%Y, %H:%M")} UTC!')
    my_message = await channel.send(embed = give)
    
    # Reacts to the message
    await my_message.add_reaction("🎉")
    await asyncio.sleep(time)

    new_message = await channel.fetch_message(my_message.id)

    # Picks a winner
    users = await new_message.reactions[0].users().flatten()
    users.pop(users.index(discord.User))
    winner = random.choice(users)

    # Announces the winner
    winning_announcement = discord.Embed(color = 0xff2424)
    winning_announcement.set_author(name = f'THE GIVEAWAY HAS ENDED!', icon_url= 'https://i.imgur.com/DDric14.png')
    winning_announcement.add_field(name = f'🎉 Prize: {prize}', value = f'🥳 **Winner**: {winner.mention}\n 🎫 **Number of Entrants**: {len(users)}', inline = False)
    winning_announcement.set_footer(text = 'Thanks for entering!')
    await channel.send(embed = winning_announcement)



@bot.command()
@commands.has_role("Admin")
async def reroll(ctx, channel: discord.TextChannel, id_ : int):
    # Reroll command requires the user to have a "Admin" role to function properly
    try:
        new_message = await channel.fetch_message(id_)
    except:
        await ctx.send("Incorrect id.")
        return
    
    # Picks a new winner
    users = await new_message.reactions[0].users().flatten()
    users.pop(users.index(bot.user))
    winner = random.choice(users)

    # Announces the new winner to the server
    reroll_announcement = discord.Embed(color = 0xff2424)
    reroll_announcement.set_author(name = f'The giveaway was re-rolled by the host!', icon_url = 'https://i.imgur.com/DDric14.png')
    reroll_announcement.add_field(name = f'🥳 New Winner:', value = f'{winner.mention}', inline = False)
    await channel.send(embed = reroll_announcement)

#type2giveaway

@bot.command()
async def gway(ctx, channel: discord.TextChannel, prize: str, winners: int, duration: int):
    participants = []
    
    embed = discord.Embed(title="Giveaway", description="**Prize:** " + str(prize) + "\n**Winners:**" + str(winners) + "\n**Ends in:** " + str(duration) + " seconds", color=discord.Color.og_blurple())
    
    message = await channel.send(embed=embed)
    await message.add_reaction("🎉")

    def check(reaction, user):
        return user != bot.user and str(reaction.emoji) == "🎉" and reaction.message.id == message.id

    try:
        while True:
            reaction, user = await bot.wait_for('reaction_add', timeout=duration)
            if check(reaction, user):
                if user not in participants:
                    participants.append(user)
                    dm_channel = await user.create_dm()
                    await dm_channel.send(f"You have entered the giveaway for **{prize}**!")
                else:
                    dm_channel = await user.create_dm()
                    await dm_channel.send("You have already entered the giveaway!")

    except asyncio.TimeoutError:
        if len(participants) < winners:
            await channel.send("Not enough participants to pick a winner.")
        else:
            winner_list = random.sample(participants, k=winners)
            winners_mention = ' '.join([winner.mention for winner in winner_list])
            reply_message = f"Congratulations {winners_mention}! You won **{prize}**!"
            await message.reply(reply_message)


DISCORD_TOKEN = os.environ['DISCORD_TOKEN']

stay_alive()
bot.run(MTE1MDE1OTMxOTI3OTYwNzkyOA.GsquGh.CAdGOkTyZ6EDpuYum5N28beVBjLrDFJ1KVEZiA)
