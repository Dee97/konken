from linebot import LineBotApi
from linebot.models import *

from django.conf import settings
from django.db.models import Q
from django.db.models.functions import Concat

from attendance.models import User, Attendance, CramSchool
from django.contrib.sessions.backends.db import SessionStore
from .models import FakeName

from random import shuffle

import logging

import bot.bot_operations as bot_op
import bot.constants as const
from bot.constants import elementary, middle, high
import attendance.services as attendance_service

logger = logging.getLogger('general')

"""
        =====================================
                       BUBBLES
        refer to diagram in the documentation
        for the numbering used here.
        =====================================
"""

def bubble_register (event, profile, cramschool):
    """
        Shows a confirmation message when the 'Register ID' in the rich menu is pressed
        or 'はい' is clicked on the prompt shown when the follow event is triggered.

        THIS IS BUBBLE 0. And the very first bubble.

        Args:
            event (Webhook Event): from Line
            profile (Line User Profile): contains the user ID from the line webhook event

        Returns:
            This function does not return anything.
    """
    
    actions = [
        PostbackAction(
                        label = "はい",
                        display_text = "はい",
                        # data = "enter_student"
                        data = "enter_usertype"
                    ),
        PostbackAction(
                        label = const.not_now,
                        display = const.not_now,
                        data = "not_register"

                    )
    ]

    bot_op.send_confirm_message(
        event,
        "確認", 
        # const.register_greeting, 
        cramschool.default_greeting,
        cramschool,
        actions)

def bubble_usertype(event, profile,cramschool):
    """
        THIS IS A NEW BUBBLE.

        Asks whether the Line User is a teacher or parent
    """

    actions = [
        PostbackAction(
                        label = "両親",
                        display_text = "両親",
                        data = "is_parent"
                    ),
        PostbackAction(
                        label = "先生",
                        display = "先生",
                        data = "is_teacher"

                    )
    ]

    bot_op.send_confirm_message(
        event,
        "ユーザタイプ", 
        # const.register_greeting, 
        "先生ですか？生徒のご両親ですか？",
        cramschool,
        actions)


def bubble_end_bubble(event, profile,cramschool):
    """
        THIS IS BUBBLE 2. 

        Receives and returns the same as bubble 0 (bubble_register).
    """
    bot_op.send_reply(event, const.not_register, cramschool)

def bubble_wrong_stud_number(event, profile,cramschool):
    """
        THIS IS BUBBLE 3. 

        Receives and returns the same as bubble 0 (bubble_register).
    """
    s = SessionStore(session_key = profile.user_id)
    usertype = "生徒" if s["usertype"] == "parent" else "先生"
    data = "is_parent" if s["usertype"] == "parent" else "is_teacher"
    actions = [
                PostbackAction(
                        label = "はい",
                        # data = "enter_student",
                        data = data,
                        display_text = "はい"
                ),
                PostbackAction(
                        label = const.not_now,
                        data = "not_register",
                        display_text = const.not_now
                ) 
        ]
    bot_op.send_confirm_message(event, f"{usertype}番号", f"{usertype}番号をお間違えのようです。登録を続けますか？", cramschool, actions)


def bubble_birthday(event, profile, id_number,cramschool):
    """
        THIS IS BUBBLE 4. 

        Args:
            event (Webhook Event): from Line
            profile (Line User Profile): contains the user ID from the line webhook event
            id_number: passed via Postback; this is the student's id_number

        Returns:
            This function does not return anything.
    """

    bot_op.send_reply(event, "生年月日を入力してください。例) 2010年10月10日 → 20201010", cramschool)

def bubble_wrong_birthday(event, profile, id_number, cramschool):
    """
        THIS IS BUBBLE 5

        Receives and returns the same as bubble 4 (bubble_birthday).
    """
    actions = [
                PostbackAction(
                        label = "はい",
                        data = f"b_bday={id_number}",
                        display_text = "はい"
                ),
                PostbackAction(
                        label = const.not_now,
                        data = "not_register",
                        display_text = const.not_now
                ) 
        ]
    bot_op.send_confirm_message(event, "生年月日入力", "生年月日をお間違えのようです。登録を続けますか？", cramschool, actions)

def bubble_sec_first_layer(event, profile, id_number, cramschool):
    """
        THIS IS BUBBLE 6.

        Receives and returns the same as bubble 4 (bubble_birthday)
    """
    student = User.objects.get(id_number = id_number)
    random_names = list(FakeName.objects.exclude(name = student.first_name))
    shuffle(random_names)
    random_name = random_names[1]

    actions = [
                PostbackAction(
                        label = "はい",
                        data = f"wrong_1st_sec={id_number}",
                        display_text = "はい、そうです。"

                ),
                PostbackAction(
                        label = "いいえ",
                        data = f"second_sec={id_number}",
                        display_text = "いいえ,違います。"
                )
            ]
    bot_op.send_confirm_message(event, "名前を選択", f"{random_name}さんですね？", cramschool, actions)

def bubble_wrong_sec(event, profile, id_number, yes_event, cramschool):
    """
        This function is used for bubbles 7 and 9

        Args:
            event (Webhook Event): from Line
            profile (Line User Profile): contains the user ID from the line webhook event
            id_number: passed via Postback; this is the student's id_number
            yes_event: the postback data used to lead the user back to the previous bubble

        Returns:
            This function does not return anything.
    """
    actions = [
                PostbackAction(
                        label = "はい",
                        data = yes_event,
                        display_text = "はい"
                ),
                PostbackAction(
                        label = const.not_now,
                        data = "not_register",
                        display_text = const.not_now
                ) 
        ]
    bot_op.send_confirm_message(event, "名前間違い", "名前をお間違えのようです。登録を続けますか？", cramschool, actions)

def bubble_sec_second_layer(event, profile, id_number, cramschool):
    """
        THIS IS BUBBLE 8.

        Receives and returns the same as bubble 4 (bubble_birthday)
    """
    s = SessionStore(session_key = profile.user_id)
    
    usertype = "生徒" if s['usertype'] == "parent" else "先生"
    mes = "お子様の名前は？" if s['usertype'] == "parent" else "先生の名前は？"
    student = User.objects.get(id_number = id_number)
    random = list(FakeName.objects.exclude(name = student.first_name))
    shuffle(random)
    random1 = random[0]
    random2 = random[1]
    actions = [
                PostbackAction(
                        label = f"{random1}さん",
                        data = f"wrong_2nd_sec={id_number}",
                        display_text = f"{random1}さん"
                ),
                PostbackAction(
                        label = f"{random2}さん",
                        data = f"wrong_2nd_sec={id_number}",
                        display_text = f"{random2}さん"
                ),
                PostbackAction(
                        label = "どちらでもない",
                        data = f"last_sec={id_number}",
                        display_text = "どちらでもない"
                ),
            ]
    bot_op.send_buttons_message(event, f"{usertype}を選択", mes, cramschool, actions)

def bubble_sec_last_layer(event, profile, id_number, cramschool):
    """
        THIS IS BUBBLE 10 and the final bubble

        Receives and returns the same as bubble 4 (bubble_birthday)
    """
    student = User.objects.get(id_number = id_number)
    actions = [
                PostbackAction(
                        label = "はい",
                        data = f"final_registration={id_number}",
                        display_text = "はい"
                ),
                PostbackAction(
                        label = "いいえ",
                        data = "wrong_registration",
                        display_text = "いいえ"
                )
        ]
    
    bot_op.send_confirm_message(event, "生徒を選択", f"{student.first_name}さんですね？", cramschool, actions)

def bubble_wrong_register(event, profile, cramschool):
    """
        THIS IS BUBBLE 11

        Receives and returns the same as bubble 0 (bubble_register).
    """
    bot_op.send_reply(event, cramschool.failed_registration, cramschool)

def bubble_show_kids(event, profile, student_list, cramschool):
    count = 0
    actions = []
    # token = attendance_service.get_token(profile.user_id)
    for student in student_list:
        if count != 3: 
            actions.append(
                PostbackAction(
                            label = f"{student.first_name}さん",
                            data = f"show_records={student.id_number}",
                            display_text = f"{student.first_name}さん"
                    )
            )
            count+=1
        else:
            actions.append(
            URIAction(
                        label = f"もっと見る",
                        uri = f"https://{settings.CURRENT_APP_URL}/view/linked/{profile.user_id}"
                )
        )
        
    bot_op.send_buttons_message(event, "生徒を選択", "どちらのお子様の履歴を表示しますか?", cramschool, actions)



def show_latest(event, profile, id_number, cramschool):
    """
        Sends a bubble showing the history of a student given the ID number

        Args:   
                event(event): Event object coming from Line (contains the reply_token)
                profile(profile): Profile object obtained from the Line User ID; contains information 
                                    such as the profile's display name, display picture, status, etc. 
                id_number(string): ID number of the student whose latest attendance records is to be shown.
        Returns:
                Returns nothing.
    """
    try:
        s = SessionStore(session_key = profile.user_id)
        # usertype = "生徒" if s["usertype"] == "parent" else "先生"
        student = User.objects.get(id_number = id_number)
        latest_records = Attendance.objects.filter(user = student).order_by('-date', '-time_in')[:2]
        if not latest_records.exists():
            raise Attendance.DoesNotExist()
            return
        message = ""
        for record in latest_records:
            time_in = record.time_in.strftime("%H:%M:%S") if record.time_in is not None else " "
            time_out = record.time_out.strftime("%H:%M:%S") if record.time_out is not None else " "
            message += f"{record.date}\n"
            message += f"\t\t\t\t入: {time_in}\n"
            message += f"\t\t\t\t出: {time_out}\n"

        # token = attendance_service.get_token(profile.user_id)

        actions = [
            URIAction(
                        label = f"もっと見る",
                        uri = f"https://{settings.CURRENT_APP_URL}/attendance/list/{student.id}/{profile.user_id}"
                )
        ]
        bot_op.send_buttons_message(event, "最新の履歴", question = message, cramschool = cramschool, actions = actions)
    except Attendance.DoesNotExist as e:
        bot_op.send_reply(event, f"このユーザは履歴がありません。", cramschool)

#=====================================
# added in accordance to 02/10 meeting
#=====================================

def bubble_search_yearlvl(event, profile, cramschool):
    logger.info("in bubble search yearlvl")
    actions = []
    actions.append(
                PostbackAction(
                        label = "小学",
                        data = "studdiv=elementary",
                        display_text = "小学"
                    )
            )
    actions.append(
                PostbackAction(
                        label = "中学",
                        data = "studdiv=middle",
                        display_text = "中学"
                    )
            )
    actions.append(
                PostbackAction(
                        label = "高校",
                        data = "studdiv=high",
                        display_text = "高校"
                    )
            )
    bot_op.send_buttons_message(event, "学校区分を選択", "生徒の学校区分は何ですか?", cramschool, actions)

def bubble_search_name(event, profile, cramschool, student_name, year_level, gakko_kubun):
    logger.info("in bubble search name")
    results = User.objects.annotate(search_name=Concat('last_name', 'first_name'))
    results = results.annotate(search_name_kana=Concat('last_name_kana', 'first_name_kana'))
    if gakko_kubun == "elementary":
        actual_yrlvl = elementary.get(int(year_level))
    elif gakko_kubun == "middle":
        actual_yrlvl = middle.get(int(year_level))
    elif gakko_kubun == "high":
        actual_yrlvl = high.get(int(year_level))
    else:
        actual_yrlvl = None
        bot_op.send_reply(event, "申し訳ございません。問題がありました。もう一度入力してください。", cramschool)
    logger.info(actual_yrlvl)
    results = results.filter(
        (
            Q(first_name__icontains = student_name) |
            Q(last_name__icontains = student_name) | 
            Q(first_name_kana__icontains = student_name) |
            Q(last_name_kana__icontains = student_name) |
            Q(search_name__icontains = student_name) | 
            Q(search_name_kana__icontains = student_name)
        )
        & Q(cramschool = cramschool)
        & Q(is_active = True)
        & Q(year_level = actual_yrlvl)
        & Q(groups__name='Students')
    ).order_by('year_level', 'search_name')

    first_three = results[:3]
    actions = []
    # token = attendance_service.get_token(profile.user_id)
    message = "どちらの生徒さんを表示しますか?"
    if len(results) > 0:
        for student in first_three:
            actions.append(
                            PostbackAction(
                                        label = f"{student.last_name}{student.first_name}さん",
                                        data = f"tshowrecs={student.id_number}",
                                        display_text = f"{student.last_name}{student.first_name}さん"
                                )
                        )
    else:
        message = "申し訳ございません。生徒が見つかりません。"

    actions.append(
                PostbackAction(
                            label = "名前をまた入力",
                            data = "srch_again",
                            display_text = f"名前をまた入力する"
                    )
            )
    bot_op.send_buttons_message(event, "生徒を選択", message, cramschool, actions)


def bubble_teacher_show_recs(event, profile, cramschool, student_id):
    logger.info("in bubble teacher show recs")
    student = User.objects.get(id_number = student_id)
    nl = '\n'
    tab = '\t'
    message = f"連絡先：{nl}{tab}{tab}{tab}{student.mobile_num_1}{nl}{tab}{tab}{tab}{student.mobile_num_2} {nl}{nl} 履歴： https://{settings.CURRENT_APP_URL}/attendance/list/{student.id_number}/{profile.user_id}"

    bot_op.send_reply(event, message, cramschool)

