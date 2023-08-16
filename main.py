import os
from os.path import join, dirname
from dotenv import load_dotenv
from discord import Reaction, app_commands
import discord
import subprocess
import re
# import pdf2image
# import requests
# from PIL import Image

from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

regex = {
    "twitter": r"https?://(?:www.)?twitter.com/.+/status(?:es)?/(\d+)(?:.+ )?",
    "tiktok": r"https?://(?:www.|vm.)?tiktok.com/.+(?: )?",
    "reddit": r"https?://(?:(?:old.|www.)?reddit.com|v.redd.it)/.+(?: )?",
    "instagram": r"https?:\/\/(?:www\.)?instagram\.com\/[a-zA-Z0-9_]+\/?(?:\?igshid=[a-zA-Z0-9_]+)?",
}
# Part of !pdf deprecated for
urlRegex = r"(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z]{2,}(\.[a-zA-Z]{2,})(\.[a-zA-Z]{2,})?\/[a-zA-Z0-9]{2,}|((https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z]{2,}(\.[a-zA-Z]{2,})(\.[a-zA-Z]{2,})?)|(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z0-9]{2,}\.[a-zA-Z0-9]{2,}\.[a-zA-Z0-9]{2,}(\.[a-zA-Z0-9]{2,})?"

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True


client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
def is_valid_url(url):
    for i in regex:
        if re.match(regex[i], url):
            return i
    return False



@tree.command(name = "pluh", description = "Plays plug sounds")
async def pluh(ctx):
    await ctx.response.send_message(file=discord.File("pluh!.mp3"))

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.invisible, activity=discord.Game(name="ffmpreg"))
    await client.user.edit(username="ffmpreg")
    await tree.sync()
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):

    content: str = message.content
    if message.author == client.user:
        return
    # Not feasible IMO, unless theres less than like 5 pages, its just a huge spam
    # print(content)

    # if content.startswith("!pdf"):
    #     args = content.split(" ")
    #     if len(args) < 2:
    #         await message.reply(mention_author=False, content="Please provide a link")
    #         return
    #     if not re.match(urlRegex, args[1]):
    #         await message.reply(mention_author=False, content="Please provide a valid link")
    #         return
    #     file = requests.get(args[1])
    #     images = None

    #     if int(file.headers['Content-length']) > 8000000:
    #         await message.reply(mention_author=False, content="File too large")
    #         return
    #     images = pdf2image.convert_from_bytes(file.content)

    #     for i in range(len(images)):
    #         print(images[i].size)
    #         images[i].save(f"output{i}.png", "PNG")
            

    #     return


    # thanks ds
    should_be_spoiled = False
    
    pattern = r"\|\|([^|]+)\|\||http[s]?:[^\}\{\|\\\^\~\[\]\`]+"
    matches = re.search(pattern, content)
    if matches is not None:
        if matches.group(0) is not None and matches.group(0).startswith("||"):
            should_be_spoiled = True
            
    content = re.search("(http[s]?:[^\}\{\|\\\^\~\[\]\`]+)", content)
    if content is None:
        return
    content = content.group(0)

    is_valid = is_valid_url(content)

    if not is_valid:
        return    
    output = None
    should_download = False

    match is_valid:
        case "twitter":
            output = subprocess.run(["yt-dlp", "-g", '-f', 'bestvideo[filesize<30MB]+bestaudio[filesize<10mb]/best/bestvideo+bestaudio', "--cookies", "cookies.txt", content], capture_output=True)
            if output.stdout.decode('utf-8').startswith("https://video.twimg.com"):  
              await message.reply(mention_author=False, content= ('||' + output.stdout.decode('utf-8') + '||') if should_be_spoiled else output.stdout.decode('utf-8'))

        case "tiktok":
            should_download = True
        case "reddit":
            should_download = True
        # doesnt work very consistently
        # case "instagram":
        #     should_download = True
    if should_download:
        outPath = 'output.mp4' if not should_be_spoiled else 'SPOILER_output.mp4'
        if(os.path.isfile(outPath)):
            os.remove(outPath)            
        output = subprocess.run(["yt-dlp",                                   
                        "-f", "bestvideo[filesize<6MB]+bestaudio[filesize<2MB]/best/bestvideo+bestaudio",
                        "-S", "vcodec:h264",
                        "--merge-output-format", "mp4",
                        "--ignore-config",
                        "--no-playlist",
                        "--no-warnings", '-o', outPath, content,
                        ], capture_output=True)
        print(output)
        if output.returncode != 0:
            return
        with open(outPath, 'rb') as file:
            await message.reply(mention_author=False, file=discord.File(file, outPath))
        os.remove(outPath)
    await client.get_channel(1128015869117747280).send(embed=discord.Embed(title="ffmpreg", description=f"{message.author.mention} sent a {is_valid} link\n\n{output.stdout.decode('utf-8')}\nReturn code: {output.returncode}", color=0x00ff00))

            

client.run(os.environ.get("BOT_TOKEN"))
