import discord
from random import choice
from collections import Counter
from discord import ButtonStyle
from bot.core.invite import RoomState
roles = {
	'mafia': ('мафия', 'мафией', 'принятия решений', 'убить', ':spy:'),
	'comissar': ('комиссар', 'комиссаром', 'проверки игроков', 'проверить', ':man_police_officer:'),
	'doctor': ('доктор', 'доктором', 'лечения игроков', 'вылечить', ':health_worker:'),
	'maniac': ('маньяк', 'маньяком', 'принятия решений', 'убить', ':ninja:'),
	'putana': ('путана', 'путаной', 'наведывания игроков', 'наведать', ':blond_haired_woman:')
}
values = {
	'roles_name': {'standard': 'Стандартные', 'russia': 'Однажды в России'},
	'roles_list': {
		'peaceful': ('Мирные жители', 'Народы России'),
		'mafia': ('Мафия', 'Владимир Путин', 'Владимиром Путиным', '<:putin:1129733781910212608>'),
		'comissar': ('Комиссар', 'Кирилл Буданов', 'Кириллом Будановым', '<:budanov:1129733793553580054>'),
		'doctor': ('Доктор', 'Джо Байден', 'Джо Байденом', '<:biden:1129733797341036564>'),
		'maniac': ('Маньяк', 'Александр Лукашенко', 'Александром Лукашенко', '<:lukashenko:1129733788478480524>'),
		'putana': ('Путана', 'Евгений Пригожин', 'Евгением Пригожиным', '<:prigozhin:1126163030732976188>')
	},
	'roles_time': {
		60: '1 минута',
		120: '2 минуты',
		180: '3 минуты',
		240: '4 минуты',
		300: '5 минут'
	},
	'yes_no': {'yes': 'да', 'no': 'нет'}
}
sentences = (
	'Ночью по естественным причинам {healed}умер <@{}>',
	'Ночью <@{}> решил запить молоком солёные огурцы',
	'Ночью заглянул на тусу к русалкам <@{}>',
	'Ночью участником <@{}> был выпит протухший дедовский самогон',
	'Ночью <@{}> стал жертвой нападения одичавших попугаев',
	'Ночью домой к участнику <@{}> заглянул призрак, вследствие чего он {healed}умер от шока'
)

async def summarize(mafia):
	channel = mafia['room'].view.message.channel
	kill_vote = None
	if not mafia['votes']:
		await channel.send('Видимо, мирным жителям неинтересна инициатива голосования и выживания.')
	else:
		votes_num = Counter(mafia['votes'].values())
		kill_list = [k for k,v in votes_num.items() if k != 'skip' and v == max(votes_num.values())]
		if not kill_list:
			await channel.send('Видимо, мирным жителям неинтересна инициатива голосования и выживания.')
		elif len(kill_list) > 1:
			if mafia['room'].settings['draw_lots'] == 'yes':
				kill_vote = choice(kill_list)
				await channel.send(f'Мирные жители разошлись в мнении между <@{">, <@".join(map(str, kill_list))}>. Было принято решение вытянуть жребий.')
				await channel.send(f'Короткий жребий достался <@{kill_vote}>. Увы, но для него это конец.')
			else:
				await channel.send(f'Мирные жители разошлись в мнении между <@{">, <@".join(map(str, kill_list))}>. Было принято решение отложить голосование до следующего дня.')
		else:
			kill_vote = kill_list[0]
	if kill_vote in mafia['roles']:
		if kill_vote == mafia['putana']['last_guest']:
			await channel.send(f'Жители приняли решение убить <@{kill_vote}>. Однако приговор не был вынесен, ибо он был у путаны прошлой ночью.')
		else:
			mafia['players'].remove(kill_vote)
			await channel.send(f"Жители приняли решение убить <@{kill_vote}>. После вынесения приговора и убийства выяснилось, что он был **{values['roles_list'][mafia['roles'][kill_vote]][2] if mafia['room'].settings['roles_name'] == 'russia' else roles[mafia['roles'][kill_vote]][1]}**.")
			if mafia['roles'][kill_vote] == 'mafia': 
				await channel.send('С утра местный шериф, попивая кофе у себя дома, радостно улыбнётся, прочитав заголовок о полном провале мафии в этом городе. На этот раз игра для неё закончена. Но конец ли это в общем?')
				mafia['room'].manager.delete(mafia['room'])
				mafia['time'] = 'end'
				return
	elif kill_vote:
		if kill_vote == mafia['putana']['last_guest']:
			await channel.send(f'Жители приняли решение убить <@{kill_vote}>. Однако приговор не был вынесен, ибо он был у путаны прошлой ночью.')
		else:
			mafia['players'].remove(kill_vote)
			await channel.send(f'Жители приняли решение убить <@{kill_vote}>. После вынесения приговора и убийства выяснилось, что он был **мирным жителем**.')
	if any((
		# можно кидать жребий и все мирные жители убиты
		mafia['room'].settings['draw_lots'] == 'yes' and len(mafia['players']) == 1 and mafia['roles'].get(mafia['players'][0]) == 'mafia',
		# нельзя кидать жребий и выживший житель один на один с мафией
		mafia['room'].settings['draw_lots'] == 'no' and len(mafia['players']) == 2 and {v:k for k,v in mafia['roles'].items()}.get('mafia') in mafia['players']
	)):
		await channel.send('Сколько бы мирные жители не старались бороться с мафией, у них это не вышло. Невозможно представить, какой ужас испытали последние выжившие, встретившись один на один с мафией. К сожалению, их игра закончена.')
		await channel.send(f'Выжившая мафия: <@{mafia["players"][0]}>')
		mafia['room'].manager.delete(mafia['room'])
		mafia['time'] = 'end'
		return
	else:
		mafia['time'] = 'night'

class SelectNames(discord.ui.View):
	def __init__(self, room):
		super().__init__()
		self.room = room
	
	@discord.ui.button(label='Стандартные', style=ButtonStyle.green)
	async def select_names(self, interaction, button):
		if interaction.user.id == self.room.host.id and self.room.settings['roles_name'] == 'standard':
			self.room.settings['roles_name'] = 'russia'
			button.label = 'Однажды в России'
			button.style = ButtonStyle.blurple
			await interaction.response.edit_message(view=self)
		elif interaction.user.id == self.room.host.id and self.room.settings['roles_name'] == 'russia':
			self.room.settings['roles_name'] = 'standard'
			button.label = 'Стандартные'
			button.style = ButtonStyle.green
			await interaction.response.edit_message(view=self)
		else:
			await interaction.response.send_message('Только ведущий может настраивать игру', ephemeral=True)

class SelectRoles(discord.ui.View):
	def __init__(self, room):
		super().__init__()
		self.room = room
	
	async def select_roles(self, role, interaction, button):
		roles = self.room.settings['roles']
		if interaction.user.id == self.room.host.id and role not in roles:
			roles.append(role)
			button.style = ButtonStyle.green
			await interaction.response.edit_message(view=self)
		elif interaction.user.id == self.room.host.id and role in roles:
			roles.remove(role)
			button.style = ButtonStyle.blurple
			await interaction.response.edit_message(view=self)
		else:
			await interaction.response.send_message('Только ведущий может настраивать игру', ephemeral=True)
	
	@discord.ui.button(label='peaceful', style=ButtonStyle.green, disabled=True)
	async def peaceful():
		pass
	
	@discord.ui.button(label='mafia', style=ButtonStyle.green, disabled=True)
	async def mafia():
		pass
	
	@discord.ui.button(label='comissar', style=ButtonStyle.blurple)
	async def comissar(self, interaction, button):
		await self.select_roles('comissar', interaction, button)
	
	@discord.ui.button(label='doctor', style=ButtonStyle.blurple, row=1)
	async def doctor(self, interaction, button):
		await self.select_roles('doctor', interaction, button)
	
	@discord.ui.button(label='maniac', style=ButtonStyle.blurple, row=1)
	async def maniac(self, interaction, button):
		await self.select_roles('maniac', interaction, button)
	
	@discord.ui.button(label='putana', style=ButtonStyle.blurple, row=1)
	async def putana(self, interaction, button):
		await self.select_roles('putana', interaction, button)

class SelectTimes(discord.ui.View):
	def __init__(self, room, mode=None):
		super().__init__()
		self.room = room
		self.mode = mode
		self.button = discord.ui.Button(
			label=values['roles_time'][room.settings['putana_time' if mode == 'putana' else 'roles_time']],
			style=ButtonStyle.blurple, disabled=True
		)
		self.add_item(self.button)

	@discord.ui.select(placeholder='Выбрать время', options=(
		discord.SelectOption(label='1 минута', value='60'),
		discord.SelectOption(label='2 минуты', value='120'),
		discord.SelectOption(label='3 минуты', value='180'),
		discord.SelectOption(label='4 минуты', value='240'),
		discord.SelectOption(label='5 минут', value='300')
	), row=1)
	async def select_times(self, interaction, select):
		if interaction.user.id == self.room.host.id:
			self.room.settings['putana_time' if self.mode == 'putana' else 'roles_time'] = int(select.values[0])
			self.button.label = values['roles_time'][int(select.values[0])]
			await interaction.response.edit_message(view=self)
		else:
			await interaction.response.send_message('Только ведущий может настраивать игру', ephemeral=True)
