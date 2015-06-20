#!/usr/bin/env python
import ConfigParser, os, uuid
from datetime import datetime, timedelta
from sets import Set
from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm import sessionmaker
from sqa_collector_db import DECLARATIVE_BASE, SqaCollector

config = ConfigParser.ConfigParser()
config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sqa_collector.conf')
config.read(config_file)

enginestr = 'mysql://sqa_collector:sqa_collector@localhost/sqa_collector'
engine = create_engine(enginestr)
DECLARATIVE_BASE.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

seek_hours   = 24
seek_seconds = 30

def main():
    # Get the last hour of events
    alarmbuf = {'cluster':{}}
    clusterid = None
    alarms = session.query(SqaCollector).filter(SqaCollector.started>=(datetime.today() - timedelta(hours = seek_hours)))
    if alarms:
        for alarm in alarms:
            if alarmbuf.get('lastid'):
                delta = alarm.started - alarmbuf['lasttime']
                if delta.seconds <= seek_seconds:
                    if clusterid is None:
                        clusterid = uuid.uuid4().urn.split(":")[2]
                    if alarmbuf['cluster'].get(clusterid) is None:
                        alarmbuf['cluster'][clusterid] = Set()
                    alarmbuf['cluster'][clusterid].add(alarmbuf['lastid'])
                    alarmbuf['cluster'][clusterid].add(alarm.id)
                else:
                    clusterid = None
                alarmbuf['lastdelta'] = delta
            alarmbuf['lasttime'] = alarm.started
            alarmbuf['lastid'] = alarm.id
           
    print alarmbuf['cluster']

    session.close()

if __name__ == '__main__':
    main()
