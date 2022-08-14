from dataclasses import dataclass
import importlib
import os
from typing import Awaitable, Callable, List

import discord
import yaml

@dataclass
class Game:
    name: str
    description: str
    min_players: int
    max_players: int

    callback: Callable[[discord.Interaction, List[discord.Member]], Awaitable[None]]

    @classmethod
    def from_dir(cls, name: str):
        with open(os.path.join("bot/games", name, "metadata.yml")) as f:
            data = yaml.safe_load(f)
        
        module = importlib.import_module(f"bot.games.{name}")
        return cls(
            name=data["name"],
            description=data["description"],
            min_players=data["min_players"],
            max_players=data["max_players"],
            callback=module.start
        )
        

    async def start(self, interaction: discord.Interaction, participants: List[discord.Member]) -> None:
        await self.callback(interaction, participants)
