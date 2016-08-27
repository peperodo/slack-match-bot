#!/usr/bin/python

import os
import time
import json
from slackclient import SlackClient
from tourny import Tourny
from player import Player

BOT_ID = os.environ.get("BOT_ID") 

# constants
AT_BOT = "<@" + BOT_ID  + ">"
ROOM_NAME = "pingpongtourny"
EXAMPLE_COMMAND = "do"
START_TOURNY = "start tourny"

tourny = Tourny()
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN')) 

def populate_tourny():
  json_raw = slack_client.api_call("channels.list")
  for channel in json_raw['channels']:
    if str(channel['name']) == "pingpongtourny":
      channel_id = str(channel['id'])
  
  if not channel_id:
    return

  channel_info_raw = slack_client.api_call("channels.info", channel=channel_id)
  channel_info = channel_info_raw["channel"]
  for member_id in channel_info["members"]:
    member_info_raw = slack_client.api_call("users.info", user=member_id)
    member_info = member_info_raw["user"]
    profile = member_info["profile"]
    tourny.add_player(Player(member_info["name"], profile["first_name"], profile["last_name"]))
  
  tourny.show_players()

def handle_command(command, channel):
  """
    Recieves commands directed to the bot and determins if they
    are valid commands. If so, then acts on teh commands. If not,
    returns back what it needs for clarification.
  """
  response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
    "* command with numbers, deliminated by spaces."
  if command.startswith(EXAMPLE_COMMAND):	
    response = "Sure... write more code then I can do that!"
  if command.startswith(START_TOURNY):
    populate_tourny()    
    response = "Generating tournament bracket!"

  slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
  """
    The Slack Real Time Messaging API is an events firehose.
    This parsing function returns None unless a messagte is
    directed at the Bot, based on its ID.
  """
  output_list = slack_rtm_output
  if output_list and len(output_list) > 0:
    for output in output_list:
      if output and 'text' in output and AT_BOT in output['text']:
        # return text after the @ mention, whitespace rempoved
        return output['text'].split(AT_BOT)[1].strip(':').lower(), output['channel']

  return None, None

def main():
  READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
  if slack_client.rtm_connect():
    print("MatchBot connected and runing!")
    while True:
      command, channel = parse_slack_output(slack_client.rtm_read())
      if command and channel:
        handle_command(command, channel)
      time.sleep(READ_WEBSOCKET_DELAY)
  else:
    print("Connection failed. Invalide Slack token or bot ID")

if __name__ == '__main__': 
  main()