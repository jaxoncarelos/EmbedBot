import os
import discord
import json
import subprocess
import re
import yt_dlp


regex = {
    "twitter": r"https?://(?:www.)?twitter.com/.+/status(?:es)?/(\d+)(?:.+ )?",
    "tiktok": r"https?://(?:www.|vm.)?tiktok.com/.+(?: )?",
    "reddit": r"https?://(?:(?:old.|www.)?reddit.com|v.redd.it)/.+(?: )?",
    "instagram": r"https?:\/\/(?:www\.)?instagram\.com\/[a-zA-Z0-9_]+\/?(?:\?igshid=[a-zA-Z0-9_]+)?"
}

config = json.load(open('config.json'))

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
def is_valid_url(url):
    for i in regex:
        if re.match(regex[i], url):
            return i
    return False

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.invisible, activity=discord.Game(name="ffmpreg"))
    await client.user.edit(username="ffmpreg")
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    content = message.content
    should_be_spoiled = re.match(r"^\|{2}.*\|{2}$", content.lower()) is not None
    if should_be_spoiled:
        content = content[2:-2]
    if message.author == client.user:
        return
    is_valid = is_valid_url(content)
    if not is_valid:
        return    
    should_download = False
    match is_valid:
        case "twitter":
            output = subprocess.run(["yt-dlp", "-g", '-f', 'bestvideo[filesize<30MB]+bestaudio[filesize<10mb]/best/bestvideo+bestaudio', '--no-warnings', content], capture_output=True)
            print(output.stdout.decode('utf-8'))
            await message.reply(mention_author=False, content= '||' + output.stdout.decode('utf-8') + '||' if should_be_spoiled else output.stdout.decode('utf-8'))
        case "tiktok":
            should_download = True
        case "reddit":
            should_download = True
# LAGS TOO MUCH ON DISCORD RUNS TOO SLOW, MIGHT BE BETTER TO DOWNLOAD IT
        case "instagram":
            should_download = True
    if should_download:
        outPath = 'output.mp4' if not should_be_spoiled else 'SPOILER_output.mp4'
        if(os.path.isfile(outPath)):
            os.remove(outPath)            
        subprocess.run(["yt-dlp",                                   
                        "-f", "bestvideo[filesize<6MB]+bestaudio[filesize<2MB]/best/bestvideo+bestaudio",
                        "-S", "vcodec:h264",
                        "--merge-output-format", "mp4",
                        "--ignore-config",
                        "--no-playlist",
                        "--no-warnings", '-o', outPath, content])
        with open(outPath, 'rb') as file:
            await message.reply(mention_author=False, file=discord.File(file, outPath))
        os.remove(outPath)

            

client.run(config["BOT_TOKEN"])
