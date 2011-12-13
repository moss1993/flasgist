from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, send_from_directory 
from os.path import join, curdir
import os
import markdown
import datetime
import threading
import requests
import json

# helpers                                                                                                                                                                                                                                                                     
def to_markdown(value):
    """Converts a string into valid Markdown."""
    return markdown.markdown(value)

# create our little application :)                                                                                                                                                                                                                                            
app = Flask(__name__)
app.jinja_env.filters['markdown'] = to_markdown
app.secret_key = os.environ['secret_key']

@app.route('/about/', methods=['GET'])
def contact():
    return render_template('about.html')


@app.route('/', methods=['GET'])
@app.route('/<page>', methods=['GET'])
def show_entries(page=None):
    app.logger.debug('hello')
    paginate = None
    if page is None:
        r = requests.get('https://api.github.com', auth=(os.environ['GIST_USR'], os.environ['GIST_PWD']))
        uri = 'https://api.github.com/gists/starred' #users/davidthewatson/gists'
    elif page in ['first', 'next', 'prev', 'last']:
        uri = session['paginate'][page]
    else:
        try:
            page = session['map'][0]['id']
            uri = 'https://api.github.com/gists/' + page
        except:
            abort(404)
    r = requests.get(uri, auth=(os.environ['GIST_USR'], os.environ['GIST_PWD']))
    if r.status_code == 200:
        if page is not None and page.isdigit():
            gists = [json.loads(r.content)]
        else:
            gists = json.loads(r.content)
        if 'link' in r.headers.keys():
            paginate = link_parser(r.headers['link'])
            session['paginate'] = paginate
        l = []
        app.logger.debug(gists)
        for gist in gists:
            id = gist['id']
            this_gist = requests.get('https://api.github.com/gists/' + id)
            content = json.loads(this_gist.content)
            if len(content['files']) == 1:
                [l.append({'filename': filename,
                           'date': datetime.datetime.strptime(content['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%m/%d/%Y@%H:%M:%S'),
                           'description': content['description'],
                           'content': content['files'][filename]['content'],
                           'id': id}) for filename in content['files'].keys()]
                session['map'] = l
        return render_template('index.html', l = l, paginate=paginate)
    abort(r.status_code)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/sights/', methods=['GET'])
def sights():
    return render_template('sights.html')

@app.route('/sounds/', methods=['GET'])
def sounds():
    return render_template('sounds.html')

@app.route('/software/', methods=['GET'])
def software():
    r = requests.get('http://github.com/api/v2/json/repos/show/davidthewatson/')
    repositories = []
    if r.status_code == 200:
        d = json.loads(r.content)
        repositories = d['repositories']
    return render_template('software.html', repos=repositories)

def link_parser(s):
    tokens = s.split(',')
    d = {}
    for pairs in tokens:
        link_rel = pairs.split(';')
        link, rel = link_rel[0].strip()[1:-1], link_rel[1].split('=')[1].strip()[1:-1]
        d[rel] = link
    return d