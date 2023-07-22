from dataclasses import dataclass
import importlib
import os
from typing import TYPE_CHECKING, Awaitable, Callable, Dict, Optional

import yaml

if TYPE_CHECKING:
    from .invite import Room

@dataclass
class Game:
    name: str
    description: str
    emoji: str
    color: int
    min_players: Optional[int]
    max_players: Optional[int]

    callback: Callable[["Room"], Awaitable[None]]

    @classmethod
    def from_dir(cls, name: str):
        with open(os.path.join("bot/games", name, "metadata.yml"), encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        module = importlib.import_module(f"bot.games.{name}")
        return cls(
            name=data["name"],
            description=data["description"],
            emoji=data["emoji"],
            color=data["color"],
            min_players=data.get("min_players"),
            max_players=data.get("max_players"),
            callback=module.start
        )
        

    async def start(self, room: "Room") -> None:
        await self.callback(room)


def load_games() -> Dict[str, Game]:
    games: dict[str, Game] = {}
    for dir in os.listdir("bot/games"):
        games[dir] = Game.from_dir(dir)
    return games
