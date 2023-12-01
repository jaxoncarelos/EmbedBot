import os
from os.path import join, dirname
from dotenv import load_dotenv
from discord import Reaction, app_commands
import discord
import subprocess
import re
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

regex = {
    "twitter": r"https?://(?:www.)?twitter.com/.+/status(?:es)?/(\d+)(?:.+ )?",
    "x": r"https?://(?:www.)?x.com/.+/status(?:es)?/(\d+)(?:.+ )?",
    "tiktok": r"https?://(?:www.|vm.)?tiktok.com/.+(?: )?",
    "reddit": r"https?://(?:(?:old.|www.)?reddit.com|v.redd.it)/.+(?: )?",
    "instagram": r"https?:\/\/(?:www\.)?instagram\.com\/[a-zA-Z0-9_]+\/?(?:\?igshid=[a-zA-Z0-9_]+)?",
    "youtube": r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?",
    "urlRegex": r"(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z]{2,}(\.[a-zA-Z]{2,})(\.[a-zA-Z]{2,})?\/[a-zA-Z0-9]{2,}|((https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z]{2,}(\.[a-zA-Z]{2,})(\.[a-zA-Z]{2,})?)|(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z0-9]{2,}\.[a-zA-Z0-9]{2,}\.[a-zA-Z0-9]{2,}(\.[a-zA-Z0-9]{2,})?"

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



@tree.comand(name="retry", description="")
@tree.command(name = "pluh", description = "Plays plug sounds")
async def pluh(ctx):
    await ctx.response.send_message(file=discord.File("pluh!.mp3"))
@tree.command(name="yt", description="Download youtube video")
@app_commands.describe(link="Link to download")
async def ytdl(interaction: discord.Interaction, link: str):
    await deferAndWrong('youtube', interaction, link)

    output,outPath = download_video_file(link)
    if output.returncode != 0:
        return
    
    with open(outPath, 'rb') as file:
        await interaction.followup.send(file=discord.File(file,outPath))
    os.remove(outPath)

async def deferAndWrong(typeOf, interaction, link):
    await interaction.response.defer(thinking=False)
    if not is_valid_url(link) == typeOf:
        await interaction.followup.send("Invalid url.")
        return False
    return True

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.invisible, activity=discord.Game(name="ffmpreg"))
    await client.user.edit(username="ffmpreg")
    await tree.sync()
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message: discord.Message):

    content = message.content
    if message.author == client.user:
        return
    should_be_spoiled = should_be_spoilered(content)
            
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
        case "twitter" | "x":
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
        output, outPath = download_video_file(content, should_be_spoiled)
        if output.returncode != 0:
            await client.get_channel(1128015869117747280).send(embed=discord.Embed(title="ffmpreg", description=f"{message.author.mention} sent a {is_valid} link. There was an error, it was {output.stdout.decode('utf-8')}", color=0xff0000))
            return
        with open(outPath, 'rb') as file:
            await message.reply(mention_author=False, file=discord.File(file, outPath))
        os.remove(outPath)
    await client.get_channel(1128015869117747280).send(embed=discord.Embed(title="ffmpreg", description=f"{message.author.mention} sent a {is_valid} link\n\n{output.stdout.decode('utf-8')}\nReturn code: {output.returncode}", color=0x00ff00))

def download_video_file(content, should_be_spoiled=False):
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
    return output,outPath

def should_be_spoilered(content):
    pattern = r"\|\|([^|]+)\|\||http[s]?:[^\}\{\|\\\^\~\[\]\`]+"
    should_be_spoiled = False
    # regex where it checks if a url is surround with ||
    matches = re.search(pattern, content)
    if matches is not None:
        if matches.group(0) is not None and matches.group(0).startswith("||"):
            should_be_spoiled = True
    return should_be_spoiled

            

client.run(os.environ.get("BOT_TOKEN"))
