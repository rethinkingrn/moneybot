# MoneyBot v0.0.90402734201 - Cosemetic Carrot
Discord bot made entirely with Cursor, ChatGPT, Claude, and Deepseek, there will be no support provided

I don't think i've typed a single line of code in myself

## Features (100% TOS violation)
- Economy based on skull reactions, encourages sending messages with no purpose then self reacting with a 💀
- Tracking avatar/status/game activity changes (Manually select users, although its definitely possible to do everyone by default)
- Message logger with timestamps, userid, idk
- Gambling (coinflip) to encourage going all in just to lose
- A leaderboard for the reaction-based economy
- Something to do with AI, it doesn't even work 90% of the time
- "Automatic" profile picture/banner/status rotation
- Shop to buy useless items that serve no purpose.

## Requirements
- Python venv with all the stuff in requirements.txt (there is most likely things missing but I don't want to fix that)
- discord.py
- mongodb server
- `.env`(refer to the .env.example)
- ollama instance running dolphin-mistral or just change it yourself
- [zipline](https://zipline.diced.sh/)

## TODO
- Implement Docker
- Fix start.sh (Get rid of absolute paths or change it)
- Fix hardcoded user id in some of the commands
- Profile picture rotation (seems to only rotate between 5 pictures max)
- Cleanup the code