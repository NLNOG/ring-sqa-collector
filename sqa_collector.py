#!/usr/bin/env python

import ConfigParser, datetime, json, os, socket
from flask import Flask, request
from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm import sessionmaker
from sqa_collector_db import DECLARATIVE_BASE, SqaCollector

app = Flask(__name__, static_url_path='')
app.debug = False

config = ConfigParser.ConfigParser()
config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sqa_collector.conf')
config.read(config_file)

# Database connector string
try:
    db_conn_str = config.get('database', 'connection_string')
except (NoOptionError, NoSectionError):
    db_conn_str = 'mysql://sqa_collector:sqa_collector@localhost/sqa_collector'

# Max results from database
try:
    max_results = config.get('output', 'max_results')    
except (NoOptionError, NoSectionError):
    max_results = 100

# Default pagination size
try:
    per_page = config.get('output', 'per_page')    
except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
    per_page = 50

# Connect to DB and session
engine = create_engine(db_conn_str)
DECLARATIVE_BASE.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Routing
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
    <style>th { background: #999999; } .modal-dialog { width: 800px; }</style>
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
    for alarm in session.query(SqaCollector).order_by(desc(SqaCollector.started)).limit(max_results):
        html += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (alarm.id, alarm.started, alarm.raised_by, alarm.short)
    html += '</tbody></table>'
    html += '''
        </div>
    </div>
    <div class="modal fade" id="textModal" tabindex="-1" role="dialog" aria-labelledby="textModalLabel" aria-hidden="true"></div>
    <script src="http://code.jquery.com/jquery-git1.min.js"></script>
    <script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js"></script>
    <script src="/jquery.dynatable.js"></script>
    <script>
            $(document).ready(function() { 
'''
    html += '$.dynatableSetup({dataset: { perPageDefault: ' + str(per_page) + ' }, writers: { _rowWriter: tableRowWriter}});'
    html += '''
                $('#results').dynatable(); 
                $('#results').css('cursor','pointer');
            });

            function tableRowWriter(rowIndex, record, columns, cellWriter) {
                row = '<tr>' + tableRowTdMaker(record.id, record.id) + tableRowTdMaker(record.id, record.timestamp) + tableRowTdMaker(record.id, record.raised_by) + tableRowTdMaker(record.id, record.short) + '</tr>';
                return row;
            }

            function tableRowTdMaker(id, body) {
                row = '<td style="text-align: left;" onClick="showText(' + id + ');">' + body + '</td>';
                return row;
            }

            function showText(id) {
                var url = '/text/' + id;
                $('#textModal').html('<div class="modal-dialog"><div class="modal-content"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button><h4 class="modal-title">View Text - Alert ' + id + '</h4><a href="/view/' + id + '">permalink</a></div><div class="modal-body"><pre id="textModal-body-text"></pre><div class="modal-footer"><button type="button" class="btn btn-default" data-dismiss="modal">Close</button></div></div></div></div>');
                $.ajax({url: url, success: function(result){
                    $('#textModal-body-text').text(result);
                    $('#textModal').modal('show'); 
                    $('#textModal').css({ 'display': 'block' });
                }});
            }

    </script> 
</body>
</html>
'''
    session.close()
    return html

@app.route('/', methods=['POST'])
def store():
    return_code = 'FAIL 0'
    try:
        blob    = json.loads(request.get_data())
        afi     = blob['afi']
        short   = blob['short']
        long    = blob['long']
        try:
            raised_by = socket.gethostbyaddr(request.remote_addr)[0]
            if '.' in raised_by:
                print "Unrecognised sending host %s" % raised_by
                return_code = 'FAIL 1'
        except Exception, e:
            print e
            return_code = 'FAIL 2'

        if blob['status'] == 'raise':
            session.add(SqaCollector(started=datetime.datetime.today(), raised_by=raised_by, afi=afi, short=short, long=long))
            session.commit()
        elif blob['status'] == 'clear':
            open_alarms = session.query(SqaCollector).filter(and_(SqaCollector.raised_by==raised_by, SqaCollector.afi==afi, SqaCollector.ended==None))
            if open_alarms:
                for open_alarm in open_alarms:
                    open_alarm.ended=datetime.datetime.today()
            session.commit()
    except Exception, e:
        print e
        return_code = 'FAIL 3'
    else:
        return_code = 'OK';

    session.close()
    return return_code

@app.route('/view/<id>', methods=['GET'])
def render_text(id):
    html = '<pre>'
    html += display_text(id)
    html += '</pre>'
    return html

@app.route('/text/<id>', methods=['GET'])
def display_text(id):
    html = 'No alarm text.'
    try:
        results = session.query(SqaCollector).filter(SqaCollector.id==id)
        if results:
            for result in results:
                html = result.long
    except Exception, e:
        print e
    session.close()
    return html

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
