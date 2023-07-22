import discord
import asyncio
import json
import requests
from discord.ext import commands
from random import choice, randint
from bot.core.invite import RoomState
games = {}
last_id = {}
with open('bot/games/geograph/data.json', encoding='utf-8') as f:
	data = json.load(f)
data['continents']['old']['Мир'] = [i for sub in data['continents']['old'].values() for i in sub]
data['continents']['general']['Мир'] = [i for sub in data['continents']['general'].values() for i in sub]

async def create_room(game, ctx):
	cog = ctx.bot.get_cog('Commands')
	await cog.create.callback(cog, ctx, ctx.bot.games[game])

async def start_game(game, ctx, rounds, continent):
	# Проверка канала игры
	if games.get(ctx.channel.id):
		await ctx.send('В данном канале уже запущена игра. Дождитесь её окончания или запустите игру в другом канале.')
	# Проверка континента
	elif continent.title() not in data['continents']['general']:
		await ctx.send('Данного континента не существует. Доступные континенты: Мир, Азия, Африка, Европа, Океания, Северная Америка, Южная Америка.')
	# Проверка числа раундов
	elif not rounds.isdigit():
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
				right = await flags(ctx.channel)
			if game == 'old':
				right = await old(ctx.channel)
			if game == 'maps':
				right = await maps(ctx.channel)
			if game == 'capitals':
				right = await capitals(ctx.channel)
			if game == 'pst_capitals':
				right = await pst_capitals(ctx.channel)
			if right: break
		else:
			if games[ctx.channel.id]['count'] >= games[ctx.channel.id]['max_count']:
				leaders = [f'**{ctx.guild.get_member(k).global_name}** ({v})' for k,v in games[ctx.channel.id]['leaders'].items()]
				await ctx.channel.send(f"Игра закончена. Статистика: {', '.join(leaders)}.")
				del games[ctx.channel.id]

async def flags(channel):
	id = games[channel.id]['id']
	country = choice(list(set(data['continents']['general'][games[channel.id]['continent']]).difference(games[channel.id]['answered'])))
	games[channel.id]['answer'] = country
	games[channel.id]['count'] += 1
	flag_pic = requests.get(f"https://commons.wikimedia.org/w/api.php?action=query&titles=File:Flag_of_{data['flags'][country]}.svg&prop=imageinfo&iiprop=url&format=json").json()
	embed = discord.Embed(title=f"Флаги: {games[channel.id]['count']}/{games[channel.id]['max_count']}", description='Назвите страну, имеющую данный флаг', color=0x0086ff)
	embed.set_image(url=flag_pic['query']['pages'][list(flag_pic['query']['pages'])[0]]['imageinfo'][0]['url'].replace('commons', 'commons/thumb') + f"/200px-Flag_of_{data['flags'][country].replace(' ', '_')}.svg.png")
	await channel.send(embed=embed)
	await asyncio.sleep(15)
	if id == games.get(channel.id, {'id': 0})['id'] and country not in games[channel.id]['answered']:
		games[channel.id]['answered'].append(country)
		await channel.send(f'Правильный ответ: **{games[channel.id]["answer"]}**')
		return False
	return True

async def old(channel):
	id = games[channel.id]['id']
	country = choice(list(set(data['continents']['old'][games[channel.id]['continent']]).difference(games[channel.id]['answered'])))
	games[channel.id]['answer'] = country
	games[channel.id]['count'] += 1
	flag_pic = requests.get(f"https://commons.wikimedia.org/w/api.php?action=query&titles=File:{data['old'][country]}{'.png' if country == 'Монгольская империя' else '.svg'}&prop=imageinfo&iiprop=url&format=json").json()
	embed = discord.Embed(title=f"Флаги бывших стран: {games[channel.id]['count']}/{games[channel.id]['max_count']}", description='Назвите страну, имеющую данный флаг', color=0x0086ff)
	embed.set_image(url=flag_pic['query']['pages'][list(flag_pic['query']['pages'])[0]]['imageinfo'][0]['url'].replace('commons', 'commons/thumb') + f"/200px-{data['old'][country].replace(' ', '_')}{'' if country == 'Монгольская империя' else '.svg'}.png")
	await channel.send(embed=embed)
	await asyncio.sleep(15)
	if id == games.get(channel.id, {'id': 0})['id'] and country not in games[channel.id]['answered']:
		games[channel.id]['answered'].append(country)
		await channel.send(f'Правильный ответ: **{games[channel.id]["answer"]}**')
		return False
	return True

async def maps(channel):
	id = games[channel.id]['id']
	country = choice(list(set(data['continents']['general'][games[channel.id]['continent']]).intersection(data['maps']).difference(games[channel.id]['answered'])))
	games[channel.id]['answer'] = country
	games[channel.id]['count'] += 1
	embed = discord.Embed(title=f"Карты: {games[channel.id]['count']}/{games[channel.id]['max_count']}", description='Назвите страну, указанную на карте', color=0x0086ff)
	embed.set_image(url=f"https://cdn.discordapp.com/attachments/1038366862007869492/{data['maps'][country]}.png")
	await channel.send(embed=embed)
	await asyncio.sleep(15)
	if id == games.get(channel.id, {'id': 0})['id'] and country not in games[channel.id]['answered']:
		games[channel.id]['answered'].append(country)
		await channel.send(f'Правильный ответ: **{games[channel.id]["answer"]}**')
		return False
	return True

async def capitals(channel):
	id = games[channel.id]['id']
	country = choice(list(set(data['continents']['general'][games[channel.id]['continent']]).difference(games[channel.id]['answered'])))
	games[channel.id]['country'] = country
	games[channel.id]['answer'] = data['capitals'][country]
	games[channel.id]['count'] += 1
	embed = discord.Embed(title=f"Столицы: {games[channel.id]['count']}/{games[channel.id]['max_count']}", description=f'Назвите столицу следующей страны: **{country}**', color=0x0086ff)
	await channel.send(embed=embed)
	await asyncio.sleep(15)
	if id == games.get(channel.id, {'id': 0})['id'] and country not in games[channel.id]['answered']:
		games[channel.id]['answered'].append(country)
		await channel.send(f'Правильный ответ: **{games[channel.id]["answer"]}**')
		return False
	return True

async def pst_capitals(channel):
	id = games[channel.id]['id']
	country = choice(list(set(data['pst_capitals']).difference(games[channel.id]['answered'])))
	games[channel.id]['country'] = country
	games[channel.id]['answer'] = data['pst_capitals'][country]
	games[channel.id]['count'] += 1
	embed = discord.Embed(title=f"Столицы: {games[channel.id]['count']}/{games[channel.id]['max_count']}", description=f'Назвите столицу следующего субъекта постсоветской страны: **{country}**', color=0x0086ff)
	await channel.send(embed=embed)
	await asyncio.sleep(15)
	if id == games.get(channel.id, {'id': 0})['id'] and country not in games[channel.id]['answered']:
		games[channel.id]['answered'].append(country)
		await channel.send(f'Правильный ответ: **{games[channel.id]["answer"]}**')
		return False
	return True

class Games(commands.Cog):
	@commands.Cog.listener()
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
				if games[message.channel.id]['count'] >= games[message.channel.id]['max_count']:
					leaders = [f'**{message.guild.get_member(k).global_name}** ({v})' for k,v in games[message.channel.id]['leaders'].items()]
					await message.channel.send(f"Игра закончена. Статистика: {', '.join(leaders)}.")
					del games[message.channel.id]

	@commands.command()
	async def bukvitsa(self, ctx):
		await create_room('bukvitsa', ctx)

	@commands.command()
	async def cantstop(self, ctx):
		await create_room('cantstop', ctx)

	@commands.command()
	async def mafia(self, ctx):
		for room in ctx.bot.rooms:
			if room.game.name == 'Мафия' and room.state == RoomState.game_in_progress and room.view.message.channel.id == ctx.channel.id:
				await ctx.send('В данном канале уже запущена игра. Дождитесь её окончания или запустите игру в другом канале.')
				return
		await create_room('mafia', ctx)

	@commands.hybrid_group()
	async def geograph(self, ctx):
		await ctx.send('Введите команду `-help geograph`, чтобы узнать список доступных игр.')

	@geograph.command(name='flags', brief='Угадайте страну по флагу')
	async def flags_cmd(self, ctx, rounds='10', continent='Мир'):
		await start_game('flags', ctx, rounds, continent)

	@geograph.command(name='old', brief='Угадайте бывшую страну по флагу')
	async def old_cmd(self, ctx, rounds='10', continent='Мир'):
		await start_game('old', ctx, rounds, continent)

	@geograph.command(name='maps', brief='Угадайте страну по расположению на карте')
	async def maps_cmd(self, ctx, rounds='10', continent='Мир'):
		await start_game('maps', ctx, rounds, continent)
			
	@geograph.command(name='capitals', brief='Угадайте столицу страны')
	async def capitals_cmd(self, ctx, rounds='10', continent='Мир'):
		await start_game('capitals', ctx, rounds, continent)

	@geograph.command(name='pst_capitals', brief='Угадайте столицу субъекта постсоветских стран')
	async def pst_capitals_cmd(self, ctx, rounds='10'):
		await start_game('pst_capitals', ctx, rounds, 'Мир')

	@geograph.command(brief='Останавливает игру.')
	async def stop(self, ctx):
		await ctx.send('Игра закончена.')
		del games[ctx.channel.id]