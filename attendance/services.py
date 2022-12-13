from django.db.models import Q, Count, Max, Subquery
from django.db.models.functions import Concat
from django.db import IntegrityError
from .models import Attendance, User, CardScan, PushRecipients, Holiday, CardLog, YearLevel, School, CramSchool
from django.contrib.auth.models import Group

import csv, io, datetime, os, requests, time, json, calendar
# from attendance import tasks
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation, ValidationError, ViewDoesNotExist
from django.core.mail import send_mail
from django.core.validators import validate_email

import bot.constants as constants

from django.http import HttpResponse

import logging

card_logger = logging.getLogger('card_scan')
logger = logging.getLogger('general')

"""
    ==========================================================
    RETRIEVAL FUNCTIONS
        - functions used for selecting stuff from the database
    ==========================================================
"""

def get_students_and_teachers_list(loggedin_user):
    """
        Gets the list of active Students and Teachers from the database

        Args:   
                is_staff(boolean): If true, will show students and teachers,
                                   If false, will only show students
        
        Returns:
                QuerySet: instance of Users
    """
    users = User.objects.annotate(search_name=Concat('last_name', 'first_name'))
    if loggedin_user.is_superuser: 
        return users.filter((Q(groups__name='Students') | Q(groups__name='Teachers')) & Q(is_active=True)).order_by('year_level', 'search_name')
    elif loggedin_user.is_staff:
        return users.filter((Q(groups__name='Students') | Q(groups__name='Teachers')) & Q(is_active=True) & Q(cramschool = loggedin_user.cramschool)).order_by('year_level', 'search_name')
    elif loggedin_user.groups.filter(name='Teachers').exist():
        return users.filter((Q(groups__name='Students')) & Q(is_active=True)).order_by('year_level', 'search_name')
    else:
        return None

def search_user(query, filter, loggedin_user):
    """
        Gets the list of active Students and Teachers from the database

        Args:   
                query(string): string to be matched in the database
                filter(string): accepted values are Students, Teachers and both
                                this value is received from the dropdown menu in the frontend
        
        Returns:
                QuerySet: instance of Users
    """ 
    if filter == "" or filter is None:
        filter = "Students"
    users = User.objects.annotate(search_name=Concat('last_name', 'first_name'))
    users = users.filter(
        (
            Q(id_number__icontains = query) |
            Q(first_name__icontains = query) |
            Q(last_name__icontains = query) | 
            Q(first_name_kana__icontains = query) |
            Q(last_name_kana__icontains = query) | 
            Q(card_id__icontains = query) | 
            Q(search_name__icontains = query)
        ) &
         Q(is_active = True)
    ).order_by('year_level', 'search_name')
    if filter == "both":
        users = users.filter((Q(groups__name='Students') | Q(groups__name='Teachers')))
    else:
        users = users.filter(groups__name = filter)

    if not loggedin_user.is_superuser:
        users = users.filter(Q(cramschool = loggedin_user.cramschool))
    return users

def get_user(id_number = None, pk = None, card_id = None, line_userid = None):
    """
        Args:   
                id_number, pk, card_id (all strings): accepts any of these parameters to search a user
        Returns:
                User: instance of User
    """
    try:
        if id_number is not None:
            return User.objects.get(id_number=id_number)
        elif pk is not None:
            return User.objects.get(pk=pk)
        elif line_userid is not None:
            return User.objects.get(line_userid = line_userid)
        else:
            return User.objects.get(card_id__iexact=card_id)
    except User.DoesNotExist:
        raise ViewDoesNotExist()

def get_user_restrict(pk, loggedin_user):
    if loggedin_user.is_superuser:
        return User.objects.get(pk = pk)
    else:
        return User.objects.get(pk = pk, cramschool = loggedin_user.cramschool)

def get_attendance_records(user, month_year):
    """
        Retrieve the attendance records of a user given a month and year
        Used in the CSV export
        Does not check if the one asking has authority to do so

        Args:   
                user(User): The User instance whose Attendance record is to be retrieved
                month_year(datetime.date): The date of the record that is to be retrieved

        Returns:
                QuerySet: of Attendance objects
            
    """
    return Attendance.objects.filter(
                            Q(date__year=month_year.year) & 
                            Q(date__month=month_year.month) & 
                            Q(user = user)
                        )

def get_attendance(date, user):
    """
        Gets the Attendance instance given a date and a User 
        THIS FUNCTION IS USED IN THE ATTENDANCE MECHANISM

        Args:   
                date(datetime.date): The date of the record that is to be retrieved
                user(User): The User instance whose Attendance record is to be retrieved

        Returns:
                Attendance: if the record exists
                None: if the record does not exist
    """
    existing = Attendance.objects.filter(
                Q(date=date),
                Q(user=user)
            ).order_by('-time_in')
    if existing.exists():
        return existing.first()
    else:
        return None

def get_holidays():
    """
        Retrieves Holidays objects sorted by date in a descending order

        Args:   
                None
        Returns:
                QuerySet: instance of Holiday objects
    """
    return Holiday.objects.all().order_by('-date')

def get_schools(loggedin_user):
    """
        Retrieves Schools objects sorted by date in a descending order

        Args:   
                None
        Returns:
                QuerySet: instance of Holiday objects
    """
    if loggedin_user.is_superuser:
        return School.objects.all().order_by('level_division','school_name')
    else:
        return School.objects.filter(cramschool = loggedin_user.cramschool).order_by('level_division','school_name')

def get_next_month(date_received):
    """
        Calculates the next month given the date received.

        Args:   
                date_received(datetime.date): date to be calculated from
        Returns:
                (datetime.date): first day of the next month
    """
    return (date_received.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

def get_prev_month(date_received):
    """
        Calculates the previous month given the date received.

        Args:   
                date_received(datetime.date): date to be calculated from
        Returns:
                (datetime.date): first day of the previous month
    """
    return (date_received.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)

def get_card_logs():
    """
        Retrieves the latest entries from the CardLog table
        sorted in descending order by date then time

        Args:   
                None
        Returns:
                QuerySet: instance of CardLog objects

    """
    return CardLog.objects.all().order_by('-date', '-time')

def get_schools():
    """
        Retrieves Schools objects sorted by date in ascending order

        Args:   
                None
        Returns:
                QuerySet: instance of School objects
    """
    return School.objects.all().order_by('school_code')

"""
    ==========================================================
    ATTENDANCE FUNCTIONS
    - used for the attendance mechanism
    ==========================================================
"""

def time_out(attendance, card_scan):
    """
        Updates the time out field of the given Attendance instance.

        Args:   
                attendance(Attendance): Attendance object to be updated
                card_scan(CardScan): CardScan object whose details will be used to update the Attendance record
        
        Returns:
                boolean: always True 
    """
    attendance.time_out = card_scan.time
    attendance.save()
    return True

def time_in(card_scan, user):
    """
        Creates and saves an Attendance instance in the database.

        Args: 
                card_scan(CardScan): CardScan object whose details will be used to create a new Attendance record
                user(User): User object that should be in the Students group, also used in the new Attendance record
        
        Returns:
                boolean: True if the record was successfully saved in the datbase otherwise False
    """
    try:
        attendance = Attendance(date = card_scan.date, time_in = card_scan.time, user = user)
        attendance.save()
        return True
    except IntegrityError as e:
        logger.info(e)
        return False

def do_attendance(card_scan):
    """
        Triggers attendance mechanism given a CardScan instance

        Args:
                card_scan(CardScan): CardScan whose details will be used to either update or
                                    create an Attendance record
        
        Returns:
                boolean: True if the attendance record was successfully updated or created
                         otherwise it is False
    """
    user = get_user(card_id = card_scan.cid)    

    attendance = get_attendance(card_scan.date, user)
    if attendance is not None and attendance.time_out is None:
        return time_out(attendance, card_scan)
    else:
        # check if the existing records is below 5, if true, allow save.
        total = len(Attendance.objects.filter(
                            Q(date = card_scan.date) & 
                            Q(user = user)))
        if total < 5:
            return time_in(card_scan, user)
        else:
            return False



def get_attendance_list(id, user_id):
    """
        Retrieves the attendance list of a student only if the user_id received is listed as the student's recipient
        LOG VIEW OF THE STUDENT ATTENDANCE, not to be confused with the get_attendance_records

        Args:
                id_number(string): ID Number of the Student whose attendance list is to be retrieved
                user_id(string): ID (not LINE ID), that is the primary key of the Recipient who wishes to retrieve 
                                the student's attendance records
        
        Returns:
                QuerySet: of Attendance
    """
    student = User.objects.get(pk = id)
    asking = User.objects.get(pk = user_id)
    existing = PushRecipients.objects.filter(
                Q(trigger = student),
                Q(recipient = asking)
            )
    if existing.exists() or student == asking \
        or asking.is_staff \
        or (student.groups.all()[0].name == "Students" and asking.groups.all()[0].name == "Teachers"):
        return Attendance.objects.filter(user = student)
    else:
        raise PermissionDenied()

"""
    ==============================================================
    BOT FUNCTIONS
     - functions that retrieve attendance related data for the bot
    ==============================================================
"""

def get_student_list(user_id):
    """
        Retrieves the students connected to a recipient

        Args:   
                user_id(string): Recipient's primary key in the database not the LINE ID
        
        Returns:
                List: of Users(that belong to the Student Group) that are connected with the Recipient
                None: if the Recipient is not connected to any student
    """
    recipient = User.objects.get(pk = user_id)
    existing = PushRecipients.objects.filter(recipient = recipient)
    if existing.exists():
        student_list = [pushrecipient.trigger for pushrecipient in existing.all()]
        return student_list
    else:
        return None

# def get_token(user_id):
#     """
#         Retrieves a token given a LINE user ID
#         USED IN THE BOT FOR AUTHENTICATION

#         Args:
#                 user_id(string): LINE user ID, only obtainable via LINE
        
#         Returns:
#                 String: authorization token
#     """
#     logger.info("getting token")
#     logger.info(f"{user_id} - {settings.DEFAULT_PASS}")
#     logger.info(f"https://{settings.CURRENT_APP_URL}/api/token/")
#     payload = {'username': user_id, 'password': settings.DEFAULT_PASS}
#     url = f"https://{settings.CURRENT_APP_URL}/api/token/"
#     token = ""

#     try:
#         response = requests.post(url, json = json.dumps(payload), timeout=3, verify = False)
#         token = response.json()["token"]
#         return token
#     except requests.exceptions.ReadTimeout:
#         logger.info("Error with getting the token.")
#         return token



"""
    ======================================================================
    CARD SCAN FUNCTIONS
    - functions used in scanning unregistered cards. mostly deals with logs
    
    =======================================================================
"""

def get_latest_unregistered_card_scan_logs(loggedin_user):
    """
        Used for retrieving today's cards that are not yet saved in the database
        
        Args:
                nothing
        
        Returns:
                QuerySet: instance of CardLogs
    """
    # show only the unregistered cards that were scanned today
    now = datetime.datetime.now()
    s = Subquery(User.objects.exclude(card_id__isnull = True).values('card_id'))
    initial = CardLog.objects.exclude(card_id__in = s).filter(date__day = now.day, date__year = now.year, date__month = now.month).distinct('card_id').order_by('card_id', 'time') 
    cards = CardLog.objects.filter(id__in = initial).order_by('-time')
    if not loggedin_user.is_superuser:
        cards = cards.filter(cramschool = loggedin_user.cramschool)
    return cards
    # file = open(os.path.join(settings.BASE_DIR, 'attendance', 'logs','scanned_cards.log'), 'r')
    # lines = tail(file,15)
    # return get_cards_not_in_db(lines)
     
def get_cards_not_in_db(vals):
    """
        Filters the card numbers from the logs. 
        Removes duplicate cards from the log and
        returns cards that are not yet in the database.
    """
    values = parse_list(vals)
    # get the cards that are in the database

    cards_in_db = User.objects.filter(card_id__in = values['cards']).values_list('card_id')
    # convert acquired list of tuples into a pure list
    in_db_card_list = [x[0] for x in cards_in_db]
    # get a new list of cards that are not in the database
    to_show = [ x for x in values['columns'] if x[2] not in in_db_card_list ]
    return to_show 

def parse_list(lines, separator = '='):
    """
        Returns a list of list given a list of strings which are separated by a symbol
        Eg.
        
        given ['2020-06-22 = 03:21:48 = PZ010ABCeddeeeee]
        will yield ['2020-06-22', '03:21:48', 'PZ010ABCeddeeeee']

        Args:
                lines(List): the list of strings to be parsed
                separator(character): the separator
        
        Returns:
                Dictionary:
                        columns: a list of lists that was parsed from the initial list of strings
                        cards  : a list of the cards that were retrieved 
                                (used to remove duplicate cards retrieved from the logs and to be used
                                 to check if the cards already exist in the database)
    """
    column = []
    cards = []
    for line in reversed(lines):
        if not line:
            continue
        row = [col.strip() for col in line.split(separator) if col]
        if (row[2] not in cards):
            cards.append(row[2])
            column.append( row )
    return {'columns': column, 'cards': cards}


def tail(f, window=10):
    """
        Returns the last `window` lines of file `f` as a list.

        Args:
                f(file): File whose last (window) lines are to be retrieved
                window(int): The number of last lines from a file to be retrieved
        
        Returns:
                List: of the last (window) lines retrieved
    """
    if window == 0:
        return []

    BUFSIZ = 1024
    f.seek(0, 2)
    remaining_bytes = f.tell()
    size = window + 1
    block = -1
    data = []

    while size > 0 and remaining_bytes > 0:
        if remaining_bytes - BUFSIZ > 0:
            # Seek back one whole BUFSIZ
            f.seek(block * BUFSIZ, 2)
            # read BUFFER
            bunch = f.read(BUFSIZ)
        else:
            # file too small, start from beginning
            f.seek(0, 0)
            # only read what was not read
            bunch = f.read(remaining_bytes)

        # bunch = bunch.decode('SHIFT_JIS')
        data.insert(0, bunch)
        size -= bunch.count('\n')
        remaining_bytes -= BUFSIZ
        block -= 1

    return ''.join(data).splitlines()[-window:]

"""
    =================================
    IMPORT FUNCTIONS
    =================================
"""

def import_users(csv_file, user_group, cramschool_id):
    """
        Used for importing students via CSV files.
        Accepts UTF-8 encoded CSV files

        Args:
                csv_file(File): CSV file to be migrated
        
        Returns:
                boolean: True if the migration is successful
                String: of the error that occured if the migration failed

    """
    logger.info("=" * 20 + " IMPORTING STUDENTS " + "=" * 20)
    start_time = time.time()
    paramFile = io.TextIOWrapper(csv_file, encoding="utf-8")
    rows = csv.DictReader(paramFile)
    logger.info(f"Finished opening file: {time.time() - start_time}")
    start_time = time.time()
    cramschool_instance = CramSchool.objects.get(pk = cramschool_id)
    try: 
        objs = [
                User(
                        id_number = row['id_number'],
                        last_name = row['last_name'] if row['last_name'] != "" else None,
                        first_name = row['first_name'] if row['first_name'] != "" else None,
                        last_name_kana = row['last_name_kana'] if row['last_name_kana'] != "" else None,
                        first_name_kana = row['first_name_kana'] if row['first_name_kana'] != "" else None,
                        year_level = YearLevel.objects.get(pk = row['year_level']) if row['year_level'] != "" else None,
                        birthdate = datetime.datetime.strptime(row['birthdate'], '%m/%d/%Y').date() if row['birthdate'] != "" else None,
                        postal_code = row['postal_code'] if row['postal_code'] != "" else None,
                        address_1 = row['address_1'] if row['address_1'] != "" else None,
                        address_2 = row['address_2'] if row['address_2'] != "" else None,
                        telephone_num = row['telephone_num'] if row['telephone_num'] != "" else None,
                        mobile_num_1 = row['mobile_num_1'] if row['mobile_num_1'] != "" else None,
                        mobile_num_2 = row['mobile_num_2'] if row['mobile_num_2'] != "" else None,
                        is_active = (True if row['is_active'] == 'TRUE' else False),
                        is_superuser = False,
                        is_staff = False,
                        # card_id = row['card_id'],
                        card_id = row['card_id'] if row['card_id'] != "" else None,
                        password = make_password(settings.DEFAULT_PASS),
                        sex = row['sex'] if row['sex'] in ('女', '男', 'なし') else 'なし',
                        school = School.objects.get(pk = row['school'] ) if row['school'] != "" else None,
                        printed_card_id = row['printed_card_id'] if row['printed_card_id'] != "" else None,
                        cramschool = cramschool_instance,
                        username = (str(row['id_number']) + str(cramschool_instance.id)),
                        # username = row['id_number'],
                    )
                    for row in rows
            ]    
        logger.info(f"Finished looping. Duration: {time.time() - start_time}")
        start_time = time.time()
        User.objects.bulk_create(objs)
        if user_group == None:
            student_group = Group.objects.get(name='Students')
        else:
            student_group = Group.objects.get(name=user_group)
        student_group.user_set.add(*objs)
        logger.info(f"Successfully imported data from CSV. Duration: {time.time() - start_time}")
        return True
    except UnicodeDecodeError as e:
        return f"ファイルのエンコーディングはUTF-8であることを確認してください。"
    except KeyError as e:
        print(e)
        return "ヘッダーが完全であることを確認してください。"
    except IntegrityError as e:
        return "CSVの一部のデータはデータベースにすでに存在します。"
    except Exception as e:
        logger.info(f"Error occured while importing data: {e}" )
        return f"Error in importing data: {e}"

def import_holidays(csv_file, flag):
    """
        Used for importing holiday via CSV files.
        Accepts UTF-8 encoded CSV files

        Args:
                csv_file(File): CSV file to be migrated
        
        Returns:
                boolean: True if the migration is successful
                String: of the error that occured if the migration failed

    """
    logger.info("=" * 20 + " IMPORTING HOLIDAYS " + "=" * 20)
    paramFile = io.TextIOWrapper(csv_file, encoding="utf-8")
    holidays = csv.DictReader(paramFile)
    try: 
        list_of_dict = list(holidays)
        objs = [
                Holiday(
                        date = datetime.datetime.strptime(row['date'], '%m/%d/%Y').date(),
                        name = row['name'],
                        remarks = row['remarks']
                    )
                    for row in list_of_dict
            ]    
        if flag:
            Holiday.objects.all().delete()
        Holiday.objects.bulk_create(objs)
        logger.info('Successfully imported data from CSV')
        return True
    except UnicodeDecodeError as e:
        return f"ファイルのエンコーディングはUTF-8であることを確認してください。"
    except KeyError as e:
        return "ヘッダーが完全であることを確認してください。"
    except IntegrityError as e:
        return "CSVの一部のデータはデータベースにすでに存在します。"
    except Exception as e:
        logger.info(f"Error occured while importing data: {e}" )
        return f"データのインポート中にエラーが出ました: {e}"

"""
    =================================
    EXPORT FUNCTIONS
    =================================
"""

def export_attendance(month_year, id):
    """
        Used for exporting a CSV file of a user's attendance records

        Args:
                month_year(datetime): period to export
                id_number(string): ID number of the user whose attendance records are to be exported
        
        Returns:
                file(csv): the csv export of the attendance records

    """
    user = get_user(pk = id)
    attendance_records = get_attendance_records(user, month_year)
    holidays = Holiday.objects.filter(date__month = month_year.month, date__year = month_year.year )
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{month_year.year}{month_year.month}.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)

    # initial header names
    header_names = ['No.','名前','日付','備考']

    # get the maximum rows the user has in that month
    # loop through it
    # m = Attendance.objects.values('date','user').annotate(cnt=Count('id')).filter(user = user, date__year=month_year.year, date__month=month_year.month).aggregate(Max('cnt'))
    # max_recs = list(m.values())[0] if list(m.values())[0] is not None else 1
    # for y in range(max_recs):
    #     header_names.append('入')
    #     header_names.append('出')

    for y in range(5):
        header_names.append('入')
        header_names.append('出')
    
    writer.writerow(header_names)

    # get how many days there are in in the chosen month
    no_of_days = calendar.monthrange(month_year.year,month_year.month)[1]

    for x in range(no_of_days):
        day_recs = attendance_records.filter(date__day=x+1)
        loop_date = datetime.date(month_year.year, month_year.month, x+1)
        
        # id_number, name, date / [No、 名前、日付]
        row = [user.id_number, f"{user.last_name if user.last_name is not None else ''}{user.first_name if user.first_name is not None else ''}",datetime.datetime.strftime(loop_date, "%Y-%m-%d")]
        
        # remarks / 備考
        remarks = constants.days_of_week_abbv[loop_date.weekday()]
        if holidays.filter(date__day = x+1).exists():
            remarks = f"{remarks} - 祝日"
        row.append(remarks)

        # 入・出
        for record in day_recs:
            row.append( f"{record.time_in.hour}:{record.time_in.minute}" if record.time_in is not None else " ")
            row.append( f"{record.time_out.hour}:{record.time_out.minute}" if record.time_out is not None else " ")
        
        writer.writerow(row)

    return response


"""
    =================================
    CARD SCAN FUNCTIONS
    =================================
"""

def scan_card(detected_card,cramschool_sn):
    """
        If the card id detected is not yet in the database, the card's information will be
        logged in the card_scan.log to be used when registering or editing student information.

        If the card is already in the database, it will invoke the do_attendance function.

        Args:   
                detected_card(CardScan): 

        Returns:
                boolean: True if the recording of the card was successful
                         otherwise returns False
    """
    cramschool = CramSchool.objects.get(short_name = cramschool_sn)
    card_exists = User.objects.filter(card_id__iexact = detected_card.cid, cramschool = cramschool).exists()
    if detected_card.is_valid:
        if card_exists:
            result = do_attendance(detected_card)
            if not result:
                logger.info("Attendance was not recorded.")
                return False
        
            # log = f"{detected_card.date} = {detected_card.time} = {detected_card.cid}"
            # # This line records every new card that is detected to the log.
            # # Data from this log is shown in the User Register Page.
            # card_logger.info(log)
            # return True
        card_log = CardLog(card_id = detected_card.cid, date = detected_card.date, time = detected_card.time, cramschool = cramschool).save()
        return True
        
    else:
        logger.info("There are some missing data in the post parameters.")
        return False

"""
    ======================================================================
    FUNCTIONS USED WITH CELERY (files connected with: tasks.py, celery.py)
    NOTE: NO LONGER USED
    ======================================================================
"""

# def get_user_email(request):
#     logger.info("Retrieving user email.")
#     try:
#         user = User.objects.get(pk = request.user.id)
#         validate_email(user.email)
#         return user.email
#     except ValidationError as e:
#         messages.error(request, "プロフィールにメールを追加してください。")
#         raise PermissionDenied()
#     except User.DoesNotExist as e:
#         messages.error(request,"ユーザーが存在していません。")
#         raise PermissionDenied()

# def send_email(subject, message, recipient):
#     send_mail(subject, message, settings.EMAIL_HOST_USER,(recipient,),fail_silently= False)

# def import_users_csv(csv_file, user_group, request):
#     recipient = get_user_email(request)
#     try:
#         paramFile = io.TextIOWrapper(csv_file, encoding="utf-8")
#         rows = csv.DictReader(paramFile)
#         u_rows = list(rows)
#         logger.info(f"u_rows:{len(u_rows)}")
#         tasks.import_users.apply_async(args=[u_rows, user_group, recipient], countdown = 1)
#     except UnicodeDecodeError as e:
#         return f"ファイルのエンコーディングはUTF-8であることを確認してください。"
#     except KeyError as e:
#         return "ヘッダーが完全であることを確認してください。"
#     except Exception as e:
#         logger.info(f"Error occured while importing data: {e}" )
#         return f"データのインポート中にエラーが出ました: {e}"
#     return None


"""
    =========
    TODO: tbd
    NOTE: NO LONGER USED
    =========
"""

# def time_in_teacher(card_scan, user):
#     # TODO: phase out shit

#     try:
#         last_attendance = Attendance.objects.filter(user = user).order_by('-date')
#         if last_attendance.exists():
#             last_attendance = last_attendance.first()
#             date_range = get_date_list(last_attendance.date, card_scan.date)
#             holidays = get_holidays_in_between(last_attendance.date, card_scan.date)
#             fill_in_attendance(date_range, holidays, user)
#         time_in(card_scan, user)
#         return True
#     except Exception as e:
#         logger.info(e)
#         return False

# def get_date_list(start_date, end_date):
#     date_mod = start_date
#     end = end_date - datetime.timedelta(days=1)
#     date_list = []
#     while date_mod < end:
#         date_mod += datetime.timedelta(days=1)
#         date_list.append(date_mod)
#     return date_list

# def fill_in_attendance(date_list, holiday_dates, user):
#     for date in date_list:
#         attendance = Attendance(date = date, time_in = None, time_out = None, user = user)
#         if date.weekday() < 5 and date not in holiday_dates:
#             attendance.remarks = "休み"
#         elif date in holiday_dates:
#             attendance.remarks = "祝日"
#         else:
#             attendance.remarks = constants.days_of_week[date.weekday()]
#         attendance.save()

# def get_holidays_in_between(start_date, end_date):
#     print("getting holidays list")
#     holidays = Holiday.objects.filter(Q(date__gt = start_date) & Q(date__lte = end_date))
#     holiday_dates = [ holiday.date for holiday in holidays ]
#     return holiday_dates


# def export_attendance_1(start_date, end_date, id_number, flag):
#     """
#         flag = indicator if the export to be done is export all 
#     """

#     user = User.objects.get(id_number = id_number)
    
#     if not flag and start_date != "" and end_date != "":
#         attendance_records = Attendance.objects.filter(
#                             Q(date__gte = start_date) & 
#                             Q(date__lte = end_date) & 
#                             Q(user = user)
#                         )
#     elif flag:
#         attendance_records = Attendance.objects.filter(user = user).all()
#     else:
#         raise SuspiciousOperation()
    
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = f'attachment; filename="{user.last_name}{user.first_name}.csv"'
#     response.write(u'\ufeff'.encode('utf8'))
#     writer = csv.writer(response)
#     field_names = ['日付', '入','出', '備考']
#     writer.writerow(field_names)
#     for record in attendance_records:
#         # you can add the remarks here instead or smth lol
#         writer.writerow( [record.date, record.time_in, record.time_out, record.remarks] )
#     return response