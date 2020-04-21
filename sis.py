import click
from tabulate import tabulate
import sisAPI as sis
import os
import sisutil

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
        cached = sisutil.read_schedule(os.environ['HOME'] + '/.osiris_schedule.txt')
        if cached is not None:
            cached_sched = cached[0]
            retrieved_time = cached[1]
            click.secho('CACHED SCHEDULE || MAY BE OUTDATED || RETRIEVED ON ' + retrieved_time, fg='red', bg='cyan')
            click.secho('CACHED SCHEDULE || MAY BE OUTDATED || RETRIEVED ON ' + retrieved_time, fg='red', bg='cyan')
            click.secho('CACHED SCHEDULE || MAY BE OUTDATED || RETRIEVED ON ' + retrieved_time, fg='red', bg='cyan')
            sched_styled = sisutil.style_schedule(cached_sched)
            click.echo(sched_styled)
            click.secho('CACHED SCHEDULE || MAY BE OUTDATED || RETRIEVED ON ' + retrieved_time, fg='red', bg='cyan')
            click.secho('CACHED SCHEDULE || MAY BE OUTDATED || RETRIEVED ON ' + retrieved_time, fg='red', bg='cyan')
            click.secho('CACHED SCHEDULE || MAY BE OUTDATED || RETRIEVED ON ' + retrieved_time, fg='red', bg='cyan')
        sched = api.schedule(n_weeks)
        sched_list = []
        click.echo_via_pager(sisutil.style_schedule(sched))
        sisutil.write_schedule(os.environ['HOME'] + '/.osiris_schedule.txt', sched)
    except sis.NoTokenError:
        click.echo('No token found. Try signing in again.')
    except KeyError as inst:
        click.echo('Unkown lecture type. Please add an issue on github and mention that the lecture type ' + str(inst) + ' is missing.')

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
        
        test_headers = ['toets_omschrijving', 'gelegenheid', 'toetsdatum', 'dag']
        tests_table = []
        test_idx = 0
        for test in course_info_tests['toetsen']:
            test_info = [test_idx]
            test_idx += 1
            for header in test_headers:
                test_info.append(test[header])
            tests_table.append(test_info)
        
        conf_msg += tabulate(tests_table, headers=['test_idx'] + test_headers) + '\n'
        click.echo(conf_msg)
        test_idx = int(click.prompt('Which test would you like to register to? test_idx', type=str))
        if test_idx < len(course_info_tests):
            test = course_info_tests['toetsen'][test_idx]
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
