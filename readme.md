Hi, this repo is still being developed as I have time, but I wanted to publish an alpha version of it so it was avaliable to use with the recent death of Clyde.

If you want to run the code, you first need to create a keys directory and add the following files:
discord_token.txt: A text file containing a discord token for the bot to use (required by everything)
giphy_apikey.txt: Text file containing a giphy api key (used in itsyou.py)
openai_apikey.txt: File containig an Chatgpt OpenAi Api key to use for various chat completions (used in gpt.py/chatgpt.py)

Required External Libraries are all avaliable in the requirements.txt document
To setup a new (virtual) environment, run the following command:
pip install -r requirements.txt

If you're running an older version of python3, you need a differnet spell checker.
See lib/spellchecker.py for details

run the bot by running the following command from the base of the repo (ideally using screen):
python3 clydebutwigglier.py
