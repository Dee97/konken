"""
    USED IN THE CALENDAR AND ATTENDANCE EXPORT CSV
"""

days_of_week = ("月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日")
days_of_week_abbv = ("月", "火", "水", "木", "金", "土", "日")

"""
    USED IN THE BOT
"""
stud_id_len = 7

"""
    ===================
    TEXT IN THE BUBBLES
    ===================
"""

b_birthday = "生徒様の生年月日を入力してください。"

failed_registration = "もうしわけございません、登録ができませんでした。\n大変お手数ですが、下記までお電話ください。\n06-6672-1509 (平日: 10:00～22:00)\n\nご協力ありがとうございました。"

successful_registration = "登録が完了しました！\nご協力ありがとうございました。\n\n今後ともよろしくおねがいします！ (^^)/"
account_exists = "すでに登録済みのアカウントです。"

token_expiration = "アクセストークンの有効期限が切れています。konken botでもう一度「履歴」メニューをタップしてください。"

register_greeting = "はじめまして、塾のkonken Botです！konken for Line に登録しますか？"
not_register = "ご利用ありがとうございました。\nまたのお越しをお待ちしています。\n　(^^)/"

follow_event_greeting = "塾のkonken Botです！私を追加してくれてありがとう～"

choose_from_menu = "メニューから選択してください。"

not_now = "いいえ"

"""
    ====================
    USED IN THE DATABASE
    ====================
"""

FEMALE = '女'
MALE = '男'
UNSURE = 'なし'

SEX_CHOICES = (
        (FEMALE, FEMALE),
        (MALE, MALE),
        (UNSURE, UNSURE),
    )


# year level dictionaries

elementary = dict([
    (1,1),
    (2,2),
    (3,3),
    (4,4),
    (5,5),
    (6,6),
])

middle = dict([
    (1,7),
    (2,8),
    (3,9)
])

high = dict([
    (1,10),
    (2,11),
    (3,12)
])