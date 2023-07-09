import os
import discord
import json
import subprocess
import re

regex = {
    "twitter": r"https?://(?:www.)?twitter.com/.+/status(?:es)?/(\d+)(?:.+ )?",
    "tiktok": r"https?://(?:www.|vm.)?tiktok.com/.+(?: )?",
    "reddit": r"https?://(?:(?:old.|www.)?reddit.com|v.redd.it)/.+(?: )?"
}

config = json.load(open('config.json'))
for i in config:
    print(i)
    print(config[i])

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
    if message.author == client.user:
        return
    is_valid = is_valid_url(content)
    if not is_valid:
        return    
    should_download = False
    match is_valid:
        case "twitter":
            output = subprocess.run(["yt-dlp", "-g", '-f', 'best[filesize<30MB]', '--no-warnings', content], capture_output=True)
            await message.reply(output.stdout.decode('utf-8'))
        case "tiktok":
            should_download = True
        case "reddit":
            should_download = True
    if should_download:
        if(os.path.isfile('output.mp4')):
            os.remove('output.mp4')            
        subprocess.run(["yt-dlp",                                   
                        "-f", "bestvideo[filesize<6MB]+bestaudio[filesize<2MB]/best/bestvideo+bestaudio",
                        "-S", "vcodec:h264",
                        "--merge-output-format", "mp4",
                        "--ignore-config",
                        "--no-playlist",
                        "--no-warnings", '-o', 'output.mp4', content])
        with open('output.mp4', 'rb') as file:
            await message.reply(mention_author=False, file=discord.File(file, 'output.mp4'))
        os.remove('output.mp4')

            

client.run(config["BOT_TOKEN"])