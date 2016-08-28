#!/usr/bin/python

import os
import json

from slackclient import SlackClient
import time

from tourny import Tourny
from player import Player

BOT_ID = os.environ.get("BOT_ID") 

# constants
AT_BOT = "<@" + BOT_ID  + ">"
ROOM_NAME = "pingpongtourny"

HELP_COMMAND = "help"
START_TOURNY = "start"
PRINT_TOURNY = "print"
REPORT_WIN = "win"

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
    
    first_name = ""
    if "first_name" in profile:
      first_name = profile["first_name"]
    lase_name = ""
    if "last_name" in profile:
      last_name = profile["last_name"]
    
    tourny.add_player(Player(member_info["id"], member_info["name"], first_name, last_name))
  
  tourny.add_player(Player("U2134134", "yyy", "han", "solo"))
  tourny.start_tourny()

def handle_command(user, command, channel):
  """
    Recieves commands directed to the bot and determins if they
    are valid commands. If so, then acts on teh commands. If not,
    returns back what it needs for clarification.
  """
  response = "Not sure what you mean. Use the *" + HELP_COMMAND + \
    "* command with numbers, deliminated by spaces."
  if command.startswith(HELP_COMMAND):	
    response = "Sure... write more code then I can do that!"
  if command.startswith(START_TOURNY):
    populate_tourny()    
    response = "Generating tournament bracket!"
  if command.startswith(PRINT_TOURNY):
    print "Printing trounament bracket..."
    response = "Printing trounament bracket...\n" + tourny.get_printed_tourny()
  if command.startswith(REPORT_WIN):
    tourny.report_win(user)
    response = "Reporting win."

  tourny.print_tourny()

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
      if output and 'text' in output and AT_BOT in output['text'] and 'user' in output:
        # return text after the @ mention, whitespace removed
        return output['user'], output['text'].split(AT_BOT)[1].strip(' ').lower(), output['channel']

  return None, None, None

def main():
  READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
  if slack_client.rtm_connect():
    print("MatchBot connected and runing!")
    while True:
      user, command, channel = parse_slack_output(slack_client.rtm_read())
      if command and channel:
        handle_command(user, command, channel)
      time.sleep(READ_WEBSOCKET_DELAY)
  else:
    print("Connection failed. Invalide Slack token or bot ID")

if __name__ == '__main__': 
  main()
