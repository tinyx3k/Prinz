#####################################################
import discord
from discord.ext import commands, tasks
import random
import wikipedia
from saucenao_api import SauceNao
import requests
import json
import asyncio
import wolframalpha
#####################################################
payload={}
headers = {}
response = requests.request("GET", "https://api.covid19api.com/summary", headers=headers, data=payload)
covi = response.json()

class Infomation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        # Help
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_author(name='Announcement!')
        embed.add_field(name='I am still developing this bot!', value='There will be a website for this bot... So stay tuned!')
        await ctx.send(embed=embed)


    @commands.command()
    async def hi(self, ctx):
        # Say hi!
        await ctx.send(f'Hi! {ctx.author.mention}')

    @commands.command()
    async def ping(self, ctx):
        # Checks bot latency
        p = round(self.bot.latency * 1000)
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_author(name=f'Pong! {p}ms!')
        await ctx.send(embed=embed)

    @commands.command()
    async def admin(self, ctx):
        # Prints infomation about the admin
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_author(name="VnPower!")
        embed.add_field(name='Website: ', value="[Here](https://page.vnpower.repl.co/)")
        embed.add_field(name='GitHub: ', value="-")
        embed.add_field(name='Discord: ', value="-")
        await ctx.send(embed=embed)

    @commands.command()
    async def wikilan(self, ctx ,*, Pinput:str):
        # Changes Wikipedia language
        embed = discord.Embed(colour=discord.Colour.blurple())
        if Pinput.lower().strip() in wikipedia.languages():
            wikipedia.set_lang(Pinput)
            embed.set_author(name=f"Changed Wikipedia's language to {wikipedia.languages()[Pinput.lower()]}({Pinput.upper()})!")
            await ctx.send(embed=embed)
        else:
            embed.set_author(name=f'That language does not exist in Wikipedia!')
            await ctx.send(embed=embed)

    @commands.command(aliases=['wiki'])
    # Searches articles on Wikipedia
    async def wikisrc(self, ctx, *, Pinput:str):
        # Searches Wikipedia
        lis = []
        count = 1
        searchR = wikipedia.search(Pinput)
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_author(name=f"Search results of {Pinput} on Wikipedia:")
        for i in searchR:
            li = {}
            embed.add_field(name=f"{count}. ", value=i, inline=True)
            li['id'] = count
            li['name'] = i
            lis.append(li)
            count +=1
        await ctx.send(embed=embed)
        while True:
            def is_correct(m):
                return m.author == ctx.author

            embed = discord.Embed(colour=discord.Colour.blurple())
            try:
                pinput = await self.bot.wait_for('message', check=is_correct, timeout=30.0)
            except asyncio.TimeoutError:
                embed.set_author(name=f'Time out!')
                await ctx.send(embed=embed)
                break
            try:
                if 1 <= int(pinput.content) <= 10:
                    for i in lis:
                        if int(i['id']) == int(pinput.content):
                            name = i['name']
                            embed.set_author(name=f'Summary of {name}')
                            embed.add_field(name=name, value=wikipedia.summary(name, sentences=3))
                            await ctx.send(embed=embed)
                            return None
            except ValueError:
                if str(pinput.content).lower().strip() == 'cancel':
                    embed.set_author(name='Canceled!')
                    await ctx.send(embed=embed)
                    break
        await ctx.send(embed=embed)

    @commands.command()
    async def sauce(self, ctx, *, words):
        # Get an image source (Anime only)
        sauce = SauceNao('18007b616a0808aa80ae9e17e3a8d110e53b081c')
        results = sauce.from_url(words)  # or from_file()

        best = results[0]
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_author(name=best.author)
        embed.add_field(name="Similarity: ", value=f"{best.similarity}%")
        embed.add_field(name="Link: ", value=f"[{best.title}]({best.urls[0]})")
        embed.set_image(url=best.thumbnail)
        embed.set_footer(text="<:mag_right:> This is what I have found!")
        await ctx.send(embed=embed)

    @commands.command()
    async def covid(self, ctx, *, words):
        # Prints COVID-19 infomation in a country
        global covi
        newConfirmed = 0
        totalConfirmed= 0
        newDeaths = 0
        totalDeaths= 0
        newRecovered = 0
        totalRecovered= 0
        for i in covi['Countries']:
            if str(i['Country'].lower()) == str(words.lower()) or str(i['CountryCode'].lower()) == str(words.lower()):
                newConfirmed = i['NewConfirmed']
                totalConfirmed= i['TotalConfirmed']
                newDeaths = i['NewDeaths']
                totalDeaths= i['TotalDeaths']
                newRecovered = i['NewRecovered']
                totalRecovered= i['TotalRecovered']
                embed = discord.Embed(colour=discord.Colour.blurple())
                embed.set_author(name=f"Covid-19 stats in {i['Country']}({i['CountryCode']})!")
                embed.add_field(name="New comfirmed:", value=newConfirmed)
                embed.add_field(name="Total comfirmed:", value=totalConfirmed)
                embed.add_field(name="New deaths:", value=newDeaths)
                embed.add_field(name="Total deaths:", value=totalDeaths)
                embed.add_field(name="New recovered:", value=newRecovered)
                embed.add_field(name="Total recovered:", value=totalRecovered)
                await ctx.send(embed=embed)
                break

    @commands.command(aliases=[])
    async def countries(self, ctx):
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_author(name="Country names and country codes(ISO Alpha-2)")
        embed.add_field(name=".", value='var.countries')
        await ctx.send(embed=embed)

    @commands.command()
    # Test
    async def math(self, ctx, *, words):
        client = wolframalpha.Client('QPK7GG-8KK22QQTLJ')
        result = client.query(words)
        output = next(result.results).text
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_author(name=output)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Infomation(bot))