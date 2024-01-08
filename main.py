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
    "tiktok": r"https?://(?:www.|vm.|vt.)?tiktok.com/.+(?: )?",
    "reddit": r"https?://(?:(?:old.|www.)?reddit.com|v.redd.it)/.+(?: )?",
    "instagram": r"https?:\/\/(?:www\.)?instagram\.com\/[a-zA-Z0-9_]+\/?(?:\?igshid=[a-zA-Z0-9_]+)?",
    "youtube": r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?",
    "urlRegex": r"(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z]{2,}(\.[a-zA-Z]{2,})(\.[a-zA-Z]{2,})?\/[a-zA-Z0-9]{2,}|((https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z]{2,}(\.[a-zA-Z]{2,})(\.[a-zA-Z]{2,})?)|(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z0-9]{2,}\.[a-zA-Z0-9]{2,}\.[a-zA-Z0-9]{2,}(\.[a-zA-Z0-9]{2,})?"

}
# Part of !pdf deprecated for now:w
 
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
    # block embeds just for people who don't want it 
    if content.startswith('!!'):
        print(f"Did no embed on {content}")
        return
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
        case "instagram":
            # cheeky little cheat to get yt-dlp to download from ddinstagram which will return the same link as instagram without using auth
            output = subprocess.run(["yt-dlp", "-g", "-f", "best", "--cookies", "cookies.txt", content], capture_output=True)
            if "cdninstagram" in output.stdout.decode('utf-8'):
                await message.reply(mention_author=False, content=('||' + "[video]("+output.stdout.decode()+")" + '||' if should_be_spoiled else "[video]("+output.stdout.decode()+")"))
    # For the cases where it needs to go link -> bytes -> file -> discord
    if should_download:
        # output contains the subprocess return, while outpath contains the data, idk why its called outpath
        # this includes if it should be spoilered
        output, outPath = download_video_file(content, should_be_spoiled)
        # if there is an error, we will retry it and pray this will work, if not log it
        if output.returncode != 0:
            output, outPath = download_video_file(content, should_be_spoilered)
            if output.returncode == 0:
                await message.reply(mention_author=False, file=discord.File(file, outPath))
                return
            with open('./lastError.log', 'w') as file:
                file.write(f'{output.stdout.decode()}, "\n", {output.stderr.decode() if output.stderr else ""}')
            await client.get_channel(1128015869117747280).send(embed=discord.Embed(title="ffmpreg", description=f"{message.author.mention} sent a {is_valid} link. There was an error, it was {output.stdout.decode('utf-8')}", color=0xff0000))
            return
        with open(outPath, 'rb') as file:
            await message.reply(mention_author=False, file=discord.File(file, outPath))
        os.remove(outPath)
    await client.get_channel(1128015869117747280).send(embed=discord.Embed(title="ffmpreg", description=f"{message.author.mention} sent a {is_valid} link\n\n{output.stdout.decode('utf-8') if output else '.'}\nReturn code: {output.returncode}", color=0x00ff00))

def download_video_file(content, should_be_spoiled=False):
    outPath = 'output.mp4' if not should_be_spoiled else 'SPOILER_output.mp4'
    # if the file exists of the last mp4, remove it to avoid run-ins
    if(os.path.isfile(outPath)):
        os.remove(outPath)            
    output = subprocess.run(["yt-dlp",                                   
                        "-f", "bestvideo[filesize<6MB]+bestaudio[filesize<2MB]/best/bestvideo+bestaudio",
                        "-S", "vcodec:h264",
                        "--merge-output-format", "mp4",
                        "--ignore-config",
                        "--verbose",
                        "--cookies", "cookies.txt" if "instagram" in content else ""
                        "--no-playlist",
                        "--no-warnings", '-o', outPath, content,
                        ], capture_output=True)
    print(output)
    return output,outPath

def should_be_spoilered(content):
    # if it is a url surrounded by ||
    pattern = r"\|\|([^|]+)\|\||http[s]?:[^\}\{\|\\\^\~\[\]\`]+"
    should_be_spoiled = False
    matches = re.search(pattern, content)
    if matches is not None:
        if matches.group(0) is not None and matches.group(0).startswith("||"):
            should_be_spoiled = True
    return should_be_spoiled

            

client.run(os.environ.get("BOT_TOKEN"))
