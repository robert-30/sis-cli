import click
from tabulate import tabulate
import json
from datetime import datetime

def style_schedule(sched):
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    LEC_TYPE_COLO = {'LEC': 'green', 'TUT': 'blue', 'DIGI-INZAGE': 'yellow', 'EXA': 'red', 'COMP': 'cyan', 'DLT': 'red', 'PRE': 'green', 'LAB': 'magenta', 'RSP': 'bright_blue'}

    sched_list = []
    for week in sched:
        for day_idx in range(0, 7):
            day = week['dagen'][day_idx]

            for subj_idx in range(0, len(day['rooster'])):
                subj = day['rooster'][subj_idx]
                
                # only fill in a value for week or day if it's the first
                week_text = ''
                day_text = ''

                if subj_idx == 0:
                    if day_idx == 0:
                        week_text = 'Week ' + str(week['week'])
                    day_text = DAYS[day_idx]
                
                subj_name = subj['onderwerp'][subj['onderwerp'].find(' ')+1:]
                sched_list.append([click.style(week_text, bg='blue'), click.style(day_text, bg='green'), click.style(subj_name, fg=LEC_TYPE_COLO[subj['soort_rooster']]), subj['tijd_vanaf'], subj['tijd_tm'], subj['locatie']])
    return tabulate(sched_list, tablefmt='fancy_grid')

def write_schedule(filename, sched):
    f = open(filename, 'w')
    json.dump({'schedule': sched, 'time_written': datetime.now().timestamp()}, f)

def read_schedule(filename):
    try:
        f = open(filename, 'r')
        sched_json = json.load(f)
        time = datetime.fromtimestamp(sched_json['time_written'])
        if time.isocalendar()[1] != datetime.now().isocalendar()[1]:
            #outdated cache
            print(time.isocalendar()[1])
            return None
        else:
            return (sched_json['schedule'], str(time))
    except FileNotFoundError:
        return None
#    except:
#        return None
