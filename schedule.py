#!/home/aisik/anaconda3/bin/python

from datetime import datetime, timedelta, date
import pytz
from random import choice
import pandas as pd
import numpy as np
import re
from collections import namedtuple
from time import sleep
#Data -----------------------------------------------------------------
months_long = ["january",
               "february",
              'march',
              'march',
              'april',
              'april',
              'may',
              'june',
              'july',
              'august',
              'september',
              'october',
              'november',
              'december']

months_short = ["jan",
                "feb",
                'mar',
                'march',
                'april',
                'april',
                'may',
                'june',
                'july',
                'aug',
                'sept',
                'oct',
                'nov',
                'dec']

short_to_long = dict(zip(months_short,months_long))


months_to_num = dict(zip(months_long,range(1,13)))
num_to_months = dict(zip(range(1,13),months_long))

days_map={
    "mon":"monday",
    "tues": "tuesday",
    "tue" : 'tuesday',
    "wed": "wednesday",
    "thurs": "thursday",
    "thur" : 'thursday',
    "fri": "friday",
    "sat": "saturday",
    "sun": "sunday"
    }

day_to_num= {
    "monday":0,
    "tuesday":1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
}

num_to_day = {
    0:  "Monday",
    1: "Tuesday",
    2:  "Wednesday",
    3:  "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}



#-----------------------------------------------------------------------
class Scheduler:
    """This objects provides a schedule based on a set of rules
    Eg.
    1. object availability for a specific date
    2. object preference for a specific day within the periond


    Inputs
    ------
    st_period:  The date for the start of a new cycle
    periods:     How many days in  the cycle
    """
    _daysofweek= {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday"
    }


    def __init__(self, st_period, periods):
        """
        st_period = start of cycle
        end_period = end of end of cycle
        """
        assert type(st_period) == datetime, "st_period has to be a date/datetime object"
        self.final_sched = {}
        self._scheduled = set()
        self.start = st_period
        self.periods = periods
        self.dates = pd.date_range(self.start, periods = self.periods, freq = "D").date
        self.dates = list(self.dates)
    def schedule(self, spreadsheet, sch_type = 'cook'):

        """
        SpreadSheet object or spreadsheet-like object that contains
        names of persons with their corresponding away dates, preferred days
        of cooking and preferred days of kitchen helping.
        It could also be a dictionary with the key being the names of persons as
        keys and the remaining information packed into a namedtuple.

        sch_type = 'cook', 'kitchen_help'
        """
        assert len(spreadsheet.record) == self.periods, "Period must be equal"+\
        " to the total number people to be scheduled."
        assert sch_type == 'cook' or sch_type == 'kitchen_help', "sch_type must"+\
        " be either 'cook' or 'kitchen_help' "

        # removing people who may not be available during schedule period
        absent_names = []
        for name in spreadsheet.record:
            absent_dates = [dat for dat in\
             spreadsheet.record[name]['away'] if dat in self.dates]  #use intersection operation
            if len(absent_dates) >= self.periods- 1:
                self.dates.pop()
                absent_names.append(name)

        print('absent folks:  ',absent_names)

        for name in absent_names:
            spreadsheet.remove_record(name)
        #done removing people absent-----------------------------
        #--------diagnosing record of the spreadsheet object-----
        # print(spreadsheet.record.keys())
        # sleep(10)

        ##### sorting list to have people not available first#############
        not_available = []
        available = []
        for name in spreadsheet.record:
            away = set(spreadsheet.record[name]['away'])
            if len(away.intersection(self.dates)) != 0:
                not_available.append(name)
            else:
                available.append(name)
        names = not_available + available
        print("May be out during schedule period: ", not_available)


        # final schedule database
        self.final_sched = dict(zip(self.dates,['' for i in range(len(self.dates))]))


        for date in self.dates:
            #Checking for availability of spot--------------
            try:
                if len(self.final_sched[date]) != 0:
                    print("checking for availability...")

                    raise SpotTaken("Sorry spot is taken")
            except SpotTaken:
                continue

            #np.random.shuffle(names)
            for person in names:
                #np.random.shuffle(names)   #shuffle names
                print("checking date {0} against {1}".format(date,person))

                if sch_type == 'cook':
                    is_pref = spreadsheet.is_pref(person, self._daysofweek[date.weekday()])
                else:
                    print('number of busy_kh, ',len(spreadsheet.record[person]['preferred_kh']) )
                    if len(spreadsheet.record[person]['preferred_kh']) == 0:
                        is_pref = spreadsheet.is_pref(person, self._daysofweek[date.weekday()])
                    else:
                        is_pref = spreadsheet.is_pref_kh(person, self._daysofweek[date.weekday()])

                print(person," availabilty: {}".format( not (spreadsheet.is_away(person, date) or is_pref)))

                if spreadsheet.is_away(person, date) or is_pref :
                    continue

                if person not in self.final_sched.values():
                    self.final_sched[date] = person
                    self._scheduled.add(person)
                    print(person,' is scheduled')
                    break
                else:
                    continue



        print("scheduled folks: ",self._scheduled)
        #Randomly assigning people not assigned yet
        try:
            notscheduled = [name for name in spreadsheet.record.keys() if name not in self._scheduled]
            print('Not yet scheduled: ', notscheduled)
            if len(notscheduled) != 0:
                raise NotScheduled()
        except NotScheduled:
            for date, person in self.final_sched.items():
                if len(person) == 0:
                    randomperson = choice(notscheduled)
                    self.final_sched[date] = randomperson
                    notscheduled.remove(randomperson)

    @property
    def table(self):
        return self.final_sched

    def __repr__(self):
        return "Schedule({0},{1})".format(self.start, self.periods)

    def __str__(self):
        if (self.final_sched) == 0:
            return self.__repr__()

        print("dates\t\t\t\t",'People')
        print("-"*40)
        for date, person in self.final_sched.items():
            print("{0}\t\t\t\t{1}".format(date.isoformat(), person))
        return ''


# Spreadsheet----------------------------------------------

class SpreadSheet:
    """
    This is an object that contains record of names with their corresponding
    away dates and preferred days
    """
    _daysofweek= {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday"
    }

    def __init__(self):
        self._record = {}
        self.data = None

    def put_record(self, name, preferred, away):
        """
        name = name of a person: must be a string
        preferred = a list of preferred days
        away = list of away dates
        """
        answered = ''

        try:
            if name in self._record:
                while not answered:
                    answered = input("Already exist: Do you want to replace?y/n:\t")
                if answered == "y":
                    self._record[name]["preferred"]= preferred
                    self._record[name]["away"] = away
                else:
                    raise DontOverride("Don't override the record")

            self._record[name] = {"preferred": preferred, "away": away}

        except DontOverride:
            return "not overriden"

    @property
    def record(self):
        return self._record


    def remove_record(self, name):
        try:
            del self._record[name]
        except KeyError:
            return "no such record exists"

    def is_away(self, name, date):
        """Check availability of a person"""
        if date in self.record[name]["away"]:
            return True
        return False

    def is_pref(self, name, day):
        """Checks for preferred day for cooking"""

        if day in self.record[name]["preferred"]:
            return True
        return False

    def is_pref_kh(self, name, day):
        """Checks for preferred day for kitchen helping"""
        if day in self.record[name]['preferred_kh']:
            return True
        return False

    def get_data(self , url):
        """takes url then downloads data"""
        url_parts = url.split("#")    #spliting url by #
        url = url_parts[0].replace("edit", "export?") + url_parts[1] + "&format=csv" # parsing url
        data = pd.read_csv(url)   #reading in data
        data.fillna('', inplace = True)   # filling missing data
        data.columns = ["Name", 'To', 'From', 'busy_day','busy_kh','comment']
        self.data = data

    def parse_days(self,days):
        """Takes a list of days and parse it to a long version
        e.g :
        mon = monday
        tues = tuesday
        return parse list of days
        """
        assert type(days) == list, 'days must be a list'
        days = [day.lower() for day in days]
        length_one = len(days[0])
        length = len(days)

        if length == 1 and 3<= length_one <=5:
            return [days_map[days[0]]]

        elif length == 1 and length_one> 5:
            return days

        else:
            for i,day in enumerate(days):
                day = day.strip()
                if 3<=len(day)<=5:
                    days[i] = days_map[day]
                else:
                    pass
            return days

    def parse_month(self,month):
        """Converts months to integers
        eg:
        January = 1
        February = 2 etc.
        """

        month = month.lower()
        length = len(month)
        if 3<= length <=5 :
            return months_to_num[short_to_long[month]]
        return months_to_num[month]

    def expand_day(self, From ='monday', To  ='sunday'):
        """Takes to separate days of the week and expands it
        e.g:
        ['monday', 'tuesday',...]
        """

        From = day_to_num[From.lower()]
        To = day_to_num[To.lower()]
        return [num_to_day[i] for i in range(From, To+1)]

    #named tuple object -----------------------------------------
    Observation = namedtuple("Observation", 'Name From To Busy_day Busy_kh')
    # Processing of observation --------------------------------------

    def obs_generator(self):
        """Takes data and reads each record"""

        n = self.data.shape[0]
        try:
            ndata = self.data.drop('comment', axis = 1)
        except ValueError:
            ndata = self.data

        for i in range(n):
            name, fr, to, busy_day, busy_kh = ndata.iloc[i,].values
            if 'week' in busy_day.lower():   # parse sentence containing 'weekday'
                busy_day = 'mon-fri'
            if 'week' in busy_kh.lower():
                busy_kh = 'mon-fri'
            yield self.Observation(name, fr, to, busy_day, busy_kh)

    def parse_list_days(self, days = ''):
        """Takes a string of days separated by ',', '-', words
         etc and return a list of parse days
        """
        if ',' in days and 'and' not in days:
            busy_day = days.split(',')
            return self.parse_days(busy_day)

        elif '-' in days:
            busy_day = days.split('-')
            busy_day = self.parse_days(busy_day)
            return self.expand_day(busy_day[0],busy_day[1])

        elif "and" in days and ',' in days:
            out = []
            busy_day = days.split(",")
            busy_day = [x.split('and') for x in busy_day]
            for ls in busy_day:
                out.extend(ls)
            busy_day = out
            return self.parse_days(busy_day)

        else:
            return self.parse_days([days])

    def parse_observation(self, obs = ''):

        year = datetime.now().year
        mpat = r'[\d]+'
        monthpat = r'[A-Za-z]+'
        mpat = re.compile(mpat)
        monthpat = re.compile(monthpat)

        # try to extract month  and day from string
        try:
            mday_from = mpat.search(obs.From).group()
            month_from = monthpat.search(obs.From).group()
            mday_to = mpat.search(obs.To).group()
            month_to = monthpat.search(obs.To).group()
        except AttributeError:
            mday_from = ''
            month_from = ""
            mday_to = ''
            month_to = ''
        #creating a list of days
        busy_day = self.parse_list_days(obs.Busy_day)
        busy_kh = self.parse_list_days(obs.Busy_kh)

        #parsing the dates to datetime objects
        Name = obs.Name
        if mday_from != '':
            From = datetime(year, self.parse_month(month_from),int(mday_from))
            To = datetime(year, self.parse_month(month_to), int(mday_to))
        else:
            From = ''
            To = ''

        return self.Observation(Name, From, To, busy_day, busy_kh)

    def create_record(self):
        """Creating  records:
        Example:
        self._record = {'name': {'from': [], 'to': [], busy_day = [], busy_kh = []}}
        """
        out = {}
        for observation in self.obs_generator():
            observation = self.parse_observation(observation)
            if observation.From != '':
                absent_days = [date.date() for date in\
                 pd.date_range(observation.From, end = observation.To, freq= 'D')]
            else:
                absent_days = []
            busy_days = [day for day in observation.Busy_day if day != '']  # remove empty strings
            busy_kh = [day for day in observation.Busy_kh if day != '']
            if observation.Name in out:
                out[observation.Name.strip()]['away'].extend(absent_days)
                out[observation.Name.strip()]['preferred'].extend(busy_days)
                out[observation.Name.strip()]['preferred_kh'].extend(busy_kh)
            else:
                out[observation.Name.strip()]= {'away': absent_days,\
                 'preferred': busy_days, 'preferred_kh': busy_kh}
        self._record = out

#Creating to new columns 'date_From' and 'date_To' --------------[USED CODE!!!!!]
def _parse_from(self,x):
    try:
        mday_from = mpat.search(x).group()
        month_from = monthpat.search(x).group()
    except AttributeError:
        mday_from = ''
        month_from = ""

    if mday_from != '':
        From = date(year,parse_month(month_from),int(mday_from))

    else:
        From = ''
    return From

def _parse_to(self, x):
    try:
        mday_to = mpat.search(x).group()
        month_to = monthpat.search(x).group()
    except AttributeError:
        mday_to = ''
        month_to = ''

    if mday_to != '':
        To = date(year, parse_month(month_to), int(mday_to))
    else:
        To = ''
    return To
# Excetions ------------------------------------------

class DontOverride(Exception):
    pass

class SpotTaken(Exception):
    pass

class NotScheduled(Exception):
    pass
#===============================================================
def make_full_schedule(x,y , path= ''):
    """
    x and y are schedules from the Scheduler object
    This function takes to different schedules and merges them into a
    complete schedule. It the saves the complete schedule to 'path'
    """
    if len(path) == 0:
        path = '/media/aisik/aisik/Documents/Steiner_schedules'

    today = datetime.now().isoformat()
    dfs = []
    for sched in [x,y]:
        date_output = []
        people_output = []
        day = []
        for dat, people in sched.items():
            date_output.append(dat.isoformat())
            people_output.append(people)
            day.append(num_to_day[dat.weekday()])
        # make a dataframe
        dfs.append(pd.DataFrame({"Date":date_output, "People":\
        people_output,"Day":day}))
    print('cooks',dfs[0])
    print('kh', dfs[1])
    df = pd.merge(dfs[0],dfs[1], how = 'inner', left_on  = 'Date', right_on = "Date")
    df.drop(['Day_y'],axis = 1, inplace = True)
    df.sort_values("Date", inplace = True)
    df.columns= ['Date','Day', 'Cook','Kitchen Helper']
    df.to_csv(path + '/{0}.csv'.format(today))

def make_schedule(kind = 'cook'):
    """Makes schedules
    kind = 'cook' or 'kitchen_help'
    """
    url = 'https://docs.google.com/spreadsheets/d/1iBv2cj6u1MH_8'+\
    'JSvEfN-aJpTveyhkkgsNrLrgj1I3_U/edit#gid=1261624705'
    ss = SpreadSheet() #Instantiate a spreadsheet object
    ss.get_data(url)   # download data from the google sheet
    ss.create_record() # Create a record
    start = datetime(2017,6,23)
    periods = 19
    # end = datetime(2017,2,20)
    scheduler= Scheduler(start, periods)  #instantiate a scheduler
    scheduler.schedule(ss, sch_type = kind)     # make a schedule for cooks
    return scheduler.table

def main():
    #Manual data recording ------------------------
    # ss.put_record("Isaac",["monday","thurday"],[datetime(2017,1,14),datetime(2017,1,15)])

    cooks = make_schedule(kind = 'cook')
    kitchen_help = make_schedule(kind = 'kitchen_help')
    make_full_schedule(cooks, kitchen_help)









if __name__ == "__main__":
    main()
#--------------To do---------------
#        priorities to be implemented
#1. Considering people with strigent schedule requirement and not mostly available
#2. People with general strigent requirements
#.  People with less strigent requirement
