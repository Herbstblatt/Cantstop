from bot.core.invite import Room
from .game import Game


async def setup(_):
    pass

async def start(room: Room):
    assert room.view is not None and room.view.active_interaction is not None
    view = Game(room)
    await room.view.active_interaction.followup.send(content=view.content, view=view)
    view.last_reminder = await room.view.message.channel.send(f'Your turn, {view.current_player.mention}!')
