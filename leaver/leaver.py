import discord

from redbot.core import Config, checks, commands
from redbot.core.commands import Context
from typing import Any

Cog: Any = getattr(commands, "Cog", object)


class Leaver(Cog):
    """
    Creates a goodbye message when people leave
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9811198108111121, force_registration=True)
        default_guild = {
            "channel": ''
        }

        self.config.register_guild(**default_guild)

    @commands.group(aliases=['setleaver'])
    @checks.mod_or_permissions(administrator=True)
    async def leaverset(self, ctx):
        """Adjust leaver settings"""
        if ctx.invoked_subcommand is None:
            pass

    @leaverset.command()
    async def channel(self, ctx: Context):
        guild = ctx.guild
        await self.config.guild(guild).channel.set(ctx.channel.id)
        await ctx.send("Channel set to " + ctx.channel.name)

    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        channel = await self.config.guild(guild).channel()

        if channel != '':
            channel = guild.get_channel(channel)
            await channel.send(str(member) + "(*" + str(member.nick) + "*) has left the server!")
        else:
            pass
