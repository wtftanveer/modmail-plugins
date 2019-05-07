import discord
import asyncio
from discord.ext import commands
from discord import NotFound, HTTPException, User

from googletrans import Translator

class TranslatePlugin:
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.translator = Translator()
        self.tt = set()
        self.enabled = True
        asyncio.create_task(self._set_config())
    
    async def _set_config(self):
        config = await self.db.find_one({'_id': 'config'})
        self.enabled = config.get('at-enabled', True)
        self.tt = set(config.get('auto-translate', []))

    @commands.command()
    async def translate(self,ctx,msgid: int):
        """Translate A Sent Message, or a modmail thread message into English."""
        try:
            msg = await ctx.channel.get_message(msgid)
            if not msg.embeds:
                ms = msg.content
            else:
                ms = msg.embeds[0].description
            
            embed = msg.embeds[0]
            tmsg = self.translator.translate(ms)
            embed = discord.Embed()
            embed.color = 4388013
            embed.description = tmsg.text
            await ctx.channel.send(embed=embed)
        except NotFound:
            await ctx.send("The Given Message Was Not Found.")
        except HTTPException:
            await ctx.send("The Try To Retrieve The Message Failed.")

    @commands.command(aliases=["tt"])
    async def translatetext(self,ctx,*,message):
        """Translates Given Message Into English"""
        tmsg = self.translator.translate(message)
        embed = discord.Embed()
        embed.color = 4388013
        embed.description = tmsg.text
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["att"])
    @commands.has_permissions(manage_messages=True)
    async def auto_translate_thread(self,ctx):
        if "User ID:" not in ctx.channel.topic:
            await ctx.send("The Channel Is Not A Modmail Thread")
            return
        if ctx.channel.id in self.tt:
            self.tt.remove(ctx.channel.id)
            removed = True
        else:
            self.tt.add(ctx.channel.id)
            removed = False
        
        await self.db.update_one(
            {'_id': 'config'},
            {'$set': {'auto-translate': list(self.tt)}}, 
            upsert=True
            )

        await ctx.send(f"{'Removed' if removed else 'Added'} Channel {'from' if removed else 'to'} Auto Translations List.")
    
    @commands.command(aliases=["tat"])
    @commands.has_permissions(manage_guild=True)
    async def toggle_auto_translations(self,ctx, enabled: bool):
        self.enabled = enabled
        await self.coll.update_one(
            {'_id': 'config'},
            {'$set': {'at-enabled': self.enabled}}, 
            upsert=True
            )
        await ctx.send(f"{'Enabled' if enabled else 'Disabled'} Auto Translations")
    
    async def on_message(self,message):
        if not self.enabled:
            return
        
        channel = message.channel

        if channel.id not in self.tt:
            return
        
        if isinstance(message.author,User):
            return
        
        if "User ID:" not in channel.topic:
            return
        
        if not message.embeds:
            return
        
        msg = message.embeds[0].description
        tmsg = self.translator.translate(msg)       
        embed = discord.Embed()
        embed.description = tmsg.text
        embed.color = 4388013
        embed.footer = "Auto Translator Plugin"

        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(TranslatePlugin(bot))
