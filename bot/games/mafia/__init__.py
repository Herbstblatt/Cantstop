import discord
import asyncio
from random import randint, choice
from bot.core.invite import RoomState
from .selects import SelectPlayer
from .game import roles, values, sentences, summarize, InviteMember
mafia = {}
last_id = {}
get_mafia = lambda id: {v:k for k,v in mafia[id]['roles'].items()}.get('mafia')
get_putana = lambda id: {v:k for k,v in mafia[id]['roles'].items()}.get('putana')

def voting(id):
	del mafia[id]

async def wait(view, channel_id):
	id = mafia[channel_id]['id']
	await asyncio.sleep(120)
	view.stop()
	if mafia.get(channel_id) and id == mafia[channel_id]['id'] and not mafia[channel_id]['early_vote']:
		await summarize(mafia[channel_id])
		if mafia[channel_id]['time'] == 'end':
			del mafia[channel_id]

async def send_dm(role, view, channel):
	params = mafia[channel.id]
	if role in params['roles'].values() and [k for k,v in params['roles'].items() if v == role][0] in params['players']:
		role_name = values['roles_list'][role][1] if params['room'].settings['roles_name'] == 'russia' else roles[role][0]
		if get_putana(channel.id) in params['players'] and role != 'putana':
			await channel.send(f"Просыпается {role_name}. У {'неё' if role == 'mafia' and params['room'].settings['roles_name'] != 'russia' else 'него'} {values['roles_time'][params['room'].settings['roles_time']]} для {roles[role][2]}.")
		elif get_putana(channel.id) not in params['players'] and role != 'mafia':
			await channel.send(f"Просыпается {role_name}. У него {values['roles_time'][params['room'].settings['roles_time']]} для {roles[role][2]}.")
		view.add_item(SelectPlayer(params, role))
		user = channel.guild.get_member([k for k,v in params['roles'].items() if v == role][0])
		try:
			await user.send(f'Вы проснулись. Выберите игрока, которого хотите {roles[role][3]}:', view=view)
		except discord.errors.Forbidden:
			pass

async def setup(bot):
	@bot.command()
	async def invite(ctx, member: discord.Member):
		for room in bot.rooms:
			if room.state == RoomState.waiting and room.host.id == ctx.author.id and room.view.message.channel.id == ctx.channel.id:
				if member in room.participants:
					await ctx.send('Данный игрок уже находится в комнате.')
				elif member.id in getattr(room, 'declined', []):
					await ctx.send('Данный игрок отказался от приглашения в комнату.')
				else:
					await ctx.send(f'{ctx.author.global_name} приглашает игрока {member.mention} в игру {room.game.emoji} {room.game.name}.', view=InviteMember(room, member))
				return
		await ctx.send('Вы не являетесь ведущим ни в одной из комнат в данном канале.')

async def start(room):
	if not getattr(room, 'settings', None):
		room.settings = {}
	for view in room.settings.get('views', []):
		view.stop()
	if room.view.message.channel.id in mafia:
		await room.view.active_interaction.followup.send('В данном канале уже запущена игра. Дождитесь её окончания или запустите игру в другом канале.')
		room.manager.delete(room)
	elif len(room.participants) < (5 if len(room.settings.get('roles', [])) == 5 else 4):
		await room.view.active_interaction.followup.send('Недостаточно игроков для начала игры.')
		room.manager.delete(room)
	else:
		channel = room.view.message.channel
		mafia[channel.id] = {
			'room': room,
			'roles': {},
			'votes': {},
			'time': 'night',
			'players': [user.id for user in room.participants],
			'early_vote': False,
			'mafia_killed': None,
			'maniac_killed': None,
			'doctor_healed': None,
			'comissar': {
				'checked': False,
				'users': []
			},
			'putana': {
				'guest': None,
				'last_guest': None
			}
		}
		if not room.settings:
			room.settings = {
				'roles': ['mafia'],
				'roles_name': 'standard',
				'roles_time': 120,
				'putana_time': 60,
				'natural_death': 'yes',
				'draw_lots': 'yes'
			}
		mafia[channel.id]['id'] = randint(1, 1000)
		if mafia[channel.id]['id'] == last_id.get(channel.id):
			mafia[channel.id]['id'] = randint(1, 1000)
		last_id[channel.id] = mafia[channel.id]['id']
		for i in room.settings['roles']:
			player = choice(list(set(mafia[channel.id]['players']).difference(mafia[channel.id]['roles'])))
			mafia[channel.id]['roles'][player] = i
		await room.view.active_interaction.followup.send('Начинается игра, рассылаю список ролей.')
		for i in room.participants:
			try:
				if i.id in mafia[channel.id]['roles'] and room.settings['roles_name'] == 'standard':
					await i.send(f'Ваша роль — {roles[mafia[channel.id]["roles"][i.id]][4]} {roles[mafia[channel.id]["roles"][i.id]][0]}.')
				elif i.id in mafia[channel.id]['roles'] and room.settings['roles_name'] == 'russia':
					await i.send(f'Ваша роль — {values["roles_list"][mafia[channel.id]["roles"][i.id]][3]} {values["roles_list"][mafia[channel.id]["roles"][i.id]][1]}.')
				else:
					await i.send('Ваша роль — :peace: мирный житель.')
			except discord.errors.Forbidden:
				await channel.send(f'{i.mention}, бот не может отправлять вам сообщения в ЛС. Проверьте свои настройки конфиденциальности.')
		while mafia.get(channel.id):
			if mafia[channel.id]['time'] == 'night':
				views = {i: discord.ui.View() for i in mafia[channel.id]['roles'].values()}
				# путана
				if 'putana' in mafia[channel.id]['roles'].values() and get_putana(channel.id) in mafia[channel.id]['players']:
					if room.settings['roles_name'] == 'russia':
						await channel.send(f"Наступает ночь. Мирные жители засыпают. Просыпается Евгений Пригожин. У него {values['roles_time'][room.settings['putana_time']]} для приглашения для похода на Москву.")
					else:
						await channel.send(f"Наступает ночь. Мирные жители засыпают. Просыпается путана. У неё {values['roles_time'][room.settings['putana_time']]} для наведывания игроков.")
					await send_dm('putana', views['putana'], channel)
					await asyncio.sleep(room.settings['putana_time'])
					views['putana'].stop()
					del views['putana']
				else:
					if room.settings['roles_name'] == 'russia':
						await channel.send(f"Наступает ночь. Мирные жители засыпают. Просыпается Владимир Путин. У него {values['roles_time'][room.settings['roles_time']]} для принятия решений.")
					else:
						await channel.send(f"Наступает ночь. Мирные жители засыпают. Просыпается мафия. У неё {values['roles_time'][room.settings['roles_time']]} для принятия решений.")
				# мафия
				await send_dm('mafia', views['mafia'], channel)
				await asyncio.sleep(2)
				# маньяк
				await send_dm('maniac', views.get('maniac'), channel)
				await asyncio.sleep(2)
				# доктор
				await send_dm('doctor', views.get('doctor'), channel)
				await asyncio.sleep(2)
				# комиссар
				await send_dm('comissar', views.get('comissar'), channel)
				await asyncio.sleep(room.settings['roles_time']-6)
				for view in views.values():
					view.stop()
				mafia[channel.id]['time'] = 'day'
			elif mafia[channel.id]['time'] == 'day':
				await channel.send('На горизонте задребезжал рассвет. Мирные жители проснулись.')
				# мафия
				if mafia[channel.id]['mafia_killed']:
					if mafia[channel.id]['mafia_killed'] == mafia[channel.id]['doctor_healed']:
						await channel.send(f'На улице был найден <@{mafia[channel.id]["mafia_killed"]}>. Он был ранен, но при этом выжил.')
						# путана
						if mafia[channel.id]['roles'].get(mafia[channel.id]['mafia_killed']) == 'putana' and mafia[channel.id]['putana']['guest']:
							await channel.send(f"{'Вместе с этим' if 'maniac' in views else 'Также'} был найден <@{mafia[channel.id]['putana']['guest']}>. Он был ранен, но при этом выжил.")
					else:
						mafia[channel.id]['players'].remove(mafia[channel.id]['mafia_killed'])
						await channel.send(f'На улице было найдено тело <@{mafia[channel.id]["mafia_killed"]}>. Следы пуль говорили о многом.')
						# путана
						if mafia[channel.id]['roles'].get(mafia[channel.id]['mafia_killed']) == 'putana' and mafia[channel.id]['putana']['guest']:
							if mafia[channel.id]['putana']['guest'] == mafia[channel.id]['doctor_healed']:
								await channel.send(f"{'Вместе с этим' if 'maniac' in views else 'Также'} был найден <@{mafia[channel.id]['putana']['guest']}>. Он был ранен, но при этом выжил.")
							else:
								mafia[channel.id]['players'].remove(mafia[channel.id]['putana']['guest'])
								await channel.send(f"{'Вместе с этим' if 'maniac' in views else 'Также'} было найдено тело <@{mafia[channel.id]['putana']['guest']}>. Следы пуль говорили о многом.")
				elif room.settings['natural_death'] == 'yes':
					mafia[channel.id]['mafia_killed'] = choice(list(set(mafia[channel.id]['players']).difference([get_mafia(channel.id)])))
					if mafia[channel.id]['mafia_killed'] == mafia[channel.id]['doctor_healed']:
						sentence = choice(sentences)
						if sentence not in (
							'Ночью по естественным причинам {healed}умер <@{}>',
							'Ночью домой к участнику <@{}> заглянул призрак, вследствие чего он {healed}умер от шока'
						): sentence += ', но при этом выжил'
						await channel.send(f"Кажется, этой ночью мафия не смогла договориться и решила оставить мирных жителей в покое. Однако этот мир жесток. {sentence.format(mafia[channel.id]['mafia_killed'], healed='чуть не ')}.")
						# путана
						if mafia[channel.id]['roles'].get(mafia[channel.id]['mafia_killed']) == 'putana' and mafia[channel.id]['putana']['guest']:
							await channel.send(f"Такая же судьба постигла и <@{mafia[channel.id]['putana']['guest']}>, но при этом он выжил.")
					else:
						mafia[channel.id]['players'].remove(mafia[channel.id]['mafia_killed'])
						await channel.send(f"Кажется, этой ночью мафия не смогла договориться и решила оставить мирных жителей в покое. Однако этот мир жесток. {choice(sentences).format(mafia[channel.id]['mafia_killed'], healed='')}.")
						# путана
						if mafia[channel.id]['roles'].get(mafia[channel.id]['mafia_killed']) == 'putana' and mafia[channel.id]['putana']['guest']:
							if mafia[channel.id]['putana']['guest'] == mafia[channel.id]['doctor_healed']:
								await channel.send(f"Такая же судьба постигла и <@{mafia[channel.id]['putana']['guest']}>, но при этом он выжил.")
							else:
								mafia[channel.id]['players'].remove(mafia[channel.id]['putana']['guest'])
								if mafia[channel.id]['roles'].get(mafia[channel.id]['putana']['guest']) == 'mafia':
									await channel.send(f"Такая же судьба постигла и <@{mafia[channel.id]['putana']['guest']}>, который оказался **мафией**.")
								else:
									await channel.send(f"Такая же судьба постигла и <@{mafia[channel.id]['putana']['guest']}>.")
				else:
					if room.settings['roles_name'] == 'russia':
						await channel.send('Кажется, этой ночью мафия не смогла договориться и решила оставить мирных жителей в покое. Однако этот мир жесток. Ночью жители слышали какие-то хлопки, но потерь нет.')
					else:
						await channel.send('Кажется, этой ночью мафия не смогла договориться и решила оставить мирных жителей в покое. Однако этот мир жесток. Ночью жители слышали какие-то потрясения, но никто не пострадал.')
				# маньяк
				if mafia[channel.id]['maniac_killed']:
					if mafia[channel.id]['maniac_killed'] == mafia[channel.id]['doctor_healed']:
						await channel.send(f'Также был найден <@{mafia[channel.id]["maniac_killed"]}>. Он был ранен, но при этом выжил.')
						# путана
						if mafia[channel.id]['roles'].get(mafia[channel.id]['maniac_killed']) == 'putana' and mafia[channel.id]['putana']['guest']:
							await channel.send(f"И также был найден <@{mafia[channel.id]['putana']['guest']}>. Он был ранен, но при этом выжил.")
					elif mafia[channel.id]['roles'].get(mafia[channel.id]['maniac_killed']) == 'mafia':
						mafia[channel.id]['players'].remove(mafia[channel.id]['maniac_killed'])
						await channel.send(f'Также было найдено тело <@{mafia[channel.id]["maniac_killed"]}>, который оказался **мафией**. Следы пуль говорили о многом.')
						break
					else:
						mafia[channel.id]['players'].remove(mafia[channel.id]['maniac_killed'])
						await channel.send(f'Также было найдено тело <@{mafia[channel.id]["maniac_killed"]}>. Следы пуль говорили о многом.')
						# путана
						if mafia[channel.id]['roles'].get(mafia[channel.id]['maniac_killed']) == 'putana' and mafia[channel.id]['putana']['guest']:
							if mafia[channel.id]['putana']['guest'] == mafia[channel.id]['doctor_healed']:
								await channel.send(f"И также был найден <@{mafia[channel.id]['putana']['guest']}>. Он был ранен, но при этом выжил.")
							else:
								mafia[channel.id]['players'].remove(mafia[channel.id]['putana']['guest'])
								if mafia[channel.id]['roles'].get(mafia[channel.id]['putana']['guest']) == 'mafia':
									await channel.send(f'Также было найдено тело <@{mafia[channel.id]["maniac_killed"]}>, который оказался **мафией**. Следы пуль говорили о многом.')
								else:
									await channel.send(f"И также было найдено тело <@{mafia[channel.id]['putana']['guest']}>. Следы пуль говорили о многом.")
				# мафия убита?
				if get_mafia(channel.id) not in mafia[channel.id]['players']:
					await channel.send('С утра местный шериф, попивая кофе у себя дома, радостно улыбнётся, прочитав заголовок о полном провале мафии в этом городе. На этот раз игра для ееё закончена. Но конец ли это в общем?')
					room.manager.delete(room)
					del mafia[channel.id]
					break
				# можно кидать жребий и все мирные жители убиты
				elif all((
					room.settings['draw_lots'] == 'yes', len(mafia[channel.id]['players']) == 1,
					mafia[channel.id]['roles'].get(mafia[channel.id]['players'][0]) == 'mafia'
				# нельзя кидать жребий и выживший житель один на один с мафией
				)) or all((
					room.settings['draw_lots'] == 'no', len(mafia[channel.id]['players']) == 2,
					get_mafia(channel.id) in mafia[channel.id]['players']
				)):
					await channel.send('Сколько бы мирные жители не старались бороться с мафией, у них это не вышло. Невозможно представить, какой ужас испытали последние выжившие, встретившись один на один с мафией. К сожалению, их игра закончена.')
					await channel.send(f'Выжившая мафия: <@{mafia[channel.id]["players"][0]}>')
					room.manager.delete(room)
					del mafia[channel.id]
					break
				mafia[channel.id]['votes'] = {}
				mafia[channel.id]['mafia_killed'] = None
				mafia[channel.id]['maniac_killed'] = None
				mafia[channel.id]['doctor_healed'] = None
				mafia[channel.id]['putana']['last_guest'] = mafia[channel.id]['putana']['guest']
				mafia[channel.id]['putana']['guest'] = None
				mafia[channel.id]['comissar']['checked'] = False
				mafia[channel.id]['early_vote'] = False
				view = discord.ui.View()
				view.add_item(SelectPlayer(mafia[channel.id], voting))
				await channel.send('Как бы то ни было, у жителей есть 2 минуты, чтобы найти преступников и убить их. Выберите игрока, за убийство которого хотите проголосовать:', view=view)
				mafia[channel.id]['time'] = 'vote'
				asyncio.get_event_loop().create_task(wait(view, channel.id))
			await asyncio.sleep(2)
