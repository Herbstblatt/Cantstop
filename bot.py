#!/usr/bin/env python3

from discord.ext import commands
import discord

import config
from cantstop import game, invite
from cantstop.constants import LIST_MARKER

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or('$'), 
            intents=discord.Intents.default(),  
            **kwargs
        )

    async def setup_hook(self) -> None:
        await self.load_extension("jishaku")
        
    async def on_ready(self):
        print(f'Logged on as {self.user}')

bot = Bot()  

@bot.tree.command(name="game")
async def field_cmd(interaction: discord.Interaction):
    """Start a new game
    
    """

    game_invite = invite.InviteView(host=interaction.user)
    await interaction.response.send_message(
        f"Participants:\n{LIST_MARKER} {interaction.user}", 
        view=game_invite
    )
    await game_invite.wait()
    
    if game_invite.status == invite.GameStatus.cancelled:
        await interaction.followup.send(f"{interaction.user} cancelled the game :confused:")
    elif game_invite.status == invite.GameStatus.requested_to_start:
        view = game.Game(players=game_invite.participants)
        await interaction.followup.send(content=view.content, view=view)

bot.run(config.token)
