from collections import defaultdict
from random import randint

import discord
from redbot.core import Config, checks, commands
from redbot.core.data_manager import cog_data_path
from typing import Any

Cog: Any = getattr(commands, "Cog", object)


class Hangman(Cog):
    """Lets anyone play a game of hangman with custom phrases"""
    navigate = "🔼🔽"
    letters = "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1049711010310997110)
        default_guild = {
            "theface": ':thinking:',
            "emojis": True,
        }

        self.config.register_guild(**default_guild)

        self.the_data = defaultdict(
            lambda: {"running": False, "hangman": 0, "guesses": [], "trackmessage": False, "answer": ''})
        self.path = str(cog_data_path(self)).replace('\\', '/')

        self.answer_path = self.path + "/bundled_data/hanganswers.txt"

        self.winbool = defaultdict(lambda: False)

        self.hanglist = {}

    async def _update_hanglist(self):
        for guild in self.bot.guilds:
            theface = await self.config.guild(guild).theface()
            self.hanglist[guild] = (
                """>
                   \_________
                    |/        
                    |              
                    |                
                    |                 
                    |               
                    |                   
                    |\___                 
                    """,

                """>
                   \_________
                    |/   |      
                    |              
                    |                
                    |                 
                    |               
                    |                   
                    |\___                 
                    H""",

                """>
                   \_________       
                    |/   |              
                    |   """ + theface + """
                    |                         
                    |                       
                    |                         
                    |                          
                    |\___                       
                    HA""",

                """>
                   \________               
                    |/   |                   
                    |   """ + theface + """                   
                    |    |                     
                    |    |                    
                    |                           
                    |                            
                    |\___                    
                    HAN""",

                """>
                   \_________             
                    |/   |               
                    |   """ + theface + """                    
                    |   /|                     
                    |     |                    
                    |                        
                    |                          
                    |\___                          
                    HANG""",

                """>
                   \_________              
                    |/   |                     
                    |   """ + theface + """                      
                    |   /|\                    
                    |     |                       
                    |                             
                    |                            
                    |\___                          
                    HANGM""",

                """>
                   \________                   
                    |/   |                         
                    |   """ + theface + """                       
                    |   /|\                             
                    |     |                          
                    |   /                            
                    |                                  
                    |\___                              
                    HANGMA""",

                """>
                   \________
                    |/   |     
                    |   """ + theface + """     
                    |   /|\           
                    |     |        
                    |   / \        
                    |               
                    |\___           
                    HANGMAN""")

    @commands.group(aliases=['sethang'], pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def hangset(self, ctx):
        """Adjust hangman settings"""
        if ctx.invoked_subcommand is None:
            pass

    @hangset.command(pass_context=True)
    async def face(self, ctx: commands.Context, theface):
        """Set the face of the hangman"""
        message = ctx.message
        # Borrowing FlapJack's emoji validation
        # (https://github.com/flapjax/FlapJack-Cogs/blob/master/smartreact/smartreact.py)
        if theface[:2] == "<:":
            theface = [r for r in self.bot.emojis if r.id == theface.split(':')[2][:-1]][0]

        try:
            # Use the face as reaction to see if it's valid (THANKS FLAPJACK <3)
            await message.add_reaction(theface)
        except discord.errors.HTTPException:
            await ctx.send("That's not an emoji I recognize.")
            return

        await self.config.guild(ctx.guild).theface.set(theface)
        await self._update_hanglist()
        await ctx.send("Face has been updated!")

    @hangset.command(pass_context=True)
    async def toggleemoji(self, ctx: commands.Context):
        """Toggles whether to automatically react with the alphabet"""

        current = await self.config.guild(ctx.guild).emojis()
        await self.config.guild(ctx.guild).emojis.set(not current)
        await ctx.send("Emoji Letter reactions have been set to {}".format(not current))

    @commands.command(aliases=['hang'], pass_context=True)
    async def hangman(self, ctx, guess: str = None):
        """Play a game of hangman against the bot!"""
        if guess is None:
            if self.the_data[ctx.guild]["running"]:
                await ctx.send("Game of hangman is already running!\nEnter your guess!")
                await self._printgame(ctx.channel)
                """await self.bot.send_cmd_help(ctx)"""
            else:
                await ctx.send("Starting a game of hangman!")
                self._startgame(ctx.guild)
                await self._printgame(ctx.channel)
        elif not self.the_data[ctx.guild]["running"]:
            await ctx.send("Game of hangman is not yet running!\nStarting a game of hangman!")
            self._startgame(ctx.guild)
            await self._printgame(ctx.channel)
        else:
            await ctx.send("Guess by reacting to the message")
            # await self._guessletter(guess, ctx.channel)

    def _startgame(self, guild):
        """Starts a new game of hangman"""
        self.the_data[guild]["answer"] = self._getphrase().upper()
        self.the_data[guild]["hangman"] = 0
        self.the_data[guild]["guesses"] = []
        self.winbool[guild] = False
        self.the_data[guild]["running"] = True
        self.the_data[guild]["trackmessage"] = False

    def _stopgame(self, guild):
        """Stops the game in current state"""
        self.the_data[guild]["running"] = False
        self.the_data[guild]["trackmessage"] = False

    async def _checkdone(self, channel):
        if self.winbool[channel.guild]:
            await channel.send("You Win!")
            self._stopgame(channel.guild)
        elif self.the_data[channel.guild]["hangman"] >= 7:
            await channel.send("You Lose!\nThe Answer was: **" + self.the_data[channel.guild]["answer"] + "**")

            self._stopgame(channel.guild)

    def _getphrase(self):
        """Get a new phrase for the game and returns it"""

        with open(self.answer_path, 'r') as phrasefile:
            phrases = phrasefile.readlines()

        outphrase = ""
        while outphrase == "":
            outphrase = phrases[randint(0, len(phrases) - 1)].partition(" (")[0]
        return outphrase

    def _hideanswer(self, guild):
        """Returns the obscured answer"""
        out_str = ""

        self.winbool[guild] = True
        for i in self.the_data[guild]["answer"]:
            if i == " " or i == "-":
                out_str += i * 2
            elif i in self.the_data[guild]["guesses"] or i not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                out_str += "__" + i + "__ "
            else:
                out_str += "**\_** "
                self.winbool[guild] = False

        return out_str

    def _guesslist(self, guild):
        """Returns the current letter list"""
        out_str = ""
        for i in self.the_data[guild]["guesses"]:
            out_str += str(i) + ","
        out_str = out_str[:-1]

        return out_str

    async def _guessletter(self, guess, message):
        """Checks the guess on a letter and prints game if acceptable guess"""
        channel = message.channel
        if guess.upper() not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" or len(guess) != 1:
            await channel.send("Invalid guess. Only A-Z is accepted")
            return

        if guess.upper() in self.the_data[channel.guild]["guesses"]:
            await channel.send("Already guessed that! Try again")
            return
        if guess.upper() not in self.the_data[channel.guild]["answer"]:
            self.the_data[channel.guild]["hangman"] += 1

        self.the_data[channel.guild]["guesses"].append(guess.upper())

        await self._reprintgame(message)

    async def on_react(self, reaction, user):
        """ Thanks to flapjack reactpoll for guidelines
            https://github.com/flapjax/FlapJack-Cogs/blob/master/reactpoll/reactpoll.py"""

        if reaction.message.id != self.the_data[user.guild]["trackmessage"]:
            return

        if user == self.bot.user:
            return  # Don't react to bot's own reactions
        message = reaction.message
        emoji = reaction.emoji

        if str(emoji) in self.letters:
            letter = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[self.letters.index(str(emoji))]
            await self._guessletter(letter, message)
            await message.remove_reaction(emoji, user)
            await message.remove_reaction(emoji, self.bot.user)

        if str(emoji) in self.navigate:
            if str(emoji) == self.navigate[0]:
                await self._reactmessage_am(message)

            if str(emoji) == self.navigate[-1]:
                await self._reactmessage_nz(message)

    async def _try_clear_reactions(self, message):
        try:
            await message.clear_reactions()
        except discord.Forbidden:
            pass

    async def _reactmessage_menu(self, message):
        """React with menu options"""
        if not await self.config.guild(message.guild).emojis():
            return

        await self._try_clear_reactions(message)

        await message.add_reaction(self.navigate[0])
        await message.add_reaction(self.navigate[-1])

    async def _reactmessage_am(self, message):
        if not await self.config.guild(message.guild).emojis():
            return

        await self._try_clear_reactions(message)

        for x in range(len(self.letters)):
            if x in [i for i, b in enumerate("ABCDEFGHIJKLM") if b not in self._guesslist(message.guild)]:
                await message.add_reaction(self.letters[x])

        await message.add_reaction(self.navigate[-1])

    async def _reactmessage_nz(self, message):
        if not await self.config.guild(message.guild).emojis():
            return

        await self._try_clear_reactions(message)

        for x in range(len(self.letters)):
            if x in [i for i, b in enumerate("NOPQRSTUVWXYZ") if b not in self._guesslist(message.guild)]:
                await message.add_reaction(self.letters[x + 13])

        await message.add_reaction(self.navigate[0])

    def _make_say(self, guild):
        c_say = "Guess this: " + str(self._hideanswer(guild)) + "\n"
        c_say += "Used Letters: " + str(self._guesslist(guild)) + "\n"
        c_say += self.hanglist[guild][self.the_data[guild]["hangman"]] + "\n"
        c_say += self.navigate[0] + " for A-M, " + self.navigate[-1] + " for N-Z"

        return c_say

    async def _reprintgame(self, message):
        if message.guild not in self.hanglist:
            await self._update_hanglist()

        c_say = self._make_say(message.guild)

        await message.edit(content=c_say)
        self.the_data[message.guild]["trackmessage"] = message.id

        await self._checkdone(message.channel)

    async def _printgame(self, channel):
        """Print the current state of game"""
        if channel.guild not in self.hanglist:
            await self._update_hanglist()

        c_say = self._make_say(channel.guild)

        message = await channel.send(c_say)

        self.the_data[channel.guild]["trackmessage"] = message.id

        await self._reactmessage_menu(message)
        await self._checkdone(channel)
