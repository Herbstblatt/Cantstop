from .game import add_stop, Games

async def setup(bot):
	add_stop(bot)
	await bot.add_cog(Games())

async def start(room):
	await room.view.active_interaction.followup.send('Введите команду `-help geograph`, чтобы узнать список доступных игр.')
	room.manager.delete(room)
