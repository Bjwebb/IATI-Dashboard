import os, json, re
from collections import defaultdict

def main(jinja_env):
    template = jinja_env.get_template('github.html')

    isoDateRegex = re.compile('(-?[0-9]{4,})-([0-9]{2})-([0-9]{2})')

    milestones_calendar = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    milestones_nodate = []

    for fname in os.listdir('data'):
        if not fname.endswith('.json'):
            continue 
        milestones = json.load(open(os.path.join('data',fname)))
        if not 'message' in milestones:
            for milestone in milestones:
                milestone['repo'] = fname[:-5]
                if not milestone['due_on']:
                    milestones_nodate.append(milestone)
                else:
                    m = isoDateRegex.match(milestone['due_on'])
                    milestones_calendar[m.group(1)][m.group(2)][m.group(3)].append(milestone)
                    #print('   ', milestone['title'], '---', milestone['due_on'], '---', str(milestone['open_issues'])+'/'+str(milestone['closed_issues']))

    return template.render(milestones_calendar=milestones_calendar, milestones_nodate=milestones_nodate, sorted=sorted, github=True)

