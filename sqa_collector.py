#!/usr/bin/env python

import ConfigParser, datetime, json, os, socket
from flask import Flask, request
from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm import sessionmaker
from sqa_collector_db import DECLARATIVE_BASE, SqaCollector, SqaCorrelator, SqaCollectorCorrelator, SqaCorrelatorObject

app = Flask(__name__, static_url_path='')
app.debug = False

config = ConfigParser.ConfigParser()
config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sqa_collector.conf')
config.read(config_file)

# Database connector string
try:
    db_conn_str = config.get('database', 'connection_string')
except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
    db_conn_str = 'mysql://sqa_collector:sqa_collector@localhost/sqa_collector'

# Database pool recycle
try:
    db_pool_recycle = config.get('database', 'pool_recycle')
except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
    db_pool_recycle = 3600

# Max results from database
try:
    max_results = config.get('output', 'max_results')
except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
    max_results = 100

# Default pagination size
try:
    per_page = config.get('output', 'per_page')
except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
    per_page = 50

# Connect to DB and session
engine = create_engine(db_conn_str, pool_recycle=db_pool_recycle)
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

@app.route('/event/<int:event_req>', methods=['GET'])
@app.route('/', methods=['GET'])
def display(event_req=None):
    html = '''
<!doctype html>

<html lang="en">
<head>
    <meta charset="utf-8">
    <title>SQA Collector</title>
    <meta name="description" content="SQA Collector">
    <meta name="author" content="NLNOG RING">

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
        <a class="navbar-brand navbar-right" href="#">NLNOG RING</a>
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
        <p class="lead">Welcome to the SQA Collector lookup service, below are the latest SQA alerts. Times all in UTC.</font></p>
      </div>
    <div class="row">
'''
    html += '<table id="events" class="table table-bordered"><thead><tr><th>major_event</th><th>timestamp</th><th>contributors</th></tr></thead><tbody>'
    if event_req:
        events = session.query(SqaCorrelator).filter(SqaCorrelator.id==event_req)
    else:
        events = session.query(SqaCorrelator).order_by(desc(SqaCorrelator.id)).limit(10)
    for event in events:
        results = session.query(SqaCorrelatorObject).filter(SqaCorrelatorObject.sqa_correlator_id==event.id)
        # window
        first_alarm = session.query(SqaCollectorCorrelator, SqaCollector).filter(SqaCollectorCorrelator.correlator_id==event.id).join(SqaCollector).limit(1)
        timestamp = first_alarm[0][1].started
        contrib = "Unknown"
        if results.count() > 0:
            contrib = ""
            for result in results:
                contrib += "%s (%s%%), " % (result.object, result.percentage)
        html += "<tr><td><a href='/event/%s'>%s</a></td><td>%s</td><td>%s</td></tr>" % (event.id, event.id, timestamp, contrib)
    html += '</tbody></table>'
    html += '''
    </div>
    <div class="row">
'''
    html += '<table id="results" class="table table-bordered"><thead><tr><th>major_event</th><th>alarm</th><th>timestamp</th><th>raised_by</th><th>afi</th><th>short</th></tr></thead><tbody>'
    if event_req:
        alarms = session.query(SqaCollector, SqaCollectorCorrelator).outerjoin(SqaCollectorCorrelator).filter(SqaCollectorCorrelator.correlator_id==event_req).order_by(desc(SqaCollector.started)).limit(max_results)
    else:
        alarms = session.query(SqaCollector, SqaCollectorCorrelator).outerjoin(SqaCollectorCorrelator).order_by(desc(SqaCollector.started)).limit(max_results)
    for alarm in alarms:
        if alarm.SqaCollectorCorrelator:
            event_id = alarm.SqaCollectorCorrelator.correlator_id if alarm.SqaCollectorCorrelator.correlator_id else 'None'
        else:
            event_id = 'None'
        alarm_id = alarm.SqaCollector.id if alarm.SqaCollector.id else 'None'
        started  = alarm.SqaCollector.started if alarm.SqaCollector.started else 'Unknown'
        afi      = alarm.SqaCollector.afi
        raisedby = alarm.SqaCollector.raised_by if alarm.SqaCollector.raised_by else 'Unknown'
        short    = alarm.SqaCollector.short if alarm.SqaCollector.short else 'No description'

        html += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (event_id, alarm_id, started, raisedby, afi, short)
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
                row = '<tr>' + tableRowEventTdMaker(record.major_event, record.major_event) + tableRowAlarmTdMaker(record.alarm, record.alarm) + tableRowAlarmTdMaker(record.alarm, record.timestamp) + tableRowAlarmTdMaker(record.alarm, record.raised_by) + tableRowAlarmTdMaker(record.alarm, record.short) + '</tr>';
                return row;
            }

            function tableRowAlarmTdMaker(id, body) {
                row = '<td style="text-align: left;" onClick="showAlarmText(' + id + ');">' + body + '</td>';
                return row;
            }

            function tableRowEventTdMaker(id, body) {
                if (id == "None") {
                    row = '<td style="text-align: left;">' + body + '</td>';
                }
                else {
                    row = '<td style="text-align: left;" onClick="showEventText(' + id + ');">' + body + '</td>';
                }
                return row;
            }

            function showAlarmText(id) {
                var url = '/alarm_text/' + id;
                $('#textModal').html('<div class="modal-dialog"><div class="modal-content"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button><h4 class="modal-title">View Text - Alarm ' + id + '</h4><a href="/view_alarm/' + id + '">permalink</a></div><div class="modal-body"><pre id="textModal-body-text"></pre><div class="modal-footer"><button type="button" class="btn btn-default" data-dismiss="modal">Close</button></div></div></div></div>');

                $.ajax({url: url, success: function(result){
                    $('#textModal-body-text').text(result);
                    $('#textModal').modal('show');
                    $('#textModal').css({ 'display': 'block' });
                }});
            }

            function showEventText(id) {
                var url = '/event_text/' + id;
                $('#textModal').html('<div class="modal-dialog"><div class="modal-content"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button><h4 class="modal-title">View Text - Event ' + id + '</h4><a href="/view_event/' + id + '">permalink</a></div><div class="modal-body"><pre id="textModal-body-text"></pre><div class="modal-footer"><button type="button" class="btn btn-default" data-dismiss="modal">Close</button></div></div></div></div>');
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
            app.logger.exception(e)
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
        app.logger.exception(e)
        return_code = 'FAIL 3'
    else:
        return_code = 'OK';

    session.close()
    return return_code

@app.route('/view_alarm/<id>', methods=['GET'])
def render_alarm_text(id):
    html = '<pre>'
    html += display_alarm_text(id)
    html += '</pre>'
    return html

@app.route('/alarm_text/<id>', methods=['GET'])
def display_alarm_text(id):
    html = 'No alarm text.'
    try:
        results = session.query(SqaCollector).filter(SqaCollector.id==id)
        if results:
            for result in results:
                html = result.long
    except Exception, e:
        app.logger.exception(e)
    session.close()
    return html

@app.route('/view_event/<id>', methods=['GET'])
def render_event_text(id):
    html = '<pre>'
    html += display_event_text(id)
    html += '</pre>'
    return html

@app.route('/event_text/<id>', methods=['GET'])
def display_event_text(id):
    html = 'No event text.'
    try:
        results = session.query(SqaCorrelatorObject).filter(SqaCorrelatorObject.sqa_correlator_id==id)
        if results:
            if results.count() > 0:
                html = 'The following were the top three contributors to the event:\n'
                for result in results:
                    html += "%s(%s%%) " % (result.object, result.percentage)
            else:
                html = 'No contributors could be determined for this event\n'
    except Exception, e:
        app.logger.exception(e)
    session.close()
    return html

# Flask specifies that teardown functions should not raise.
# However, they might not have their own error handling,
# so we wrap them here to log any errors and prevent errors from
# propagating.

def wrap_teardown_func(teardown_func):
    def log_teardown_error(*args, **kwargs):
        try:
            teardown_func(*args, **kwargs)
        except Exception, e:
            app.logger.exception(e)
    return log_teardown_error

if app.teardown_request_funcs:
    for bp, func_list in app.teardown_request_funcs.items():
        for i, func in enumerate(func_list):
            app.teardown_request_funcs[bp][i] = wrap_teardown_func(func)

if app.teardown_appcontext_funcs:
    for i, func in enumerate(app.teardown_appcontext_funcs):
        app.teardown_appcontext_funcs[i] = wrap_teardown_func(func)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
