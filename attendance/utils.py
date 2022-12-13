from datetime import datetime, timedelta
from calendar import HTMLCalendar
from .models import Attendance, User
from bot import constants

"""
    Class used to display a calendar-like display for a user's attendance record
    but this time in LIST FORM
    utils_og.py shows a user's attendance record in a literal calendar format
"""
class Calendar(HTMLCalendar):

    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    def formatmonthname(self, theyear, themonth, withyear=True):
        if withyear:
            s = '%s %s' % (f'{theyear}年', f'{themonth}月')
        else:
            s = '%s' % f'{themonth}月'
        return '<tr><th colspan="7">%s</th></tr>' % (s)

    def formatweekday(self, day):
        """
        Return a weekday name as a table header.
        """
        return '<th>%s</th>' % (constants.days_of_week_abbv[day])

    # formats a day as a td
    # filter events by day
    def formatday(self, day, attendance, holiday, weekday):
        records = attendance.filter(date__day=day)
        holidays = holiday.filter(date__day=day)
        d = ''
        hol = ''

        for h in holidays:
            hol = f'<li class="p-1">{ h.name }</li>'

        for record in records:
            if record.time_in is not None:
                d += f'<li class="text-success">{ record.time_in.strftime("%H:%M")}</li>'
            if record.time_out is not None:
                d += f'<li class="text-danger">{ record.time_out.strftime("%H:%M")}</li>'

        if day != 0:
            return f"<tr><td><span class='d-none d-sm-inline'>{self.year}年</span>{self.month}月{day}日</td><td>{constants.days_of_week_abbv[weekday]}</td><td><ul>{d}<ul></td><td class='d-none d-sm-table-cell'>{hol}</td></tr>"
        return '<tr></tr>'

    # formats a week as a tr 
    def formatweek(self, theweek, attendance, holiday):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, attendance, holiday, weekday)
        return f'{week}'

    # formats a month as a table
    # filter attendance by year and month
    def formatmonth(self, attendance_records, holiday = None, withyear=True):
        attendance = attendance_records.filter(date__month=self.month, date__year=self.year)
        holidays = holiday.filter(date__month=self.month, date__year=self.year)
        cal = f'<h4 class="text-center text-info mt-3">{self.formatmonthname(self.year, self.month,withyear=withyear)}</h4>'
        cal += f'<table class="table table-hover col-12 mx-auto" cellspacing="0" style="table-layout:fixed;">'
        cal += f'<tr> <th>日付</th><th>曜日</th><th>レコード</th><th class="d-none d-sm-table-cell">備考</th>'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, attendance, holidays)}\n'
        return cal