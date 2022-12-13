from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, AbstractBaseUser
import datetime
from bot import constants as consts
from django.db.models import Max
from django.core.exceptions import ValidationError


class CramSchool(models.Model):
    line_channel_access_token = models.CharField(max_length = 200, blank = True, null = True, verbose_name="Line Channel Access Token")
    line_channel_secret = models.CharField(max_length = 200, blank = True, null = True, verbose_name="Line Channel Secret")
    name = models.CharField(max_length = 50, blank = True, null = True, verbose_name="塾名")
    address = models.CharField(max_length = 50, blank = True, null = True, verbose_name="塾住所")
    short_name = models.CharField(unique = True, max_length = 50, blank = True, null = True, verbose_name="塾short name")
    contact_number = models.CharField(max_length = 50, blank = True, null = True, verbose_name="塾連絡先")
    default_greeting = models.CharField(max_length = 300, blank = True, null = True, verbose_name="Default Greeting")
    rich_menu_img = models.ImageField(upload_to='images/', blank = True, null = True)
    failed_registration = models.CharField(max_length = 300, blank = True, null = True, verbose_name="Failed Registration Message")

    class Meta:
        verbose_name_plural = "塾 - Cram School"

    def __str__(self):
        return f"{self.name}" 

class SchoolDivision(models.Model):
    division = models.SmallIntegerField(primary_key=True, verbose_name="学校区分")
    division_name = models.CharField(max_length = 50, blank = False, null = False, verbose_name="学校区分名")

    def __str__(self):
        return f"{self.division} {self.division_name}" 

    class Meta:
        verbose_name_plural = "学校区分　- School Division" 

class YearLevel(models.Model):

    year_level = models.SmallIntegerField(primary_key=True, verbose_name="学年CD")
    level_division = models.ForeignKey(SchoolDivision, null = False, on_delete = models.SET_DEFAULT, default = None, related_name = "学年_区分")
    year_level_name1 = models.CharField(max_length = 50, blank = True, null = True, verbose_name="学年名１")
    year_level_name2 = models.CharField(max_length = 50, blank = True, null = True, verbose_name="学年名2")
    year_level_name3 = models.CharField(max_length = 50, blank = True, null = True, verbose_name="学年名3")

    def __str__(self):
        return f"{self.year_level_name1}"

    class Meta:
        verbose_name_plural = "学年　- Year Level" 

class School(models.Model):    
    school_code = models.IntegerField(primary_key=True, verbose_name="学校CD") 
    school_name = models.CharField(max_length = 100, blank = False, null = False, verbose_name="学校名")
    level_division = models.ForeignKey(SchoolDivision, null = False, on_delete = models.SET_DEFAULT, default = None, related_name = "学校_区分")
    cramschool = models.ForeignKey(CramSchool, null = True, on_delete = models.SET_DEFAULT, default = None, related_name = "学校の塾")

    def __str__(self):
        return f"{self.school_name} {self.level_division.division_name}"

    class Meta:
        unique_together = ['school_code', 'cramschool']

    class Meta:
        verbose_name_plural = "学校　- School" 

    def save(self, *args, **kwargs):
        if self.school_code is None:
            last_id = School.objects.aggregate(Max('school_code'))['school_code__max']
            self.school_code = last_id + 1
        return super(School, self).save(*args, **kwargs)

class User(AbstractUser):

    sex = models.CharField(
        max_length = 3,
        choices = consts.SEX_CHOICES,
        default = consts.UNSURE,
        verbose_name = "性別"
    )

    first_name = models.CharField(max_length = 100, null = True, blank = True, verbose_name="名")
    last_name = models.CharField(max_length = 100, null = True, blank = True, verbose_name="姓")
    username = models.CharField(max_length = 150, null = False, unique = True, verbose_name="ユーザ名")
    id_number = models.CharField(max_length = 100, null = True, blank = True, verbose_name="ID番号")
    line_userid = models.CharField(max_length = 100, null = True, blank = True, unique = True, verbose_name="LINEユーザID番号")
    
    line_username = models.CharField(max_length = 50, blank = True, null = True, verbose_name="LINEユーザ名")
    birthdate = models.DateField(blank = True, null = True, verbose_name="生年月日")
    first_name_kana = models.CharField(max_length = 100, null = True, blank = True, verbose_name="名かな")
    last_name_kana = models.CharField(max_length = 100, null = True, blank = True, verbose_name="姓かな")
    # move year level to a student details if there are more details that are exclusively for students
    # year_level = models.SmallIntegerField(blank = True, null = True, verbose_name="学年")
    
    postal_code = models.CharField(max_length = 50, blank = True, null =True, verbose_name="郵便番号")
    address_1 = models.CharField(max_length = 100, blank = True, null = True, verbose_name="住所１")
    address_2 = models.CharField(max_length = 100, blank = True, null = True, verbose_name="住所２")
    telephone_num = models.CharField(max_length = 50, blank = True, null = True, verbose_name="電話番号")
    mobile_num_1 = models.CharField(max_length = 100, blank = True, null = True, verbose_name="携帯番号１")
    mobile_num_2 = models.CharField(max_length = 100, blank = True, null = True, verbose_name="携帯番号2")
    #USERNAME_FIELD = 'email'
    email = models.EmailField(null = True, blank = True, verbose_name = "メールアドレス")

    year_level = models.ForeignKey(YearLevel, null = True, on_delete = models.SET_DEFAULT, default = None, related_name = "生徒学年", verbose_name="生徒学年")
    school = models.ForeignKey(School, null = True, on_delete = models.SET_DEFAULT, default = None, related_name = "生徒学校", verbose_name="生徒学校")
    # serial number (the id of the card when you scan it) /　カードをかざすとのナンバー
    card_id = models.CharField(max_length = 100, blank = True, null = True, verbose_name="カードID・シリアルナンバー")
    # card number printed on the card itself / カードに印刷したナンバー
    printed_card_id = models.CharField(max_length = 10, blank = True, null = True, unique = True, verbose_name="印刷したカードID")

    cramschool = models.ForeignKey(CramSchool, null = True, on_delete = models.SET_DEFAULT, default = None, related_name = "塾")


    REQUIRED_FIELDS = []

    def __str__(self):
        return (f"{self.first_name}{self.last_name} - {self.line_username}")

    def get_recipients(self):
        return PushRecipients.objects.filter(trigger=self)

    class Meta:
        unique_together = ['id_number', 'cramschool']

    class Meta:
        verbose_name_plural = "ユーザ - Users" 

    def save(self, *args, **kwargs):
        if self.id_number is not None:
            self.id_number = self.id_number.zfill(7)
        return super(User, self).save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.cramschool is not None and self.card_id is not None:
            check_card = User.objects.filter(cramschool = self.cramschool, card_id = self.card_id)
            if check_card.exists():
                raise ValidationError( {'card_id': 'このカードIDはすでに存在します。'} )

class Attendance(models.Model):
    date = models.DateField(blank=True)
    time_in = models.TimeField(blank=True, null=True)
    time_out = models.TimeField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    remarks = models.CharField(max_length = 100, blank = True, null = True)

    class Meta:
        unique_together = ['date', 'user', 'time_in']

    def __str__(self):
        return f"{self.date} - {self.user.last_name} {self.user.first_name}" 

    class Meta:
        verbose_name_plural = "履歴　- Attendance"    


class Answer(models.Model):
    """
        NOTE: No longer used
        Associated with a Question object
    """
    answer = models.TextField()
    recipient_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.answer

class Question(models.Model):
    """
        NOTE: No longer used but can be used if you want the bot to be able to answer questions
    """
    q_type = models.SmallIntegerField() 
    keyword = models.CharField(max_length=300)  
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)


    def __str__(self):
        return self.keyword

class PushRecipients(models.Model):
    """
        Associates a user (Student) with another user
        Used in Line
        The recipient user is the one who accesses the trigger 
        user's details (e.g. attendance records) via LINE bot
    """
    trigger = models.ForeignKey(User, null=True, on_delete=models.SET_DEFAULT, default=None, related_name="trigger_user")
    recipient = models.ForeignKey(User, null=True, on_delete=models.SET_DEFAULT, default=None, related_name="recipient_user")

    class Meta:
        unique_together = ['trigger', 'recipient']

    def __str__(self):
        return f"Student: {self.trigger.first_name}{self.trigger.last_name} {self.trigger.line_username} - Recipient: {self.recipient.first_name}{self.recipient.last_name} {self.recipient.line_username}"

    class Meta:
        verbose_name_plural = "Push Recipients"

class Holiday(models.Model):
    date = models.DateField(blank = False, null = False)
    name = models.CharField(max_length = 50, null = False, blank = False)
    remarks = models.CharField(max_length = 100, null = True, blank = True)

    class Meta:
        unique_together = ['date', 'name']
        verbose_name_plural = "祝日 - Holidays"

class WeekDays(models.Model):
    """
        To be used with the Subjects.
        NOTE: NOT YET USED
    """
    day = models.CharField(max_length=10, unique = True)

class Subject(models.Model):
    """
        NOTE: NOT YET USED
    """
    name = models.CharField(max_length = 50, null = False, blank = False)
    from_time = models.TimeField(blank=True, null=True)
    to_time = models.TimeField(blank=True, null=True)
    days = models.ManyToManyField(WeekDays)
    teacher = models.ForeignKey(User, null=True, on_delete=models.SET_DEFAULT, default=None, related_name="teacher")
    room = models.CharField(max_length = 20, null = True, blank = True)

    class Meta:
        unique_together = ['name', 'from_time', 'to_time', 'room']

class CardLog(models.Model):
    """
        showing the cards that have been scanned
    """
    card_id = models.CharField(max_length = 100, blank = True, null = True, verbose_name="カードID")
    date = models.DateField(blank = False, null = False)
    time = models.TimeField(blank=True, null=True)
    cramschool = models.ForeignKey(CramSchool, null = True, on_delete = models.SET_DEFAULT, default = None, related_name = "カード塾") 

    def __str__(self):
        return f"{self.date} {self.time} - {self.card_id}"

class CardScan:
    """
        A class not in the database used to handle data for cards that are scanned.
    """

    def __init__(self, tid, cid, type, time_info, status):
        self.tid = tid
        self.cid = cid
        self.type = type
        self.time_info = time_info
        self.status = status

    def convert_date(self):
        return datetime.datetime.strptime(self.time_info, "%Y%m%d%H%M%S")

    @property
    def time(self):
        return self.convert_date().time()

    @property
    def date(self):
        return self.convert_date().date()

    @property
    def is_valid(self):
        return not any(k is None or k == '' for k in (self.cid, self.time_info))

    
    def __str__(self):
        if self.is_valid:
            return f"card id: {self.cid}\ndate: {self.date}\ntime: {self.time}"
        else:
            return "Missing values."
    
