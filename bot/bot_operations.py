from linebot import (
    LineBotApi
)
from linebot.models import *
from django.conf import settings
from attendance.models import CramSchool

# line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)

"""
==================================================
                Message Actions
==================================================
"""

def send_reply(event, message,cramschool):
    """
        Reply to a message given by the user 

        Args:
            event(event): Event object coming from Line (contains the reply_token)
            username(string): username of the message recipient
            
        Returns:
            nothing
    """
    line_bot_api = LineBotApi(cramschool.line_channel_access_token)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

def send_message(user_id, message, cramschool):
    """
        Send a message to a user any time

        Args:
            user_id(string): Webhook event user_id from Line
            message(string): Message to be sent
        
        Returns:
            nothing
    """
    line_bot_api = LineBotApi(cramschool.line_channel_access_token)
    line_bot_api.push_message(user_id, TextSendMessage(text=message))

def send_multicast_message(msg, initial_list, cramschool):
    """
        Sends the same message to multiple users at once any time
        
        Args:
            msg(string): Message to be sent
            initial_list(QuerySet of Users): List of recipients; obtained by running User.get_recipients()
            
        Returns:
            nothing
    """
    if initial_list is None:
        return
    recipients = []
    for row in initial_list:
        recipients.append(row.recipient.line_userid)
    line_bot_api = LineBotApi(cramschool.line_channel_access_token)
    line_bot_api.multicast(recipients, TextSendMessage(text=msg))

def send_confirm_message(event, alt_title, question, cramschool, actions=None):
    """
        Sends a confirmation message 
        
        Args:
            event(event): Event object from Line
            alt_title(string): Title seen when the confirmation message is not viewable (e.g. in Line PC)
            question(string): Question seen on the confirm message. Must be answerable with yes or no.
            actions(list): A list of Messaging Api actions. There must be exactly two elements. 
            
        Returns:
            nothing
    """
    if actions is not None and len(actions) == 2:
        action_list = actions
    else:
        raise IndexError("Not enough elements in the list!")
    confirm_message = TemplateSendMessage(
        alt_text=alt_title,
        template=ConfirmTemplate(
            text=question,
            actions=action_list
        )
    )
    line_bot_api = LineBotApi(cramschool.line_channel_access_token)
    line_bot_api.reply_message(event.reply_token, confirm_message)

def send_buttons_message(event, alt_title, question, cramschool, actions= None):
    """
        Sends a button template message 
        A maximum of four button can be created
        
        Args:
            event(event): Event object from Line
            alt_title(string): Title seen when the confirmation message is not viewable (e.g. in Line PC)
            question(string): Question seen on the confirm message. Must be answerable with yes or no.
            actions(list): A list of Messaging Api actions. There must be exactly two elements. 
            
        Returns:
            nothing
    """
    if actions is not None or len(actions) > 4:
        action_list = actions
    else:
        raise IndexError("There is an error on the actions list passed.")
        return
    buttons_message = TemplateSendMessage(
        alt_text=alt_title,
        template=ButtonsTemplate(
            text=question,
            actions=action_list
        )
    )
    line_bot_api = LineBotApi(cramschool.line_channel_access_token)
    line_bot_api.reply_message(event.reply_token, buttons_message)

