from bot.core.game import load_games
from bot.core.invite import Room
from .game import Game


async def setup(_):
    pass

async def start(room: Room):
    assert room.view is not None and room.view.active_interaction is not None
    view = Game(players=room.participants)
    await room.view.active_interaction.followup.send(content=view.content, view=view)
