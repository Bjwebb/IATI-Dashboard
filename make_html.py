from collections import OrderedDict
import json, sys, os, re, copy, datetime
import subprocess

from flask import Flask, render_template
app = Flask(__name__)

def group_files(d):
    out = OrderedDict()
    publisher_re = re.compile('(.*)\-[^\-]')
    for k,v in d.items():
        out[k] = OrderedDict()
        for k2,v2 in v.items():
            if type(v2) == list:
                out[k][k2] = OrderedDict()
                v2.sort()
                for listitem in v2:
                    publisher = publisher_re.match(listitem).group(1)
                    if not publisher in out[k][k2]:
                        out[k][k2][publisher] = []
                    out[k][k2][publisher].append(listitem)
            else:
                out[k][k2] = v2
    return out
            

current_stats = {
    'aggregated': json.load(open('./stats-calculated/current/aggregated.json'), object_pairs_hook=OrderedDict),
    'inverted': json.load(open('./stats-calculated/current/inverted.json'), object_pairs_hook=OrderedDict),
    'inverted_file': json.load(open('./stats-calculated/current/inverted-file.json'), object_pairs_hook=OrderedDict),
    'download_errors': []
}
current_stats['inverted_file_grouped'] = group_files(current_stats['inverted_file'])
ckan = json.load(open('./stats-calculated/ckan.json'), object_pairs_hook=OrderedDict)
gitdate = json.load(open('./stats-calculated/gitdate.json'), object_pairs_hook=OrderedDict)
with open('./data/downloads/errors') as fp:
    for line in fp:
        if line != '.\n':
            current_stats['download_errors'].append(line.strip('\n').split(' ', 3))


def iati_stats_page(template, **kwargs):
    def f():
        return render_template(template, current_stats=current_stats, ckan=ckan, **kwargs) 
    return f

def element_url(element):
    return element.replace('.//', '').replace('/@','.').replace('/','_')

def get_publisher_stats(publisher):
    return json.load(open('./stats-calculated/current/aggregated/{0}.json'.format(publisher)), object_pairs_hook=OrderedDict)

def firstint(s):
    if s[0].startswith('<'): return 0
    m = re.search('\d+', s[0])
    return int(m.group(0))

app.jinja_env.filters['url_to_filename'] = lambda x: x.split('/')[-1]
app.jinja_env.globals['url'] = lambda x: x
app.jinja_env.globals['datetime_generated'] = subprocess.check_output(['date', '+%Y-%m-%d %H:%M:%S %z']).strip()
app.jinja_env.globals['datetime_data'] = max(gitdate.values())
app.jinja_env.globals['element_url'] = element_url
app.jinja_env.globals['sorted'] = sorted

from vars import expected_versions
import github.web, licenses
urls = {
    'index.html': iati_stats_page('index.html', publisher=True, get_publisher_stats=get_publisher_stats),
    'files.html': iati_stats_page('files.html', files=True, firstint=firstint),
    'download.html': iati_stats_page('download.html', download=True),
    'xml.html': iati_stats_page('xml.html', xml=True),
    'validation.html': iati_stats_page('validation.html', validation=True),
    'versions.html': iati_stats_page('versions.html', versions=True, expected_versions=expected_versions),
    'licenses.html': licenses.create_main(ckan),
    'organisation.html': iati_stats_page('organisation.html', organisation=True),
    'elements.html': iati_stats_page('elements.html', elements=True),
    #'element':  dict([ (element_url(element)+'.html', iati_stats_page('element.html',
    #    element=element,
    #    publishers=publishers,
    #    url=lambda x: '../'+x,
    #    elements=True)) for element, publishers in current_stats['inverted']['elements'].items() ]),
    'codelists.html': iati_stats_page('codelists.html', codelists=True),
    'booleans.html': iati_stats_page('booleans.html', booleans=True),
    'codelist': dict([ (element_url(element)+'.html', iati_stats_page('codelist.html',
        element=element,
        values=values,
        url=lambda x: '../'+x,
        codelists=True)) for element, values in current_stats['inverted']['codelist_values'].items() ]),
    'publisher': dict([ (publisher+'.html', iati_stats_page('publisher.html',
        url=lambda x: '../'+x,
        publisher=publisher,
        publisher_stats=get_publisher_stats(publisher)
        )) for publisher in ckan ]),
    'github.html': github.web.main,
}

def make_html(urls, outdir=''):
    for url, f in urls.items():
        full_url = outdir+'/'+url
        if callable(f):
            f.__name__ = full_url.replace('.','_').encode('utf-8')
            app.add_url_rule(full_url, view_func=f)
        else:
            make_html(f, full_url)

make_html(urls)

if __name__ == '__main__':
    if '--live' in sys.argv:
        app.debug = True
        app.run()
    else:
        from flask_frozen import Freezer
        app.config['FREEZER_DESTINATION'] = 'out'
        app.config['FREEZER_REMOVE_EXTRA_FILES'] = False
        freezer = Freezer(app)
        freezer.freeze()
