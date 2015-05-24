#!/usr/bin/env python

import datetime, json, socket
from flask import Flask, request
from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm import sessionmaker
from sqa_collector_db import DECLARATIVE_BASE, SqaCollector

app = Flask(__name__, static_url_path='')

enginestr = 'mysql://sqa_collector:sqa_collector@localhost/sqa_collector'
engine = create_engine(enginestr)
DECLARATIVE_BASE.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/jquery.dynatable.css', methods=['GET'])
def dynatableCSS():
    return app.send_static_file('jquery.dynatable.css')

@app.route('/jquery.dynatable.js', methods=['GET'])
def dynatableJS():
    return app.send_static_file('jquery.dynatable.js')

@app.route('/', methods=['GET'])
def display():
    html = '''
<!doctype html>

<html lang="en">
<head>
    <meta charset="utf-8">
    <title>SQA Collector</title>
    <meta name="description" content="SQA Collector">
    <meta name="author" content="NLNog RING">

    <link href="/jquery.dynatable.css" rel="stylesheet">
    <link href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css" rel="stylesheet">
    <!--[if lt IE 9]>
        <script src="http://html5shiv.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->
    <style>th { background: #999999; }</style>
</head>

<body>
    <nav class="navbar navbar-inverse navbar-fixed-top">
      <div class="container">
        <a class="navbar-brand navbar-right" href="#">NLNog RING</a>
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-col-md-4="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="#">SQA Collector lookup service</a>
        </div>
        <div id="navbar" class="collapse navbar-collapse">
          <ul class="nav navbar-nav">
            <li class="active"><a href="/">Home</a></li>
          </ul>
        </div>
      </div>
    </nav>
    <div class="container">
      <div class="jumbotron">
        <h1>SQA Collector lookup service</hq>
        <p class="lead">Welcome to the SQA Collector lookup service, below are the lastest SQA alerts. Times all in UTC.</font></p>
      </div>
      <div class="row">
'''
    html += '<table id="results" class="table table-bordered"><thead><tr><th>id</th><th>timestamp</th><th>raised_by</th><th>short</th></tr></thead><tbody>'
    for alarm in session.query(SqaCollector).order_by(desc(SqaCollector.started)).limit(50):
        html += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (alarm.id, alarm.started, alarm.raised_by, alarm.short)
    html += '</tbody></table>'
    html += '''
        </div>
    </div>
    <script src="http://code.jquery.com/jquery-git1.min.js"></script>
    <script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js"></script>
    <script src="/jquery.dynatable.js"></script>
    <script>$(document).ready(function() { $('#results').dynatable(); })</script> 
</body>
</html>
'''
    return html

@app.route('/', methods=['POST'])
def store():
    try:
        blob    = json.loads(request.get_data())
        afi     = blob['afi']
        short   = blob['short']
        try:
            raised_by = socket.gethostbyaddr(request.remote_addr)[0]
            if '.' in raised_by:
                print "Unrecognised sending host %s" % raised_by
                return "FAIL 1"
        except Exception, e:
            print e
            return "FAIL 2"

        if blob['status'] == 'raise':
            session.add(SqaCollector(started=datetime.datetime.today(), raised_by=raised_by, afi=afi, short=short))
            session.commit()
        elif blob['status'] == 'clear':
            open_alarms = session.query(SqaCollector).filter(and_(SqaCollector.raised_by==raised_by, SqaCollector.afi==afi, SqaCollector.ended==None))
            if open_alarms:
                for open_alarm in open_alarms:
                    open_alarm.ended=datetime.datetime.today()
            session.commit()
    except Exception, e:
        print e
        return "FAIL 3"
    else:
        return "OK"

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
