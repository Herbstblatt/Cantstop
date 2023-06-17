from .game import GeographCog

async def setup(bot):
    await bot.add_cog(GeographCog())

async def start(room):
    for member in room.participants:
      await room.remove_participant(member)
    await room.view.active_interaction.followup.send('Введите команду `-help geograph`, чтобы узнать список доступных игр.')
