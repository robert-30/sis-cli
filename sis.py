import click
from tabulate import tabulate
import sisAPI as sis

api = sis.sisAPI()

@click.group()
def osiris():
    pass

@click.command()
def sign_in():
    username = click.prompt('s-number', type=str)
    password = click.prompt('password', type=str, hide_input=True)
    
    if api.sign_in(username, password):
        click.secho('sign in successful', fg='green')
    else:
        click.secho('sign in failed', fg='red')

@click.command()
def grades():
    try:
        grades = api.grades(100)

        #filter relevant cells
        grades = list(map(lambda row: [row['cursus'], row['cursus_korte_naam'], row['collegejaar'], row['blok'], row['weging'], row['resultaat'], row['voldoende']], grades))
        grades_col = []
        column_headers = ['cursus', 'cursus_korte_naam', 'collegejaar', 'blok', 'weging', 'resultaat']
        for row in grades:
            res_row = row[:-2]
            colo = 'red'
            if row[-1] == 'J':
                colo = 'green'
            
            res_row.append(click.style(row[-2], fg=colo))
            grades_col.append(res_row)
        click.echo_via_pager(tabulate(grades_col, column_headers, tablefmt='fancy_grid'))

    except sis.NoTokenError:
        click.echo('Please sign in again: sis sign_in');


@click.command()
@click.option('--n_weeks', '-w', 'n_weeks', default=1)
def schedule(n_weeks):
    try:
        DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        LEC_TYPE_COLO = {'LEC': 'green', 'TUT': 'blue', 'DIGI-INZAGE': 'yellow', 'EXA': 'red', 'COMP': 'cyan', 'DLT': 'red', 'PRE': 'green'}
 
        sched = api.schedule(n_weeks)
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
        click.echo_via_pager(tabulate(sched_list, tablefmt='fancy_grid'))
    except:
        click.echo('Something went wrong. Try signing in again.');

@click.command()
def courses():
    try:
        courses = api.registered_courses(100)

        #filter relevant cells
        courses = list(map(lambda row: [row['collegejaar'], row['blok'], row['id_cursus'], row['cursus'], row['cursus_korte_naam'], row['punten']], courses))
        courses = sorted(courses, key = lambda course: str(course[0]) + course[1] + str(course[2]))
        
        courses_col = []

        for course in courses:
            if course[-1] == 6:
                courses_col.append(map (lambda x: click.style(str(x), fg='green'), course))
            else:
                courses_col.append(map (lambda x: click.style(str(x), fg='blue'), course))

        column_headers = ['collegejaar', 'blok', 'id_cursus', 'cursus', 'cursus_korte_naam', 'ec']
        
        click.echo(tabulate(courses_col, column_headers, tablefmt='fancy_grid'))
        
    except sis.NoTokenError:
        click.echo('Please sign in again: sis sign_in');

@click.command()
def exams():
    try:
        exams = api.registered_exams(100)

        #filter relevant cells
        exams = list(map(lambda row: [row['collegejaar'], row['blok'], row['id_cursus'], row['cursus'], row['cursus_korte_naam'], row['id_toets_gelegenheid'], row['toets_omschrijving'], row['gelegenheid'], row['toetsdatum'], row['dag']], exams))
        for exam in exams:
            if exam[-2] is None:
                exam[-2] = ''
        exams = sorted(exams, key = lambda exam: str(exam[-2]))
        exams_col = []

        for exam in exams:
            if exam[-3] == 1:
                exams_col.append(map (lambda x: click.style(str(x), fg='green'), exam))
            else:
                exams_col.append(map (lambda x: click.style(str(x), fg='yellow'), exam))

        column_headers = ['collegejaar', 'blok', 'id_cursus', 'cursus', 'cursus_korte_naam', 'id_toets_gelegenheid', 'omschrijving', 'gelegenheid', 'toetsdatum', 'dag']

        click.echo(tabulate(exams_col, column_headers, tablefmt='fancy_grid'))

    except sis.NoTokenError:
        click.echo('Please sign in again: sis sign_in');


@click.command()
@click.argument('id_cursus')
def newexam(id_cursus):
    try:
        course_info_tests = api.get_tests_for_course(id_cursus)

        conf_msg = ''
        headers = ['collegejaar', 'cursus', 'cursus_korte_naam']
        for header in headers:
            conf_msg = conf_msg + str(course_info_tests[header]) + '\t'
        conf_msg += '\n'        
        
        test_headers = ['id_toets_gelegenheid', 'toets_omschrijving', 'gelegenheid', 'toetsdatum', 'dag']
        tests_table = []
        for test in course_info_tests['toetsen']:
            test_info = []
            for header in test_headers:
                test_info.append(test[header])
            tests_table.append(test_info)
        
        conf_msg += tabulate(tests_table, headers=test_headers) + '\n'
        click.echo(conf_msg)
        id_toets = click.prompt('Which test would you like to register to? id_toets_gelegenheid', type=str)
        for test in course_info_tests['toetsen']:
            if str(test['id_toets_gelegenheid']) == id_toets:
                if api.register_for_test(test).status_code == 200:
                    click.echo(click.style('Registration successful!', fg='green'))
                    return
                else:
                    click.echo(click.style('Registration failed.', fg='red'))
        click.echo(click.style('Test not found.', fg='red'))
    except sis.NoTokenError:
        click.echo('Please sign in again: sis sign_in')

@click.command()
@click.argument('query')
def search(query):
    try:
        hits = api.search_for_course(query)['hits']
        print(str(hits['total']) + ' hit(s) found')
        
        headers = ['id_cursus_blok', 'id_cursus', 'collegejaar', 'blok', 'cursus', 'cursus_korte_naam', 'punten']
        results_table = []
        
        for hit in hits['hits']:
            result = []
            for header in headers:
                result.append(hit['_source'][header])
            
            can_register = False

            for registration_period in hit['_source']['inschrijfperiodes']:
                can_register=True
            
            fg_color = None
            
            if can_register:
                fg_color = 'green'
            else:
                fg_color = 'red'

            result.append(click.style(str(can_register), fg=fg_color))
                

            results_table.append(result)

        click.echo(tabulate(results_table, headers + ['registration open'], tablefmt='fancy_grid'))
    except sis.NoTokenError:
        click.echo('Please sign in again: sis sign_in')

@click.command()
@click.argument('id_cursus_blok')
def newcourse(id_cursus_blok):
    try:
        course_info = api.get_course_info(id_cursus_blok)
        
        conf_msg = ''
        headers = ['collegejaar', 'blok', 'cursus', 'cursus_korte_naam', 'categorie_omschrijving', 'punten']
        for header in headers:
            conf_msg = conf_msg + str(course_info[header]) + '\t'
        conf_msg += '\n'        
        
        study_table = []
        for studytype in course_info['werkvorm_voorzieningen']:
            study_table.append([studytype['werkvorm'], studytype['werkvorm_omschrijving']])
        
        conf_msg += tabulate(study_table, headers=['Study types', '']) + '\n'
        
        test_table = []
        for testtype in course_info['toets_voorzieningen']:
            test_table.append([testtype['toets'], testtype['toets_omschrijving']])
        
        conf_msg += tabulate(test_table, headers=['Test types', ''])
        click.echo(conf_msg)

        if click.confirm('Confirm registration?'):
            ret = api.register_for_course(course_info)
            if ret.status_code == 200:
                print('Registered successfully!')
            else:
                print('Registration failed. Please try again.')
        else:
            click.echo('Registration cancelled')

    except sis.NoTokenError:
        click.echo('Please sign in again: sis sign_in')

osiris.add_command(sign_in)
osiris.add_command(grades)
osiris.add_command(schedule)
osiris.add_command(courses)
osiris.add_command(search)
osiris.add_command(newcourse)
osiris.add_command(newexam)
osiris.add_command(exams)
osiris()
