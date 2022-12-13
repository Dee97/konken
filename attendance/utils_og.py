from datetime import datetime, timedelta
from calendar import HTMLCalendar
from .models import Attendance, User
from bot import constants

class Calendar(HTMLCalendar):

	def __init__(self, year=None, month=None):
		self.year = year
		self.month = month
		super(Calendar, self).__init__()

	def formatmonthname(self, theyear, themonth, withyear=True):
		if withyear:
			s = '%s %s' % (f'{themonth}月', f'{theyear}年')
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
	def formatday(self, day, attendance, holiday):
		records = attendance.filter(date__day=day)
		holidays = holiday.filter(date__day=day)
		d = ''

		for h in holidays:
			d += f'<li class="bg-info text-light p-1">{ h.name }</li>'

		for record in records:
			if record.time_in is not None:
				d += f'<li class="text-success">{ record.time_in.strftime("%H:%M")}</li>'
			if record.time_out is not None:
				d += f'<li class="text-danger">{ record.time_out.strftime("%H:%M")}</li>'

		if day != 0:
			return f"<td><span class='date'>{day}</span><ul>{d}<ul></td>"
		return '<td></td>'

	# formats a week as a tr 
	def formatweek(self, theweek, attendance, holiday):
		week = ''
		for d, weekday in theweek:
			week += self.formatday(d, attendance, holiday)
		return f'<tr> {week} </tr>'

	# formats a month as a table
	# filter attendance by year and month
	def formatmonth(self, attendance_records, holiday = None, withyear=True):
		attendance = attendance_records.filter(date__month=self.month, date__year=self.year)
		holidays = holiday.filter(date__month=self.month, date__year=self.year)

		cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
		cal += f'{self.formatmonthname(self.year, self.month,withyear=withyear)}\n'
		cal += f'{self.formatweekheader()}\n'
		for week in self.monthdays2calendar(self.year, self.month):
			cal += f'{self.formatweek(week, attendance, holidays)}\n'
		return cal