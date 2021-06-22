#!/usr/bin/env python3

from discord.ext import commands
from discord import ui
import discord

import config
from cantstop import game, invite
from cantstop.constants import LIST_MARKER

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=commands.when_mentioned_or('$'), **kwargs)
        
    async def on_ready(self):
        print(f'Logged on as {self.user} (ID: {self.user.id})')

bot = Bot()  

@bot.command(name="game")
async def field_cmd(ctx):
    game_invite = invite.InviteView(caller=ctx.author)
    await ctx.send(f"Participants:\n{LIST_MARKER} {ctx.author}", view=game_invite)
    await game_invite.wait()
    if game_invite.status == invite.GameStatus.cancelled:
        await ctx.send("Game cancelled")
    elif game_invite.status == invite.GameStatus.requested_to_start:
        print(game_invite.participants)
        view = game.Game(ctx=ctx, players=game_invite.participants)
        msg = await ctx.send(content=view.content, view=view)
        view.message = msg
        await view.wait()
        print("Done!")

bot.run(config.token)
