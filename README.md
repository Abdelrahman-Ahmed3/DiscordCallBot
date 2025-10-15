# Discord Call Bot



This is a bot designed to notify opted-in users when someone joins a specific “waiting room” voice channel; it can be used for study groups, gaming servers, or teams doing a group project. The bot monitors a designated waiting channel, waits the configured delay, notifies opted-in users, and (when applicable) moves members to the target channel. The bot is designed to be hosted on Render for free, with the option of self-hosting if preferred.

## Features
- Notifies selected users when someone joins a waiting voice channel.
- Fully configurable with slash commands.
- Can run 24/7 for free on Render.
- Saves settings using JSONBin.io.

## Requirements
- Python 3.8+
- A Discord bot token (from the Discord Developer Portal)
- A JSONBin.io account (API key and Bin ID)
- (Optional) A Render account for hosting
## Hosting and Installation.

1. If you plan to host it on Render, skip this step. But if you are hosting the bot locally, make a file in the folder that the bot is in called `.env` and paste the following into it, we will fill it later. 
   ```bash
   DISCORD_TOKEN=TOKEN
   JSONBIN_API_KEY=API_KEY
   JSONBIN_BIN_ID=BIN_ID
   ```
   then you will need to run the following command in the Command prompt to install the requirements, you will need to have python installed to run the bot.
   ```cmd
   pip install requirements.txt
   ```

2. Go to [Render](https://render.com/register) and follow [this video](https://youtu.be/HZis54wRF98?t=132) on how to host the bot for free, you will need to create the environment variables like in the code above.
3. Go to the [Discord Developer Hub](https://discord.com/developers/applications),
   - Make an app with all the privileged intents (Presence Intent, Server Members Intent
 & Message Content Intent).
   
   - From the bot tab, press `Reset Token`, and then copy your token over to the `.env` file or the environment variables in Render.
   - Finally, from the `OAuth2` tab, under `OAuth2 URL Generator`, select the `bot` scope and below it select the following Bot Permissions.
![perms](https://i.ibb.co/674LGWRJ/botperms.png)
   - Copy the `Generated URL` below and paste it in chrome to invite the bot to your discord server.

4. Head over to [JSONBIN.io](https://jsonbin.io/create-account) and make an account, then from `API KEYS` copy the `X-Master-Key` and put that in the environment variables in place of `API_KEY`.
5. In JSONBIN.io, go to `BINS`, create a bin and copy the `Bin ID` and paste it in your .env or Render environment variables as the value for JSONBIN_BIN_ID., it should automatically create the content of the bin as soon as we host the bot, in case it does not, copy the code below into the bin.


    ```json
    {
       "waiting_channelid": Null,
       "target_channelid": Null,
       "targets": [],
       "optin_message_id": Null,
       "wait": 10,
       "server_id": Null
    }
    ```
## Set Up

After inviting the bot to your Discord server, Use the following commands:

1. Type `!setserver` into a channel, the bot should reply with  
`✅ Server has been set. Commands will now sync to SERVERNAME`, restart the bot from Render to ensure correct syncing, otherwise the slash commands won't work straight away, and you will need to wait about an hour.
2. Use `/set_waiting_channel` to select the channel you want users to wait in.
3. Use `/set_target_channel` to select the channel the users will get moved to after someone joins a waiting user.
4. In the channel you want the opt-in message to be, Use `/setup_message` to send a channel that members can use to opt in to notifications from the bot.

Optionally, you can use `/set_waiting_time` to change the time that a person needs to wait before the bot sends a message to the opted-in users, the default is set to 10 seconds.

## FAQ
1. I don't see any commands from the bot.
- This is because of how discord's slash commands work, they need to sync globally which causes a delay of about an hour or so, BUT I have implemented a sync function to force it to sync to your server quickly, to fix it, type !setserver in any text channel and then when the bot replies, restart it from [Render](https://dashboard.render.com/) and it should work.
2. The bot isn't online when I just set it up.
-  This is most likely because you haven't set up the environment variables correctly, double check them and if they are correct, make sure that you set up Render correctly according to [the video provided above](https://youtu.be/HZis54wRF98?t=132).
For any other issues, feel free to open an issue or contact send me a message on the support discord: [invite](https://discord.gg/9T9XrGgCFY)

## To Do
- [x] Make a README
- [ ] Use the render webserver to make a website to configure the bot.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
with what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)