from discord import ui, ButtonStyle, SelectOption
from .game import roles, values, summarize, InviteMember, SelectNames, SelectRoles, SelectTimes
get_name = lambda user: user.global_name if user.global_name else user.name
roles_list = {
	'standard': lambda role: values['roles_list'][role][0].lower(),
	'russia': lambda role: values['roles_list'][role][1]
}

class OpenSettings(ui.Button):
	def __init__(self, room):
		super().__init__(
			label='Открыть настройки',
			style=ButtonStyle.grey,
			emoji='<:host:1009182501325000887>',
		)
		self.room = room

	async def callback(self, interaction):
		if interaction.user.id == self.room.host.id:
			if not getattr(self.room, 'settings', None):
				self.room.settings = {
					'roles': ['mafia'],
					'roles_name': 'standard',
					'roles_time': 120,
					'putana_time': 60,
					'natural_death': 'yes',
					'draw_lots': 'yes',
					'views': []
				}
			view = ui.View()
			view.add_item(SelectOptions(self.room))
			self.room.settings['views'].append(view)
			await interaction.response.send_message('Вы открыли настройки. Доступные опции:', view=view)
		else:
			await interaction.response.send_message('Только ведущий может настраивать игру', ephemeral=True)

class SelectYesNo(ui.Button):
	def __init__(self, room, mode=None):
		super().__init__(
			label=values['yes_no'][room.settings['draw_lots' if mode == 'draw_lots' else 'natural_death']].capitalize(), 
			style=ButtonStyle.green if room.settings['draw_lots' if mode == 'draw_lots' else 'natural_death'] == 'yes' else ButtonStyle.red
		)
		self.room = room
		self.mode = mode
		self.views = ui.View()
		self.views.add_item(self)

	async def callback(self, interaction):
		mode = 'draw_lots' if self.mode == 'draw_lots' else 'natural_death'
		if interaction.user.id == self.room.host.id and self.room.settings[mode] == 'yes':
			self.room.settings[mode] = 'no'
			self.button.label = 'Нет'
			self.button.style = ButtonStyle.red
			await interaction.response.edit_message(view=self)
		elif interaction.user.id == self.room.host.id and self.room.settings[mode] == 'no':
			self.room.settings[mode] = 'yes'
			self.button.label = 'Да'
			self.button.style = ButtonStyle.green
			await interaction.response.edit_message(view=self)
		else:
			await interaction.response.send_message('Только ведущий может настраивать игру', ephemeral=True)

class SelectOptions(ui.Select):
	def __init__(self, room):
		self.room = room
		options = (
			SelectOption(label='Названия ролей', description='Текущее значение: ' + values['roles_name'][room.settings['roles_name']], value='roles_name'),
			SelectOption(label='Список ролей', description='Текущее значение: ' + ', '.join(map(roles_list[room.settings['roles_name']], room.settings['roles'])), value='roles_list'),
			SelectOption(label='Время на раздумие ролям (кроме путаны)', description='Текущее значение: ' + values['roles_time'][room.settings['roles_time']], value='roles_time'),
			SelectOption(label='Время на раздумие путане', description='Текущее значение: ' + values['roles_time'][room.settings['putana_time']], value='putana_time'),
			SelectOption(label='Могут ли умирать игроки, если мафия никого не убила?', description='Текущее значение: ' + values['yes_no'][room.settings['natural_death']], value='natural_death'),
			SelectOption(label='Могут ли игроки вытянуть жребий, если не определились, кого убить?', description='Текущее значение: ' + values['yes_no'][room.settings['draw_lots']], value='draw_lots'),
		)
		super().__init__(placeholder='Выбрать опцию', options=options)

	async def callback(self, interaction):
		if interaction.user.id == self.room.host.id:
			if self.values[0] == 'roles_name':
				view = SelectNames(self.room)
				self.room.settings['views'].append(view)
				await interaction.response.send_message('Названия ролей:', view=view)
			elif self.values[0] == 'roles_list':
				view = SelectRoles(self.room)
				for button in view.children:
					if button.label in self.room.settings['roles']:
						button.style = ButtonStyle.green
					button.label = values['roles_list'][button.label][1 if self.room.settings['roles_name'] == 'russia' else 0]
				self.room.settings['views'].append(view)
				await interaction.response.send_message('Список ролей:', view=view)
			elif self.values[0] == 'roles_time':
				view = SelectTimes(self.room)
				self.room.settings['views'].append(view)
				await interaction.response.send_message('Время на раздумие ролям (кроме путаны):', view=view)
			elif self.values[0] == 'putana_time':
				view = SelectTimes(self.room, 'putana')
				self.room.settings['views'].append(view)
				await interaction.response.send_message('Время на раздумие путане:', view=view)
			elif self.values[0] == 'natural_death':
				button = SelectYesNo(self.room)
				self.room.settings['views'].append(button.views)
				await interaction.response.send_message('Могут ли умирать игроки, если мафия никого не убила?', view=button.views)
			elif self.values[0] == 'draw_lots':
				button = SelectYesNo(self.room, 'draw_lots')
				self.room.settings['views'].append(button.views)
				await interaction.response.send_message('Могут ли игроки вытянуть жребий, если не определились, кого убить?', view=button.views)
		else:
			await interaction.response.send_message('Только ведущий может настраивать игру', ephemeral=True)

class SelectPlayer(ui.Select):
	def __init__(self, mafia, role):
		options = []
		self.mafia = mafia
		if not isinstance(role, str):
			self.role = 'voting'
			self.delete = role
		else:
			self.role = role
		for i in mafia['room'].participants:
			if i.id in mafia['players']:
				if mafia['roles'].get(i.id) != ('' if self.role == 'doctor' else self.role): 
					options.append(SelectOption(label=get_name(i), value=i.id))
		if self.role == 'voting':
			options.append(SelectOption(label='Воздержаться', value='skip', emoji='<:host:1009182501325000887>'))
		super().__init__(placeholder='Выбрать игрока', options=options)

	async def callback(self, interaction):
		if self.role == 'voting':
			if interaction.user not in self.mafia['room'].participants:
				await interaction.response.send_message('Вы не можете проголосовать, ибо не участвуете в игре.', ephemeral=True)
			elif interaction.user.id not in self.mafia['players']:
				await interaction.response.send_message('Вы не можете проголосовать, ибо были убиты.', ephemeral=True)
			else:
				if self.values[0] == 'skip':
					self.mafia['votes'][interaction.user.id] = 'skip'
					await interaction.channel.send(f'{get_name(interaction.user)} воздержался от голосования.')
				else:
					self.mafia['votes'][interaction.user.id] = int(self.values[0])
					await interaction.channel.send(f'{get_name(interaction.user)} проголосовал за убийство <@{self.values[0]}>.')
				await interaction.response.defer()
				if set(self.mafia['players']) == set(self.mafia['votes']):
					channel_id = interaction.channel.id
					self.mafia['early_vote'] = True
					self.view.stop()
					await summarize(self.mafia)
					if self.mafia['time'] == 'end':
						self.delete(channel_id)
		elif self.role == 'mafia':
			if interaction.user.id == self.mafia['putana']['guest']:
				await interaction.response.send_message('Вы не можете убивать игроков, ибо вы в гостях у путаны.')
			elif int(self.values[0]) == self.mafia['maniac_killed']:
				await interaction.response.send_message('Данный игрок уже стал жертвой маньяка.')
			else:
				if int(self.values[0]) != self.mafia['putana']['guest']:
					self.mafia['mafia_killed'] = int(self.values[0])
				await interaction.response.send_message('Ваше решение принято.')
		elif self.role == 'maniac':
			if interaction.user.id == self.mafia['putana']['guest']:
				await interaction.response.send_message('Вы не можете убивать игроков, ибо вы в гостях у путаны.')
			elif int(self.values[0]) == self.mafia['mafia_killed']:
				await interaction.response.send_message('Данный игрок уже стал жертвой мафии.')
			else:
				if int(self.values[0]) != self.mafia['putana']['guest']:
					self.mafia['maniac_killed'] = int(self.values[0])
				await interaction.response.send_message('Ваше решение принято.')
		elif self.role == 'doctor':
			if interaction.user.id == self.mafia['putana']['guest']:
				await interaction.response.send_message('Вы не можете лечить игроков, ибо вы в гостях у путаны.')
			else:
				if self.mafia['roles'].get(int(self.values[0])) != 'mafia':
					self.mafia['doctor_healed'] = int(self.values[0])
				await interaction.response.send_message('Ваше решение принято.')
		elif self.role == 'comissar':
			if interaction.user.id == self.mafia['putana']['guest']:
				await interaction.response.send_message('Вы не можете проверять игроков, ибо вы в гостях у путаны.')
			elif self.mafia['comissar']['checked']:
				await interaction.response.send_message('Вы уже проверяли игроков этой ночью.')
			elif int(self.values[0]) in self.mafia['comissar']['users']:
				await interaction.response.send_message('Вы уже проверяли данного игрока.')
			else:
				self.mafia['comissar']['checked'] = True
				self.mafia['comissar']['users'].append(int(self.values[0]))
				user = self.mafia['room'].host.guild.get_member(int(self.values[0]))
				if int(self.values[0]) in self.mafia['roles']:
					role = self.mafia['roles'][int(self.values[0])]
					await interaction.response.send_message(f"{get_name(user)} является {values['roles_list'][role][2] if self.mafia['room'].settings['roles_name'] == 'russia' else roles[role][1]}.")
				else:
					await interaction.response.send_message(f'{get_name(user)} является мирным жителем.')
		elif self.role == 'putana':
			if int(self.values[0]) == self.mafia['putana']['last_guest']:
				await interaction.response.send_message('Вы уже наведывались к данному игроку прошлой ночью.')
			else:
				self.mafia['putana']['guest'] = int(self.values[0])
				await interaction.response.send_message('Ваше решение принято.')
