#####################################################
import discord
from discord.ext import commands, tasks
import json
import nekos
import asyncio
import re
import typing
import urllib

from discord.ext.commands.cooldowns import BucketType
from googletrans import Translator

from utils.requests import async_post_json, async_text
#####################################################

def decrypt(key, ciphertext):
	''' 
		params: char key - offset of A
				string ciphertext - encoded message to be read
		desc: decrypt message by reversing offset of each letter by key
	'''
	shift = ord(key.upper()) - 65
	plaintext = ""
	for c in ciphertext.upper():
		if ord(c) != ord(" "):
			nchar = chr(ord(c) - shift)
			if ord(nchar) < 65:
				nchar = chr(ord(nchar) + 26)
			elif ord(nchar) > 90:
				nchar = chr(ord(nchar) - 26)
			plaintext += nchar
		else:
			plaintext += " "
	return plaintext

async def get_prefix(bot, message):
	with open('data/prefixes.json', 'r') as f:
		prefixes = json.load(f)

	try:
		return prefixes[str(message.guild.id)]
	except KeyError:
		prefixes[str(message.guild.id)] = 'l!'

		with open('prefixes.json', 'w') as file:
			json.dump(prefixes, file, indent=4)
		return prefixes[str(message.guild.id)]

async def get_emoji(bot, ctx, emoji_name):
	with open('others/emoji_database.json', 'r') as f:
		emojis = json.load(f)
	print(emoji_name)
	try:
		return emojis[str(emoji_name)]
	except KeyError:
		await ctx.send("Not found!")
		return None

def encrypt(key, plaintext):
	''' 
		params: char key - offset of A
				string plaintext - message to be encoded
		desc: encrypt message by offsetting each letter by key
	'''
	shift = ord(key.upper()) - 65
	ciphertext = ""
	for c in plaintext.upper():
		if ord(c) != ord(" "):
			nchar = chr(ord(c) + shift)
			if ord(nchar) > 90:
				nchar = chr(ord(nchar) - 26)
			ciphertext += nchar
		else:
			ciphertext += " "
	return ciphertext

def to_emoji(c):
	base = 0x1f1e6
	return chr(base + c)

async def convert(self, ctx, argument):
	time_regex = re.compile(r"(\d{1,5}(?:[.,]?\d{1,5})?)([smhd])")
	time_dict = {"h":3600, "s":1, "m":60, "d":86400}
	matches = time_regex.findall(argument.lower())
	time = 0
	for v, k in matches:
		try:
			time += time_dict[k]*float(v)
		except KeyError:
			embed = discord.Embed(color = discord.Colour.blurple(),description=  "{} is an invalid time-key! h/m/s/d are valid!".format(k))
			await ctx.send(embed=embed)
	return time

class Utility(commands.Cog, description="Some tools", name="Utlilty"):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_content=True, help="Send a invite link")
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def invite(self, ctx):
		await ctx.author.send("Here is the link! Thanks for inviting!\nhttps://discord.com/api/oauth2/authorize?client_id=877182587725049897&permissions=139012336887&scope=bot")

	@commands.command(hidden=True)
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def ascii(self, ctx, *, words):
		await ctx.send(nekos.owoify(words))

	@commands.command(aliases=['owo'], help="Owoify a string! Nya~")
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def owoify(self, ctx, *, words):
		loop = asyncio.get_event_loop()
		r = await loop.run_in_executor(None, nekos.owoify, words)
		await ctx.send(r)

	@commands.command(help="Create a simple poll")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def poll(self, ctx, time:str = '30m', *, topic:str):
		embed = discord.Embed(title=f"{ctx.author} asks: {topic}", description=f":one: Yes\n:two: No", color = discord.Colour.blurple())

		time = await convert(self, ctx, time)
		h = round(time) // 3600
		s = round(time) % 3600
		m = s // 60
		s = s % 60

		embed.add_field(name="Duration: ", value=f"{h} hour{'s' if h > 1 else ''}, {m} minute{'s' if m > 1 else ''}, {s} second{'s' if s > 1 else ''}")
		embed.set_footer(text= f"Poll created at {ctx.message.created_at}", icon_url=ctx.author.display_avatar.url)
		msg = await ctx.send(embed=embed)
		try:
			await ctx.message.delete()
		except:
			pass
		await msg.add_reaction('1️⃣')
		await msg.add_reaction('2️⃣')

		await asyncio.sleep(time)

		newMSG = await ctx.fetch_message(msg.id)
		onechoice = await newMSG.reactions[0].users().flatten()
		secchoice = await newMSG.reactions[1].users().flatten()

		result = "Tie"
		if len(onechoice) > len(secchoice):
			result = 'Yes'
		elif len(secchoice) > len(onechoice):
			result = 'No'

		embed = discord.Embed(title=topic, description=f"Result: {result}", color = discord.Colour.blurple())
		await newMSG.edit(embed=embed)

	@commands.command(help="Create a quickpoll with multiple choices")
	@commands.cooldown(1, 2, commands.BucketType.user)
	@commands.guild_only()
	async def quickpoll(self, ctx, *questions_and_choices: str):
		"""Makes a poll quickly.
		The first argument is the question and the rest are the choices.
		"""

		if len(questions_and_choices) < 3:
			embed = discord.Embed(colour=discord.Colour.blurple(), description="Need at least 1 question with 2 choices.")
			return await ctx.send(embed=embed)
		elif len(questions_and_choices) > 21:
			embed = discord.Embed(colour=discord.Colour.blurple(), description="You can only have up to 20 choices.")
			return await ctx.send(embed=embed)

		perms = ctx.channel.permissions_for(ctx.me)
		if not (perms.read_message_history or perms.add_reactions):
			return await ctx.send('Need Read Message History and Add Reactions permissions.')

		question = questions_and_choices[0]
		choices = [(to_emoji(e), v) for e, v in enumerate(questions_and_choices[1:])]

		try:
			await ctx.message.delete()
		except:
			pass

		body = "\n".join(f"{key}: {c}" for key, c in choices)
		embed = discord.Embed(colour=discord.Colour.blurple(), title=f"{ctx.author} asks: {question}\n\n", description=body)
		embed.set_footer(text= f"Poll created at {ctx.message.created_at}", icon_url=ctx.author.avatar_url)
		poll = await ctx.send(embed=embed)
		for emoji, _ in choices:
			await poll.add_reaction(emoji)

	@commands.command(help="Decode, encode or break Ceasar cipher.", usage="l!rot {encode/decode/break} {key} \"{cipher_text}\"", aliases=['caesar'])
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def rot(self, ctx, *args:str):
		embed = discord.Embed(colour=discord.Colour.blurple())
		try:
		   type_ = args[0].strip().lower()
		   key = args[1].strip().lower()
		   ciphertext = args[2]
		except:
			await ctx.send(embed=discord.Embed(colour=discord.Colour.blurple(), description=f"You are executing this command incorrectly. Type `{await get_prefix(self.bot, ctx)}help rot` to know how to use this command!"))
		if type_ == 'decode':
			plaintext = decrypt(key, ciphertext)
			embed.description = plaintext
			await ctx.send(embed=embed)
		elif type_ == 'encode':
			plaintext = encrypt(key, ciphertext)
			embed.description = plaintext
			await ctx.send(embed=embed)
		elif type_ == 'break':
			ciphertext = ciphertext.upper()
			if (key.upper()).find("Y") != -1:
				bruteforce = True
			else:
				bruteforce = False

			# check the frequency of each letter occurrence (A to Z)
			keys, text = [], []
			for l in list(map(chr, range(ord('A'), ord('[')))):
				freq = ciphertext.count(l) / float(len(ciphertext.replace(" ", "")))
				# if letter appears 10% or more it could be 'E'
				if freq >= .1 or bruteforce:
					# shift so decrypt key is A=
					key = chr(ord(l) - 4)
					if ord(key) < 65:
						key = chr(ord(key) + 26)
					elif ord(key) > 90:
						key = chr(ord(key) - 26)
					keys.append("Possible key: A=" + key)
					text.append(decrypt(key, ciphertext) + "\n")
			embed = discord.Embed(colour=discord.Colour.blurple())
			for a in range(len(keys)):
				embed.add_field(name=f"{keys[a]}", value=f"{text[a]}", inline=True)
			await ctx.send(embed=embed)

	@commands.cooldown(1, 3600, commands.BucketType.user)
	@commands.command(help="Sends a feedback to developers")
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def feedback(self, ctx, *, words:str):
		owner = self.bot.owner
		await owner.send(f"{ctx.author} sent a feedback: {words}")
		await ctx.send("Your feedback has been sent!")

	@commands.command(aliases=['elog'])
	@commands.cooldown(1, 2, commands.BucketType.user)
	@commands.is_owner()
	async def emoji_log(self, ctx, *words:str):
		with open('others/emoji_database.json', 'r') as f:
			emojis = json.load(f)
		a = words[0]
		b = words[1]
		emojis[str(a)] = b
		with open('others/emoji_database.json', 'w') as f:
			json.dump(emojis, f, indent=4)
		embed = discord.Embed(colour=discord.Colour.blurple(), description=f"Added!")
		await ctx.send(embed=embed)
		

	@commands.command(aliases=['edel'])
	@commands.cooldown(1, 2, commands.BucketType.user)
	@commands.is_owner()
	async def emoji_del(self, ctx, *, words:str):
		with open('others/emoji_database.json', 'r') as f:
			emojis = json.load(f)

		try:
			emojis.pop(words)
		except KeyError:
			await ctx.send(embed=discord.Embed(colour=discord.Colour.blurple(), description=f"That emoji does not exist!"))

		with open('others/emoji_database.json', 'w') as f:
			json.dump(emojis, f, indent=4)
		await ctx.send(embed=discord.Embed(colour=discord.Colour.blurple(), description=f"Deleted!"))

		

	@commands.command(aliases=['e'], help="Get an emoji from bot's emoji database")
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def emoji(self, ctx, *, emoji_name:str):
		r = await get_emoji(self.bot, ctx, emoji_name)
		try:
			await ctx.message.delete()
		except:
			pass
		if r is not None:
			await ctx.send(r)

	@commands.command(aliases=['elist'], help="Get an emoji from bot's emoji database")
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def emoji_list(self, ctx):
		with open('others/emoji_database.json', 'r') as f:
			emojis = json.load(f)

		names =list(emojis.keys())
		emojis_list = list(emojis.values())
		embed = discord.Embed(colour=discord.Colour.blurple(), title="Bot's emoji list")
		for index, name in enumerate(names):
			embed.add_field(name=f"{emojis_list[index]}", value=f"{name}", inline=True)

		await ctx.send(embed=embed)

	@commands.command(name="binary", help="Convert everything to binary.")
	@commands.cooldown(1, 2, commands.BucketType.user)
	async def _binary(self, ctx, *, words:str):
		Type = words.split(' ')[0]
		string = words.split(str(Type+' '))
		if Type.lower().strip() == 'decode':
			string = string[1]
			binary_values = string.split()
			ascii_string = ""
			for binary_value in binary_values:
				an_integer = int(binary_value, 2)
				ascii_character = chr(an_integer)
				ascii_string += ascii_character
				embed = discord.Embed(colour=discord.Colour.blurple())
				embed.set_author(name=f'Output: {ascii_string}')
				await ctx.send(embed=embed)
		elif Type.lower().strip() == 'encode':
			string = string[1]
			embed = discord.Embed(colour=discord.Colour.blurple())
			embed.set_author(name="Output: "+" ".join(f"{ord(i):08b}" for i in string))
			await ctx.send(embed=embed)
		else:
			embed = discord.Embed(colour=discord.Colour.blurple())
			embed.set_author(name=f'Please provide a type! (Ex: "decode" or "encode")')
			await ctx.send(embed=embed)

	@commands.command(pass_context=True, no_pm=True)
	async def ascii(self, ctx, *, text : str = None):
		"""Beautify some text (font list at http://artii.herokuapp.com/fonts_list)."""

		if text == None:
			await ctx.channel.send('Usage: `{}ascii [font (optional)] [text]`\n(font list at http://artii.herokuapp.com/fonts_list)'.format(ctx.prefix))
			return

		# Get list of fonts
		fonturl = "http://artii.herokuapp.com/fonts_list"
		response = await async_text(fonturl)
		fonts = response.split()

		font = None
		# Split text by space - and see if the first word is a font
		parts = text.split()
		if len(parts) > 1:
			# We have enough entries for a font
			if parts[0] in fonts:
				# We got a font!
				font = parts[0]
				text = ' '.join(parts[1:])
	
		url = "http://artii.herokuapp.com/make?{}".format(urllib.parse.urlencode({'text':text}))
		if font:
			url += '&font={}'.format(font)
		response = await async_text(url)
		await ctx.channel.send("```Markup\n{}```".format(response))

def setup(bot):
	bot.add_cog(Utility(bot))
