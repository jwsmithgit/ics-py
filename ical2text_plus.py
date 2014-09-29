#!/usr/bin/python

from optparse import OptionParser
import fileinput
import sys
from datetime import date
import re

# get start date, end date, and filename from user
def process_input():
	parser = OptionParser()
	parser.add_option("-f", "--file", dest="filename", help="read from *.ics FILE") #metavar="FILE"??
	parser.add_option("-s", "--start", dest="startdate", help="start date for displayed events")
	parser.add_option("-e", "--end", dest="enddate", help="end date for displayed events") 
	parser.add_option("-t", "--tz", dest="timezone", help="universal time zone")
	(options, args) = parser.parse_args()
	#print options
	if (options.filename == None or options.startdate == None or options.enddate == None):
		print("Please format as ./ical2text --file=filename.ics --start=dd/mm/yyyy --end=dd/mm/yyyy --tz=+-d")
		sys.exit()

	# dealing with single values for day and month, make it two digits
	# as well, changing double digit years to 20\d\d
	tok_start = options.startdate.split('/')
	tok_end = options.enddate.split('/')
	if (len(tok_start[0]) == 1):
		day_start = '0' + tok_start[0]
	else:
		day_start = tok_start[0]
	if (len(tok_start[1]) == 1):
		month_start = '0' + tok_start[1]
	else:
		month_start = tok_start[1]
	if (len(tok_start[2]) == 2):
		year_start = '20' + tok_start[2]
	else:
		year_start = tok_start[2]
	if (len(tok_end[0]) == 1):
		day_end = '0' + tok_end[0]
	else:
		day_end = tok_end[0]
	if (len(tok_end[1]) == 1):
		month_end = '0' + tok_end[1]
	else:
		month_end = tok_end[1]
	if (len(tok_end[2]) == 2):
		year_end = '20' + tok_end[2]
	else:
		year_end = tok_end[2]
		
	options.startdate = day_start + '/' + month_start + '/' + year_start
	options.enddate = day_end + '/' + month_end + '/' + year_end

	options.filename = options.filename.split(',')
	
	return options
	
# read the lines of the file place in a 
def read_lines(file_name):
	lines = []
	f = open(file_name, 'r')
	for line in f:
		line = line.strip()
		if (line):
			lines.append(line)
	return lines

# tokenizes all rows in an array given token character, only 1 token
def tokenizer(array, token_char):
	tokenized = []
	for i in range(len(array)):
		split_row = array[i].split(token_char)
		if (len(split_row) != 1):
			tokenized.append(split_row)
		else:
			tokenized[len(tokenized)-1][1] += split_row[0]
	return tokenized

# process each line of the file, get label and data
def process_tok_array(tok_array):
	proc_array = []
	event_data = [0 for x in xrange(5)]
	for i in range(len(tok_array)):
		if (tok_array[i][0] == "DTSTART"):
			event_data[0] = tok_array[i][1]
		elif (tok_array[i][0] == "DTEND"):
			event_data[1] = tok_array[i][1]
		elif (tok_array[i][0] == "RRULE"):
			event_data[2] = tok_array[i][1]
		elif (tok_array[i][0] == "LOCATION"):
			event_data[3] = tok_array[i][1]
		elif (tok_array[i][0] == "SUMMARY"):
			event_data[4] = tok_array[i][1]
		elif (tok_array[i][0] == "END" and tok_array[i][1] == "VEVENT"):
			proc_array.append(event_data[:])
			for element in range(len(event_data)):
				event_data[element] = 0
	return proc_array

# adjust the time of all events according to time zone
def adjust_array(events, timezone):
	# change the from dates
	for event in events:
		# if tz is negative, minus the time
		if (timezone[0] == '-'):
			neg_new_time = int(event[0][9:11]) - int(timezone[1:])
			# if time is less then 0, minus a day
			if (neg_new_time < 0):
				neg_new_time += 24
				if (neg_new_time < 10):
					neg_new_time = "0" + str(neg_new_time)
				else:
					neg_new_time = str(neg_new_time)
				event[0] = re.sub(r"T\d\d", r"T%s" %neg_new_time, event[0])
				new_day = int(event[0][6:8]) - 1
				real_date = make_real_date(int(event[0][0:6]+str(new_day)))
				event[0] = re.sub(r"\d*T", r"%sT" %str(real_date), event[0])
			else:
				if (neg_new_time < 10):
					neg_new_time = "0" + str(neg_new_time)
				else:
					neg_new_time = str(neg_new_time)
				event[0] = re.sub(r"T\d\d", r"T%s" %neg_new_time, event[0])
		# if not negative, add the timezone
		else:	
			if (timezone[0] == '+'):
				pos_new_time = int(event[0][9:11]) + int(timezone[1:])
			else:
				pos_new_time = int(event[0][9:11]) + int(timezone)
			# if hours are past 24(midnight) go to next day
			if (pos_new_time > 23):
				pos_new_time -= 24
				if (pos_new_time < 10):
					pos_new_time = "0" + str(pos_new_time)
				else:
					pos_new_time = str(pos_new_time)
				event[0] = re.sub(r"T\d\d", r"T%s" %pos_new_time, event[0])
				new_day = int(event[0][6:8]) + 1
				real_date = make_real_date(int(event[0][0:6]+str(new_day)))
				event[0] = re.sub(r"\d*T", r"%sT" %str(real_date), event[0])
			else:
				if (pos_new_time < 10):
					pos_new_time = "0" + str(pos_new_time)
				else:
					pos_new_time = str(pos_new_time)
				event[0] = re.sub(r"T\d\d", r"T%s" %pos_new_time, event[0])
	# change all the to dates
	for event in events:
		# if tz is negative, minus the time
		if (timezone[0] == '-'):
			# if time is less then 0, minus a day
			neg_new_time = int(event[1][9:11]) - int(timezone[1:])
			if (neg_new_time < 0):
				neg_new_time += 24
				if (neg_new_time < 10):
					neg_new_time = "0" + str(neg_new_time)
				else:
					neg_new_time = str(neg_new_time)
				event[1] = re.sub(r"T\d\d", r"T%s" %neg_new_time, event[1])
				new_day = int(event[1][6:8]) - 1
				real_date = make_real_date(int(event[1][0:6]+str(new_day)))
				event[1] = re.sub(r"\d*T", r"%sT" %str(real_date), event[1])
			else:
				if (neg_new_time < 10):
					neg_new_time = "0" + str(neg_new_time)
				else:
					neg_new_time = str(neg_new_time)
				event[1] = re.sub(r"T\d\d", r"T%s" %neg_new_time, event[1])
		# if not negative, add the timezone
		else:
			if (timezone[0] == '+'):
				pos_new_time = int(event[1][9:11]) + int(timezone[1:])
			else:
				pos_new_time = int(event[1][9:11]) + int(timezone)
			# if hours are past 24(midnight) go to next day
			if (pos_new_time > 23):
				pos_new_time -= 24
				if (pos_new_time < 10):
					pos_new_time = "0" + str(pos_new_time)
				else:
					pos_new_time = str(pos_new_time)
				event[1] = re.sub(r"T\d\d", r"T%s" %pos_new_time, event[1])
				new_day = int(event[1][6:8]) + 1
				real_date = make_real_date(int(event[1][0:6]+str(new_day)))
				event[1] = re.sub(r"\d*T", r"%sT" %str(real_date), event[1])
			else:
				if (pos_new_time < 10):
					pos_new_time = "0" + str(pos_new_time)
				else:
					pos_new_time = str(pos_new_time)
				event[1] = re.sub(r"T\d\d", r"T%s" %pos_new_time, event[1])

	return events
				

# copy all events with in bounds dates into new array, return new array
def remove_out_of_date(events, user_start, user_end):
	in_user_bounds = [] # will only store events that are in bound or have frequencies in bound
	user_start_cmp = user_start[6:] + user_start[3:5] + user_start[:2] # user input start ymd
	user_end_cmp = user_end[6:] + user_end[3:5] + user_end[:2] #user input end ymd

	for i in range(len(events)):
		# events end on same day if, so we dont need end date for comparing
		event_start_cmp = events[i][0][:8]
		# if the events starts after users end date, it is not in bounds
		if (event_start_cmp > user_end_cmp):
			continue
		# if the events has a weekly frequency, the frequency will last longer then the event end date
		# and if the frequency ends before the user start date, it is not in bounds
		elif (events[i][2] != 0):
			event_freq_end_cmp = events[i][2][18:26]
			if (event_freq_end_cmp < user_start_cmp):
				continue
		# if no frequency check the end date against against user start date, if earlier, not in bounds
		elif (event_start_cmp < user_start_cmp and events[i][2] == 0):
			continue
		#must be in bounds if here, move to new array
		in_user_bounds.append(events[i][:])
	return in_user_bounds

# process data if there is a weekly flag
# returns new array that:
# has all events without frequencies (removed out of bound ones before)
# has all events with frequencies that are in bounds
# events that are not in bounds with frequencies in bounds will not be in the array
# output will have all data but will not be sorted
def process_weekly(events, user_start, user_end):
	user_start_cmp = user_start[6:] + user_start[3:5] + user_start[:2] # user input start date in ymd format
	user_end_cmp = user_end[6:] + user_end[3:5] + user_end[:2] # user input end date in ymd format
	in_user_bounds = [] # will only store events that are in bounds after frequencies calculated
	in_bound_repeat = [0 for x in xrange(5)] # will hold event that gets appended
	for i in range(len(events)):
		# if frequency is 0, it must be in bounds, copy it
		if (events[i][2] == 0):
			in_user_bounds.append(events[i][:])
			continue
		# frequency is not 0 and the event or the frequency appears in bounds
		curr_date = events[i][0][:8]
		# find frequencies until user end date or event end date
		while (curr_date <= user_end_cmp and curr_date <= events[i][2][18:26]):
			# if the date is after the user start date it is in bounds
			if (user_start_cmp <= curr_date):
				new_start_event = curr_date + events[i][0][8:]
				new_end_event = curr_date + events[i][1][8:]
				in_bound_repeat = [new_start_event, new_end_event, events[i][2], events[i][3], events[i][4]]
				in_user_bounds.append(in_bound_repeat[:])
			curr_date = int(curr_date) + 7
			curr_date = make_real_date(curr_date)
	return in_user_bounds

# takes yyyymmdd and turns it into a real date if over day or month bounderies				
def make_real_date(date_ymd):
	year = int(str(date_ymd)[:4])
	month = int(str(date_ymd)[4:6])
	day = int(str(date_ymd)[6:])
	
	# January to February
	if (month == 1 and day > 31):
		day = day % 31
		month += 1
	# Jan to Dec
	elif (month == 1 and day < 1):
		day += 31
		month = 12
		year -= 1
	# February to March
	if (month == 2 and day > 28):
		day = day % 28
		month += 1
	# Feb to Jan
	elif (month == 2 and day < 1):
		day += 31
		month -= 1
	# March to April
	if (month == 3 and day > 31):
		day = day % 31
		month += 1
	# Mar to Feb
	elif (month == 3 and day < 1):
		day += 28
		month -= 1
	# April to May
	if (month == 4 and day > 30):
		day = day % 30
		month += 1
	# Apr to Mar
	elif (month == 4 and day < 1):
		day += 31
		month -= 1
	# May to June
	if (month == 5 and day > 31):
		day = day % 31
		month += 1
	# May to Apr
	elif (month == 5 and day < 1):
		day += 30
		month -= 1
	# June to July
	if (month == 6 and day > 30):
		day = day % 30
		month += 1
	# June to May
	elif (month == 6 and day < 1):
		day += 31
		month -= 1
	# July to August
	if (month == 7 and day > 31):
		day = day % 31
		month += 1
	# Jul to Jun
	elif (month == 7 and day < 1):
		day += 30
		month -= 1
	# August to September
	if (month == 8 and day > 31):
		day = day % 31
		month += 1
	# Aug to Jul
	elif (month == 8 and day < 1):
		day += 31
		month -= 1
	# September to October
	if (month == 9 and day > 30):
		day = day % 30
		month += 1
	# Sept to Aug
	elif (month == 9 and day < 1):
		day += 31
		month -= 1
	# October to November	
	if (month == 10 and day > 31):
		day = day % 31
		month += 1
	# Oct to Sept
	elif (month == 10 and day < 1):
		day += 30
		month -= 1
	# November to December
	if (month == 11 and day > 30):
		day = day % 30
		month += 1
	# Nov to Oct
	elif (month == 11 and day < 1):
		day += 31
		month -= 1
	# December to January
	if (month == 12 and day > 31):
		day = day % 30
		month = 1
		year += 1
	# Dec to Nov
	elif (month == 12 and day < 1):
		day += 30
		month -= 1
	
	#convert ints to strings
	year = str(year)
	if (month < 10):
		month = '0' + str(month)
	else:
		month = str(month)
	if (day < 10):
		day = '0' + str(day)
	else:
		day = str(day)	
	return year + month + day

# find the day of the week given a date
def find_weekday(date_ymd):
	date_day = date(int(str(date_ymd)[:4]), int(str(date_ymd)[4:6]), int(str(date_ymd)[6:]))
	return weekday_int_to_str(date_day.weekday())

# changes integer representation of a weekday to a string
# 0 is Monday 6 is Sunday
def weekday_int_to_str(weekday_num):	
	# Monday
	if (weekday_num == 0):
		return 'Monday'
	# Tuesday
	elif (weekday_num == 1):
		return 'Tuesday'
	# Wednesday
	elif (weekday_num == 2):
		return 'Wednesday'
	# Thursday
	elif (weekday_num == 3):
		return 'Thursday'
	# Friday
	elif (weekday_num == 4):
		return 'Friday'
	# Saturday
	elif (weekday_num == 5):
		return 'Saturday'
	# Sunday
	elif (weekday_num == 6):
		return 'Sunday'
	return None

# changes integer representation of a month to a string
# 1 is January 12 is December
def find_month(month_num):
	# January
	if (month_num == 1):
		return 'January'
	# February
	elif (month_num == 2):
		return 'February'
	# March
	elif (month_num == 3):
		return 'March'
	# April
	elif (month_num == 4):
		return 'April'
	# May
	elif (month_num == 5):
		return 'May'
	# June
	elif (month_num == 6):
		return 'June'
	# July
	elif (month_num == 7):
		return 'July'
	# August
	elif (month_num == 8):
		return 'August'
	# September
	elif (month_num == 9):
		return 'September'
	# October
	elif (month_num == 10):
		return 'October'
	# November
	elif (month_num == 11):
		return 'November'
	# December
	elif (month_num == 12):
		return 'December'
	return None

# prints out all events in range
def print_events(events):
	# used to check if dates are same to not print out header
	last_date = ""
	current_date = ""
	for event in events:
		date_ymd = event[0][:8]
		
		last_date = current_date
		current_date = date_ymd
		not_same_day = last_date != current_date
		
		# printing new line
		if (not_same_day and last_date != ""):
			print
		
		first_line = find_weekday(date_ymd) + ', ' + date_ymd[6:] + ' ' + find_month(int(date_ymd[4:6])) + ' ' +  date_ymd[:4]
		# check if event is on same day as the last
		if (not_same_day):
			print first_line

		second_line = ''
		for i in range(len(first_line)):
			 second_line += '-'
		
		if (not_same_day):
			print second_line

		third_line = event[0][9:13] + ' to ' + event[1][9:13]
		if (event[0][6:8] != event[1][6:8]):
			third_line += '+'
		third_line += ': '
		if (event[4] != 0):
			third_line += event[4]
		third_line += ' '
		if (event[3] !=0):
			third_line += '[' + event[3] + ']'
		print third_line
	
def main():
	options = process_input()
		
	# data stored as array [start time, end time, weekly, location, description] in an array
	data_lines = []
	for filename in options.filename:
		data_lines += (read_lines(filename))
	labels_data = tokenizer(data_lines, ':')
	events = process_tok_array(labels_data)
	events_adjusted_time = adjust_array(events, options.timezone)
	events_in_bounds = remove_out_of_date(events_adjusted_time, options.startdate, options.enddate)
	events_final = process_weekly(events_in_bounds, options.startdate, options.enddate)
	# sort by start date then description
	events_final.sort(key = lambda x: (x[0],x[4]))
	
	print_events(events_final)
	
if __name__ == "__main__":
	main()
