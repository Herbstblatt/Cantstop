import discord
import asyncio
import json
import requests
from random import choice, randint
from bot.core.invite import RoomState
from discord import app_commands, Interaction, Embed
from discord.ext.commands import command, Context, Cog
games = {}
last_id = {}
with open('bot/games/geograph/data.json', encoding='utf-8') as f:
	data = json.load(f)
data['continents']['old']['Мир'] = [i for sub in data['continents']['old'].values() for i in sub]
data['continents']['general']['Мир'] = [i for sub in data['continents']['general'].values() for i in sub]
get_name = lambda user: user.global_name if user.global_name else user.name
games_name = {
	'flags': 'Флаги', 
	'maps': 'Карты', 
	'capitals': 'Столицы', 
	'old': 'Флаги бывших стран', 
	'pst_capitals': 'Столицы субъектов постсоветских стран'
}

def add_stop(bot):
	cog = bot.get_cog('Commands')
	@cog.game.command(brief='Останавливает игру (география)')
	async def stop(ctx):
		if ctx.channel.id in games:
			await ctx.send('Игра закончена.')
			del games[ctx.channel.id]
		else:
			await ctx.send('В данном канале не запущена игра.')

async def create_room(game, ctx):
	if isinstance(ctx, Interaction):
		ctx = await Context.from_interaction(ctx)
	cog = ctx.bot.get_cog('Commands')
	await cog.create.callback(cog, ctx, ctx.bot.games[game])

async def start_game(game, ctx, rounds, continent):
	if isinstance(ctx, Interaction):
		ctx = await Context.from_interaction(ctx)
	# Проверка канала игры
	if ctx.channel.id in games:
		await ctx.send('В данном канале уже запущена игра. Дождитесь её окончания или запустите игру в другом канале.')
	# Проверка континента
	elif continent.title() not in data['continents']['general']:
		await ctx.send('Данного континента не существует. Доступные континенты: Мир, Азия, Африка, Европа, Океания, Северная Америка, Южная Америка.')
	# Проверка числа раундов
	elif not str(rounds).isdigit():
		await ctx.send('Число раундов должно быть целым числом.')
	elif int(rounds) < 1:
		await ctx.send('Число раундов не может быть меньше 1.')
	elif continent == 'Мир' and int(rounds) > len(data[game]):
		await ctx.send(f'Число раундов не может быть больше {len(data[game])}.')
	elif continent != 'Мир' and int(rounds) > len(set(data['continents']['old' if game == 'old' else 'general'][continent.title()]).intersection(data[game])):
		await ctx.send(f"Число раундов не может быть больше {len(set(data['continents']['old' if game == 'old' else 'general'][continent.title()]).intersection(data[game]))}.")
	# Если всё правильно
	else:
		games[ctx.channel.id] = {'game': game, 'count': 0, 'max_count': int(rounds), 'continent': continent.title(), 'answered': [], 'leaders': {}, 'actived': False}
		games[ctx.channel.id]['id'] = randint(1, 1000)
		if games[ctx.channel.id]['id'] == last_id.get(ctx.channel.id):
			games[ctx.channel.id]['id'] = randint(1, 1000)
		last_id[ctx.channel.id] = games[ctx.channel.id]['id']
		while not games[ctx.channel.id]['actived'] and games[ctx.channel.id]['count'] < games[ctx.channel.id]['max_count']:
			if game == 'flags':
				right = await flags(ctx)
			if game == 'old':
				right = await old(ctx)
			if game == 'maps':
				right = await maps(ctx)
			if game == 'capitals':
				right = await capitals(ctx)
			if game == 'pst_capitals':
				right = await pst_capitals(ctx)
			if right: break
		else:
			if games[interaction.channel.id]['count'] >= games[interaction.channel.id]['max_count'] and games[interaction.channel.id]['leaders']:
				leaders = [f'**{get_name(interaction.guild.get_member(k))}** ({v})' for k,v in games[interaction.channel.id]['leaders'].items()]
				await interaction.channel.send(f"Игра закончена. Статистика: {', '.join(leaders)}.")
				del games[interaction.channel.id]
			elif games[interaction.channel.id]['count'] >= games[interaction.channel.id]['max_count']:
				await interaction.channel.send('Игра закончена.')

async def flags(ctx):
	channel = ctx.channel if isinstance(ctx, Context) else ctx
	country = choice(list(set(data['continents']['general'][games[channel.id]['continent']]).difference(games[channel.id]['answered'])))
	id = games[channel.id]['id']
	games[channel.id]['answer'] = country
	games[channel.id]['count'] += 1
	flag_pic = requests.get(f"https://commons.wikimedia.org/w/api.php?action=query&titles=File:Flag_of_{data['flags'][country]}.svg&prop=imageinfo&iiprop=url&format=json").json()
	embed = Embed(title=f"Флаги: {games[channel.id]['count']}/{games[channel.id]['max_count']}", description='Назвите страну, имеющую данный флаг', color=0x0086ff)
	embed.set_image(url=flag_pic['query']['pages'][list(flag_pic['query']['pages'])[0]]['imageinfo'][0]['url'].replace('commons', 'commons/thumb') + f"/200px-Flag_of_{data['flags'][country].replace(' ', '_')}.svg.png")
	await ctx.send(embed=embed)
	await asyncio.sleep(15)
	if id == games.get(channel.id, {'id': 0})['id'] and country not in games[channel.id]['answered']:
		games[channel.id]['answered'].append(country)
		await channel.send(f'Правильный ответ: **{games[channel.id]["answer"]}**')
		return False
	return True

async def old(ctx):
	channel = ctx.channel if isinstance(ctx, Context) else ctx
	country = choice(list(set(data['continents']['old'][games[channel.id]['continent']]).difference(games[channel.id]['answered'])))
	id = games[channel.id]['id']
	games[channel.id]['answer'] = country
	games[channel.id]['count'] += 1
	flag_pic = requests.get(f"https://commons.wikimedia.org/w/api.php?action=query&titles=File:{data['old'][country]}{'.png' if country == 'Монгольская империя' else '.svg'}&prop=imageinfo&iiprop=url&format=json").json()
	embed = Embed(title=f"Флаги бывших стран: {games[channel.id]['count']}/{games[channel.id]['max_count']}", description='Назвите страну, имеющую данный флаг', color=0x0086ff)
	embed.set_image(url=flag_pic['query']['pages'][list(flag_pic['query']['pages'])[0]]['imageinfo'][0]['url'].replace('commons', 'commons/thumb') + f"/200px-{data['old'][country].replace(' ', '_')}{'' if country == 'Монгольская империя' else '.svg'}.png")
	await ctx.send(embed=embed)
	await asyncio.sleep(15)
	if id == games.get(channel.id, {'id': 0})['id'] and country not in games[channel.id]['answered']:
		games[channel.id]['answered'].append(country)
		await channel.send(f'Правильный ответ: **{games[channel.id]["answer"]}**')
		return False
	return True

async def maps(ctx):
	channel = ctx.channel if isinstance(ctx, Context) else ctx
	country = choice(list(set(data['continents']['general'][games[channel.id]['continent']]).intersection(data['maps']).difference(games[channel.id]['answered'])))
	id = games[channel.id]['id']
	games[channel.id]['answer'] = country
	games[channel.id]['count'] += 1
	embed = Embed(title=f"Карты: {games[channel.id]['count']}/{games[channel.id]['max_count']}", description='Назвите страну, указанную на карте', color=0x0086ff)
	embed.set_image(url=f"https://cdn.discordapp.com/attachments/1038366862007869492/{data['maps'][country]}.png")
	await ctx.send(embed=embed)
	await asyncio.sleep(15)
	if id == games.get(channel.id, {'id': 0})['id'] and country not in games[channel.id]['answered']:
		games[channel.id]['answered'].append(country)
		await channel.send(f'Правильный ответ: **{games[channel.id]["answer"]}**')
		return False
	return True

async def capitals(ctx):
	channel = ctx.channel if isinstance(ctx, Context) else ctx
	country = choice(list(set(data['continents']['general'][games[channel.id]['continent']]).difference(games[channel.id]['answered'])))
	id = games[channel.id]['id']
	games[channel.id]['country'] = country
	games[channel.id]['answer'] = data['capitals'][country]
	games[channel.id]['count'] += 1
	embed = Embed(title=f"Столицы: {games[channel.id]['count']}/{games[channel.id]['max_count']}", description=f'Назвите столицу следующей страны: **{country}**', color=0x0086ff)
	await ctx.send(embed=embed)
	await asyncio.sleep(15)
	if id == games.get(channel.id, {'id': 0})['id'] and country not in games[channel.id]['answered']:
		games[channel.id]['answered'].append(country)
		await channel.send(f'Правильный ответ: **{games[channel.id]["answer"]}**')
		return False
	return True

async def pst_capitals(ctx):
	channel = ctx.channel if isinstance(ctx, Context) else ctx
	country = choice(list(set(data['pst_capitals']).difference(games[channel.id]['answered'])))
	id = games[channel.id]['id']
	games[channel.id]['country'] = country
	games[channel.id]['answer'] = data['pst_capitals'][country]
	games[channel.id]['count'] += 1
	embed = Embed(title=f"Столицы: {games[channel.id]['count']}/{games[channel.id]['max_count']}", description=f'Назвите столицу следующего субъекта постсоветской страны: **{country}**', color=0x0086ff)
	await ctx.send(embed=embed)
	await asyncio.sleep(15)
	if id == games.get(channel.id, {'id': 0})['id'] and country not in games[channel.id]['answered']:
		games[channel.id]['answered'].append(country)
		await channel.send(f'Правильный ответ: **{games[channel.id]["answer"]}**')
		return False
	return True

class Games(Cog):
	@Cog.listener()
	async def on_message(self, message):
		if message.channel.id in games and all((
			games[message.channel.id]['answer'] not in games[message.channel.id]['answered'],
			message.content.lower() in (getattr(data['aliases'].get(games[message.channel.id]['answer']), 'lower', lambda: None)(), games[message.channel.id]['answer'].lower())
		)):
			if games[message.channel.id]['game'] in ('capitals', 'pst_capitals'):
				games[message.channel.id]['answered'].append(games[message.channel.id]['country'])
			else:
				games[message.channel.id]['answered'].append(games[message.channel.id]['answer'])
			await message.add_reaction("✅")
			if message.author.id not in games[message.channel.id]['leaders']:
				games[message.channel.id]['leaders'][message.author.id] = 1
			else:
				games[message.channel.id]['leaders'][message.author.id] += 1
			if not games[message.channel.id]['actived']:
				games[message.channel.id]['actived'] = True
			while games[message.channel.id]['count'] < games[message.channel.id]['max_count']:
				if games[message.channel.id]['game'] == 'flags':
					right = await flags(message.channel)
				elif games[message.channel.id]['game'] == 'old':
					right = await old(message.channel)
				elif games[message.channel.id]['game'] == 'maps':
					right = await maps(message.channel)
				elif games[message.channel.id]['game'] == 'capitals':
					right = await capitals(message.channel)
				elif games[message.channel.id]['game'] == 'pst_capitals':
					right = await pst_capitals(message.channel)
				if message.channel.id not in games:
					return
				if right: break
			else:
				if games[message.channel.id]['count'] >= games[message.channel.id]['max_count'] and games[message.channel.id]['leaders']:
					leaders = [f'**{get_name(message.guild.get_member(k))}** ({v})' for k,v in games[message.channel.id]['leaders'].items()]
					await message.channel.send(f"Игра закончена. Статистика: {', '.join(leaders)}.")
					del games[message.channel.id]
				elif games[message.channel.id]['count'] >= games[message.channel.id]['max_count']:
					await message.channel.send('Игра закончена.')

	@command()
	async def bukvitsa(self, ctx):
		await create_room('bukvitsa', ctx)

	@app_commands.command(name='bukvitsa')
	async def bukvitsa_slash(self, interaction):
		await create_room('bukvitsa', interaction)

	@command()
	async def cantstop(self, ctx):
		await create_room('cantstop', ctx)

	@app_commands.command(name='cantstop')
	async def cantstop_slash(self, interaction):
		await create_room('cantstop', interaction)

	@command()
	async def mafia(self, ctx):
		for room in ctx.bot.rooms:
			if room.game.name == 'Мафия' and room.state == RoomState.game_in_progress and room.view.message.channel.id == ctx.channel.id:
				await ctx.send('В данном канале уже запущена игра. Дождитесь её окончания или запустите игру в другом канале.')
				return
		await create_room('mafia', ctx)

	@app_commands.command(name='mafia')
	async def mafia_slash(self, interaction):
		ctx = await Context.from_interaction(interaction)
		for room in ctx.bot.rooms:
			if room.game.name == 'Мафия' and room.state == RoomState.game_in_progress and room.view.message.channel.id == ctx.channel.id:
				await ctx.send('В данном канале уже запущена игра. Дождитесь её окончания или запустите игру в другом канале.')
				return
		await create_room('mafia', ctx)

	@command()
	async def geograph(self, ctx, game, rounds='10', continent='Мир'):
		if ctx.invoked_subcommand: return
		if game in ('flags', 'old', 'maps', 'capitals', 'pst_capitals'):
			await start_game(game, ctx, rounds, 'Мир' if game == 'pst_capitals' else continent)
		elif game == 'stop':
			await ctx.send('Игра закончена.')
			del games[ctx.channel.id]
		else:
			await ctx.send('Данной игры не существует. Доступные игры: flags, old, maps, capitals, pst_capitals.')

	@app_commands.command(name='geograph')
	@app_commands.describe(game='Игра, в которую вы хотите сыграть', rounds='Количество раундов в игре', continent='Континент, страны которого будут в игре')
	@app_commands.choices(
		game=[app_commands.Choice(name=v, value=k) for k,v in games_name.items()],
		continent=[app_commands.Choice(name=i, value=i) for i in data['continents']['general']]
	)
	async def geograph_slash(self, interaction, game:app_commands.Choice[str], rounds:int=10, continent:app_commands.Choice[str]=None):
		if game.value != 'pst_capitals' and getattr(continent, 'value', None):
			await start_game(game.value, interaction, rounds, continent.value)
		else:
			await start_game(game.value, interaction, rounds, 'Мир')
