from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
)
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.backends.db import SessionStore

from linebot import (
    LineBotApi, WebhookHandler, WebhookParser
)
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

import bot.services as bot_service
from attendance.models import CramSchool, User


from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.renderers import TemplateHTMLRenderer
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.parsers import FormParser, MultiPartParser


# line_bot_api = LineBotApi("sample")
# handler = WebhookHandler("sample")

from importlib import import_module
import json, logging
from bot import sessions

logger = logging.getLogger('general')

@csrf_exempt
def callback_new(request, short_name):
    cramschool = CramSchool.objects.get(short_name = short_name)
    line_bot_api = LineBotApi(str(cramschool.line_channel_access_token))
    #handler =  WebhookHandler(str(cramschool.line_channel_secret))
    parser = WebhookParser(cramschool.line_channel_secret)
    domain = request.META['HTTP_HOST']

    if request.method == "POST":

        signature = request.META['HTTP_X_LINE_SIGNATURE']

        body = request.body.decode('utf-8')
        body_dict = json.loads(body)
        # getting the user ID to retrieve its session
        sessions.open_session(body_dict['events'][0]['source']['userId'])
        s = SessionStore(session_key = body_dict['events'][0]['source']['userId'])
        s['cramschool'] = short_name
        s.save()

        try:
            logger.info(signature)
            # handle webhook
            # handler.handle(body, signature)
            events = parser.parse(body, signature)

            for event in events:
                if isinstance(event, MessageEvent):
                    if isinstance(event.message, TextMessage):
                        logger.info("handling message")
                        profile = line_bot_api.get_profile(event.source.user_id)
                        bot_service.handle_message(event, profile)
                if isinstance(event, PostbackEvent):
                    logger.info("handling postback")
                    profile = line_bot_api.get_profile(event.source.user_id)
                    bot_service.handle_postback(event, profile)
                if isinstance(event, FollowEvent):
                    logger.info("handling follow event")
                    profile = line_bot_api.get_profile(event.source.user_id)
                    bot_service.handle_follow(event, profile)
                if isinstance(event, UnfollowEvent):
                    logger.info("handling unfollow event")
                    bot_service.handle_unfollow(event)
            
        except InvalidSignatureError:
            return HttpResponseBadRequest
        return HttpResponse()
    else:
        return HttpResponseBadRequest

    
# @handler.add(FollowEvent)
#             def handle_follow(event):
#                 profile = line_bot_api.get_profile(event.source.user_id)
#                 bot_service.handle_follow(event, profile)

#             @handler.add(UnfollowEvent)
#             def handle_unfollow(event):
#                 bot_service.handle_unfollow(event)

#             @handler.add(MessageEvent, message=TextMessage)
#             def handle_message(event):
#                 logger.info("handling message")
#                 profile = line_bot_api.get_profile(event.source.user_id)
#                 bot_service.handle_message(event, profile)
                
#             @handler.add(PostbackEvent)
#             def handle_postback(event):
#                 logger.info("handling postback")
#                 profile = line_bot_api.get_profile(event.source.user_id)
#                 bot_service.handle_postback(event, profile)

# @csrf_exempt
# def callback(request):
#     # old callback method, for one bot only
#     if request.method == "POST":
#         signature = request.headers['X-Line-Signature']
#         signature = request.META['HTTP_X_LINE_SIGNATURE']
#         global domain
#         domain = request.META['HTTP_HOST']
#         body = request.body.decode('utf-8')
#         body_dict = json.loads(body)
#         # getting the user ID to retrieve its session
#         sessions.open_session(body_dict['events'][0]['source']['userId'])

#         try:
#             # handle webhook
#             handler.handle(body, signature)
#         except InvalidSignatureError:
#             return HttpResponseBadRequest
#         return HttpResponse()
#     else:
#         return HttpResponseBadRequest


    
def index(request):
    return HttpResponse("Bot index.")

class RefreshRichMenu(APIView):
    permission_classes = (AllowAny,)
    renderer_classes  = [TemplateHTMLRenderer]
    template_name = 'bot/refresh_menu.html'
    parser_classes = (FormParser, MultiPartParser)

    def get(self, request):
        return Response(status = status.HTTP_200_OK)

    def post(self, request, format = None):
        logger.info("Refreshing all rich menus...")
        # refreshes all rich menus in all bots
        bot_service.create_rich_menus()
        context = "Refresh successful!"
        return Response(status = status.HTTP_200_OK)