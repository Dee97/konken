from linebot import LineBotApi
from linebot.models import *

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import Group
from django.contrib.sessions.backends.db import SessionStore

from dateutil.parser import parse

from attendance.models import User, Question, Attendance, PushRecipients, CramSchool
from bot import bubbles, rich_menu, views
import attendance.services as attendance_service
import bot.bot_operations as bot_op
import bot.constants as const

import json, os, datetime, logging


logger = logging.getLogger('general')
# line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)

"""
        ================
        RICH MENU SET UP
        ================
"""

def create_rich_menu():
    """
        Creates a rich menu according to the template file stored in the rich_menu folder
    """
    template_file = "template.json"
    try:
        location = os.path.join("bot","rich_menu")
        template = json.load(open(os.path.join(location, template_file),'r', encoding='utf-8', errors = 'ignore'))
        # location of rich menu image
        rich_menu.create_menu(template, location)
    except Exception as error:
        logger.info("Error in loading rich menu: " + error)

def create_rich_menus():
    template_file = "template.json"
    cramschools = CramSchool.objects.all()
    try:
        for cramschool in cramschools:
            template_location = os.path.join("bot","rich_menu")
            # img_loc = cramschool.rich_menu_img.url
            template = json.load(open(os.path.join(template_location, template_file),'r', encoding='utf-8', errors = 'ignore'))
            # location of rich menu image
            rich_menu.create_menu(template, cramschool)
    except Exception as error:
        logger.info("Error in loading rich menu: " + error)



"""
        ====================
        FOLLOW EVENT HANDLER
        ====================
"""

def handle_follow(event, profile):
    s = SessionStore(session_key = profile.user_id)
    #getting cramschool details
    cramschool = CramSchool.objects.get(short_name = s['cramschool'])
    bubbles.bubble_register(event, profile, cramschool) 


"""
        ======================
        UNFOLLOW EVENT HANDLER
        ======================
"""

def handle_unfollow(event):
    user = User.objects.filter(line_userid = event.source.user_id)
    if user.exists():
        user = user.first()
        if user.groups.filter(name='Recipients').exists():
            push_recipients = PushRecipients.objects.filter(recipient = user)
            push_recipients.delete()
            user.delete()
            logger.info("Line User student connection and user information deleted.")
        elif user.groups.filter(name='Teachers').exists():
            user.line_userid = ""
            user.line_username = ""
            user.save()
            logger.info("Line User student connection and user information deleted.")
        else:
            logger.info("Something went wrong. Cannot delete user information.")


"""
        ===============
        MESSAGE HANDLER
        ===============
"""

def handle_message(event, profile):
    s = SessionStore(session_key = profile.user_id)
    cramschool = CramSchool.objects.get(short_name = s['cramschool'])
    msg = event.message.text.strip()
    user = User.objects.filter(line_userid = profile.user_id)
    if user.exists():
        user = user.first()

    if s['phase'] == "student_year_level_search" and len(msg) == 1:
        logger.info("student year level search and 1")
        logger.info(s['gkkbn'])
        logger.info(msg)
        if s['gkkbn'] == "elementary" and int(msg) > 6:
            bot_op.send_reply(event, "無効な入力です。1-6を入力してください。", cramschool)
            return
        elif s['gkkbn'] != "elementary" and int(msg) > 3:
            bot_op.send_reply(event, "無効な入力です。1-3を入力してください。", cramschool)
            return

        s['phase'] = "search_student_name"
        s['yrlvl'] = msg
        s.save()
        bot_op.send_reply(event, "名前はなんですか？", cramschool)
        return

    if s['phase'] == "student_year_level_search" and len(msg) != 1:
        logger.info("student year level not 1")
        logger.info(s['phase'])
        logger.info(msg)
        if s['gkkbn'] == "elementary":
            bot_op.send_reply(event, "無効な入力です。1-6を入力してください。", cramschool)
        else:
            bot_op.send_reply(event, "無効な入力です。1-3を入力してください。", cramschool)
        return

    if s['phase'] == "search_student_name":
        logger.info("search_student_name")
        logger.info(s['phase'])
        logger.info(msg)
        bubbles.bubble_search_name(event, profile, cramschool, msg, s['yrlvl'], s['gkkbn'])

    # if the length of the text matches the categories of the student number, trigger bubble
    if len(msg) <= const.stud_id_len and msg.isnumeric():
        s['student_id_number'] = msg
        s.save()
        # bubble 1 yes, user input
        if s['usertype'] == 'parent':
            student = User.objects.filter(
                Q(id_number = msg),
                Q(is_active = True),
                Q(cramschool = cramschool),
                Q(groups__name = 'Students')
            )
        else:
            student = User.objects.filter(
                Q(id_number = msg),
                Q(is_active = True),
                Q(cramschool = cramschool),
                Q(groups__name = 'Teachers')
            )
        if student.exists():
            # call bubble 4
            s['phase'] = "enter_birthday"
            s.save()
            student = student.first()
            bubbles.bubble_birthday(event, profile, student.id_number, cramschool)
        else:
            #calls bubble 3
            bubbles.bubble_wrong_stud_number(event, profile, cramschool)
            logger.info("No student with such student number exists.")
    elif len(msg) == 8:
        if s['student_id_number'] == "":
            bot_op.send_reply(event, "処理できません。まず、生徒番号を入力してください。", cramschool)
            return
        if not is_date(msg):
            bubbles.bubble_wrong_birthday(event, profile, s['student_id_number'], cramschool)
            return
        birthday = datetime.datetime.strptime(msg, '%Y%m%d').date()
        student = User.objects.filter(id_number = s['student_id_number']).first()
        if student is None:
            bot_op.send_reply(event, "申し訳ございません。エラーがありました。登録ボタンをもう一度押してください。")
            return
        if student.birthdate == birthday:
            # calls bubble 6
            bubbles.bubble_sec_first_layer(event, profile, s['student_id_number'], cramschool)
        else:
            #calls bubble 5
            bubbles.bubble_wrong_birthday(event, profile, s['student_id_number'], cramschool)
    elif len(msg) != 8 and len(msg) > const.stud_id_len:
        if s['phase'] == "enter_student_number":
            bubbles.bubble_wrong_stud_number(event, profile, cramschool)
        elif s['phase'] == "enter_birthday":
            bubbles.bubble_wrong_birthday(event, profile, s['student_id_number'], cramschool)
        else:
            bot_op.send_reply(event, "申し訳ございません。入力したキーワードが分かりません。", cramschool)

    # elif msg.find("登録") != -1:
    #     bubbles.bubble_register(event, profile)
    else: 
        find_question = Question.objects.filter(keyword__contains = msg)
        if find_question.exists():
            question = find_question.first()
            if question.q_type == 3:
                bot_op.send_reply(event, f"{const.choose_from_menu}", cramschool)

"""
        =================
        POSTBACK HANDLER
        =================
"""

def handle_postback(event, profile):
    logger.info("entering handle_postback")

    data = event.postback.data
    logger.info(f"data:{data}")
    date_now = datetime.datetime.now().date()
    time_now = datetime.datetime.now()
    time_now_string = time_now.strftime("%H:%M")

    s = SessionStore(session_key = profile.user_id)
    try:
        id_number = s['student_id_number']
    except KeyError as e:
        logger.info('No id number key yet')

    # =========================================================================
    # FIXME: User object BELOW TO BE DELETED ONCE THE SCANNER IS UP AND RUNNING
    # =========================================================================
    # user = User.objects.filter(line_userid = profile.user_id)
    # if user.exists():
    #     user = user.first()

    logger.info("CALLING POSTBACK")
    
    #getting cramschool details
    cramschool = CramSchool.objects.get(short_name = s['cramschool'])
    # bubbles.bubble_register(event, profile, cramschool.default_greeting) 


    question = Question()
   
    if data == "menu_register":
        # call bubble 0
        bubbles.bubble_register(event, profile, cramschool)     
    
    elif data == "enter_student":
        # calls bubble 1
        s['phase'] = "enter_student_number"
        s.save()
        bubbles.bot_op.send_reply(event, "生徒番号をご入力ください。", cramschool)
    
    elif data == "not_register":
        # calls bubble 2
        bubbles.bubble_end_bubble(event, profile, cramschool)
    
    elif data.find("b_bday") != -1:
        # calls bubble 4
        s['phase'] = "enter_birthday"
        s.save()
        bubbles.bubble_birthday(event, profile, id_number, cramschool)
    
    elif data.find("first_sec") != -1:
        s['phase'] = ""
        s.save()
       # calls bubbble 6
        bubbles.bubble_sec_first_layer(event, profile, id_number, cramschool)

    elif data.find("wrong_1st_sec") != -1:
        # calls bubble 7 and 9; the yes_event calls back bubble 6
        bubbles.bubble_wrong_sec(event, profile, id_number, f"first_sec={id_number}", cramschool)
        

    elif data.find("second_sec") != -1:
        # calls bubble 8
        bubbles.bubble_sec_second_layer(event, profile, id_number, cramschool)

    elif data.find("wrong_2nd_sec") != -1:
        # calls bubble 7 and 9; the yes_event calls back bubble 8
        bubbles.bubble_wrong_sec(event, profile, id_number, f"second_sec={id_number}", cramschool)

    elif data.find("last_sec") != -1:
        #calls bubble 10
        bubbles.bubble_sec_last_layer(event, profile, id_number, cramschool)

    elif data.find("final_registration") != -1:
        student = User.objects.get(id_number = id_number)
        logger.info(f"usertype: {s['usertype']}")
        if s['usertype'] == 'parent':
            recipient = User.objects.filter(line_userid = profile.user_id)
            # check if the recipients already (maybe the recipient wants to be registered to another kid)
            if User.objects.filter(line_userid = profile.user_id).exists():
                recipient = recipient.first()
            else:
                recipient = User.objects.create_user(username = profile.user_id, line_userid = profile.user_id, password = settings.DEFAULT_PASS, line_username = profile.display_name, cramschool = student.cramschool)
                recipient.groups.add(Group.objects.get(name='Recipients'))
                recipient.save()

            if PushRecipients.objects.filter(
                Q(trigger = student),
                Q(recipient = recipient)
            ).exists():
                bot_op.send_reply(event, const.account_exists, cramschool)
            else:    
                connect = PushRecipients(trigger = student, recipient = recipient)
                connect.save()
                bot_op.send_reply(event, const.successful_registration, cramschool)
        else:
            confirm_not_exists = User.objects.filter(line_userid = profile.user_id)
            if not confirm_not_exists.exists(): 
                if student.line_userid != profile.user_id:
                    student.line_userid = profile.user_id
                    student.line_username = profile.display_name
                    student.save()
                    bot_op.send_reply(event, const.successful_registration, cramschool)
                elif student.line_userid == profile.user_id:
                    bot_op.send_reply(event, const.account_exists, cramschool)
            else:
                bot_op.send_reply(event, f"アカウントはすでに登録されています。", cramschool)

    elif data == "wrong_registration" :
        # calls bubble 11 
        bubbles.bubble_wrong_register(event, profile, cramschool)

    elif data == "latest_records":
        get_history(event, profile, cramschool)
    
    elif data.find("show_records") != -1:
        stud_id_number = data[data.find("=") + 1 : ]
        bubbles.show_latest(event, profile, stud_id_number, cramschool)

# =======================================
# ADDED IN 02/15/2020
# changes introduced in the 02/10 meeting
# =======================================
    elif data == "enter_usertype":
        # calls bubble 1
        s['phase'] = "enter_usertype"
        s.save()
        bubbles.bubble_usertype(event, profile, cramschool) 
    
    elif data == "is_parent":
        s['usertype'] = "parent"
        s.save()
        bubbles.bot_op.send_reply(event, "生徒番号をご入力ください。", cramschool)

    elif data == "is_teacher":
        s['usertype'] = "teacher"
        s.save() 
        bubbles.bot_op.send_reply(event, "先生番号をご入力ください。", cramschool)
    
    elif data == "student_search":
        s['phase'] = "student_search"
        s.save()
        logger.info("in student_search")
        user = User.objects.filter(line_userid = profile.user_id)
        if user.exists():
            user = user.first()
            if user.groups.filter(name='Teachers').exists():
                # follow bubble path
                bubbles.bubble_search_yearlvl(event, profile, cramschool)
                pass
            else:
               bubbles.bot_op.send_reply(event, "申し訳ございません。先生として登録されていないので、検索ができません。", cramschool) 
        else:
            bubbles.bot_op.send_reply(event, "申し訳ございません。このアカウントはまだ存在しません。登録してください。", cramschool) 
        
    elif data.find("studdiv") != -1:
        student_division = data[data.find("=") + 1 : ]
        s['phase'] = "student_year_level_search"
        s['gkkbn'] = student_division
        s.save()
        if student_division == "elementary":
            bubbles.bot_op.send_reply(event, "生徒は何年生ですか？１-６を入力してください。", cramschool)
        else:
            bubbles.bot_op.send_reply(event, "生徒は何年生ですか？１-３を入力してください。", cramschool) 

    elif data == "srch_again":
        logger.info("search again.")
        s['phase'] == "search_student_name"
        s.save()
        bot_op.send_reply(event, "名前はなんですか？", cramschool)
    
    elif data.find("tshowrecs") != -1:
        logger.info("teacher show recs")
        student_id = data[data.find("=") + 1 : ]
        s['phase'] == "show_stud_info"
        s.save()
        bubbles.bubble_teacher_show_recs(event, profile, cramschool, student_id)

    # =====================================================================
    # FIXME: ACTIONS BELOW TO BE DELETED ONCE THE SCANNER IS UP AND RUNNING
    # =====================================================================
    # elif data == "timein":
    #     actions = [
    #         PostbackAction(
    #                         label = "はい",
    #                         display_text = "TIME INします。",
    #                         data = "do_timein"
    #                     ),
    #         MessageAction(
    #                         label = "いいえ",
    #                         text = "TIME INしません。"
    #                     )
    #     ]
    #     bot_op.send_confirm_message(event,"確認", "TIME INしますか？", actions)
    # elif data == "timeout":
    #     actions = [
    #         PostbackAction(
    #                         label = "はい",
    #                         display_text = "TIME OUTします。",
    #                         data = "do_timeout"
    #                     ),
    #         MessageAction(
    #                         label = "いいえ",
    #                         text = "TIME OUTしません。"
    #                     )
    #     ]
    #     bot_op.send_confirm_message(event,"確認", "TIME OUTしますか？", actions)
    # elif data == "do_timein":
    #     question = Question.objects.get(keyword__contains = "きました")
    #     attendance = Attendance(date = date_now, time_in = time_now, user = user)
    #     success = attendance_service.do_time_in(attendance)
    # elif data == "do_timeout":
    #     question = Question.objects.get(keyword__contains = "でました")
    #     attendance = Attendance(date = date_now, time_out = time_now, user = user)
    #     success = attendance_service.do_time_out(attendance)

    # if data in ["do_timein", "do_timeout"]:
    #     attendance_send_messages(event, user, profile, time_now_string, attendance, question, success)

"""
    ==============
    MISC FUNCTIONS
    ==============
"""
    
def get_history(event, profile, cramschool):
    """
        Sends a bubble message showing the connected students of a recipient

        Args:   
                event(event): Event object coming from Line (contains the reply_token)
                profile(profile): Profile object obtained from the Line User ID; contains information 
                                    such as the profile's display name, display picture, status, etc. 
        Returns:
                Returns nothing.

    """
    try:
        user = User.objects.filter(line_userid = profile.user_id)
        if not user.exists():
            bot_op.send_reply(event, "申し訳ございません。アカウントはまだ存在していません。登録してください。", cramschool)
            return
        user = user.first()
        if user.groups.filter(name='Recipients').exists():
            push_recipient = PushRecipients.objects.filter(recipient = user)
            if not push_recipient.exists():
                raise PushRecipients.DoesNotExist()
                return
            if push_recipient.count() > 1:
                student_list = []
                for pr in push_recipient:
                    student_list.append(pr.trigger)
                bubbles.bubble_show_kids(event, profile, student_list, cramschool)
            else:
                student = push_recipient.first().trigger
                bubbles.show_latest(event, profile, student.id_number, cramschool)
        elif user.groups.filter(name='Teachers').exists():
            bubbles.show_latest(event, profile, user.id_number, cramschool)
        else:
            bot_op.send_reply(event, "申し訳ございません。問題がありました。", cramschool)
    except User.DoesNotExist as e:
        logger.info("User does not exist!")
        bot_op.send_reply(event, "申し訳ございません。アカウントはまだ存在していません。登録してください。", cramschool)
    except PushRecipients.DoesNotExist as e:
        logger.info("Link does not exist!")
        bot_op.send_reply(event, "申し訳ございません。生徒アンケートとつながりません。登録してください。", cramschool)




def is_date(string, fuzzy=False):
    """
        Return whether the string can be interpreted as a date;
        Accepts any format.

        Args:   
                string(string): string to check for date
                fuzzy(boolean): ignore unknown tokens in string if True
        Returns:
                boolean: True if the string can be interpreted as a date otherwise false
    """
    try: 
        to_parse = parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False
    except Exception as e:
        logger.info(e)
        return False

"""
        =======================================
        TO DELETE once the scanner is available
        =======================================
"""

def attendance_send_messages(event, user, profile, time, attendance, question, success):
    """
        Sends multicast message to the recipients if the attendance function is successful and
        replies to the user

        Args:
            event (Webhook Event): from Line
            user (User): contains the recipients
            profile (Line User Profile): obtained from the user id in the webhook event object
            time (time): time when the user timed in or timed out
            attendance (Attendance): contains the mechanism
            question (Question): contains the Answer object, the Answer object contains the recipient_message
            success (Boolean): determines if the attendance was a success
    """
    if user is None:
        bot_op.send_reply(event, "ユーザがデータベースにいません。登録してください。")
        return 
    if success is True and question.answer.recipient_message is not None:
        # bot_op.send_multicast_message(f"{user.first_name}さんが{time}に{question.answer.recipient_message}", list(user.get_recipients()))
        bot_op.send_reply(event, question.answer.answer)
    else:
        bot_op.send_reply(event, "問題がありました。")

