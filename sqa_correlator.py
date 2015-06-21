#!/usr/bin/env python
import ConfigParser, os, re, sys
from collections import Counter
from datetime import datetime, timedelta
from dns import name, resolver, reversename
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

# Hours to look back
seek_hours   = 72 
# Seconds to compare for delta
seek_seconds = 30
# Min number of events per cluster
seek_min     = 10 
# Min number of nodes down per cluster event
nodes_min    = seek_min
# Traceroute min packet loss to be of concern
trace_lmin   = 10

def main():
    # Get the last hour of events
    alarmbuf = {'cluster':{}}
    clusterid = None
    nextclusterid = 1
    alarms = session.query(SqaCollector).filter(SqaCollector.started>=(datetime.today() - timedelta(hours = seek_hours)))
    if alarms:
        for alarm in alarms:
            if alarmbuf.get('lastid'):
                delta = alarm.started - alarmbuf['lasttime']
                if delta.seconds <= seek_seconds:
                    if clusterid is None:
                        clusterid = nextclusterid
                        nextclusterid+=1
                    if alarmbuf['cluster'].get(clusterid) is None:
                        alarmbuf['cluster'][clusterid] = Set()
                    alarmbuf['cluster'][clusterid].add(alarmbuf['lastid'])
                    alarmbuf['cluster'][clusterid].add(alarm.id)
                else:
                    clusterid = None
                alarmbuf['lastdelta'] = delta
            alarmbuf['lasttime'] = alarm.started
            alarmbuf['lastid'] = alarm.id

    # Scan interesting clusters, extract information about brokenness
    for cluster in alarmbuf['cluster'].keys():
        # If cluster had min number of events
        if len(alarmbuf['cluster'][cluster]) >= seek_min:
            confirmed_alarms = []
            problem_asns = []
            for sqa_id in alarmbuf['cluster'][cluster]:
                # Get alarm
                alarm = session.query(SqaCollector).filter(SqaCollector.id == sqa_id)
                if alarm.count() == 1:
                    alarm = alarm[0]
                    # Look inside alarm for min number of nodes down
                    nodes_down = re.search(r'(\d+) new nodes down', alarm.short)
                    if nodes_down:
                        if nodes_down.groups():
                            if nodes_down.groups()[0] >= nodes_min:
                                #Note a confirmed alarm
                                confirmed_alarms.append(str(sqa_id))
                                #Start analysing the traceroutes
                                problem_nodes = []
                                if 'StDev' in alarm.long:
                                    in_traceroute = None
                                    for line in alarm.long.splitlines():
                                        if in_traceroute == 1:
                                            line_parse = re.search(r'^\s+(\d+)\.\|--\s+(\S+)\s+(\S+)%\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$', line)
                                            if line_parse:
                                                # If you find a traceroute line with more than min packet loss, store it
                                                if int(line_parse.groups()[0]) > 1 and float(line_parse.groups()[2]) > trace_lmin:
                                                    problem_nodes.append(line_parse.groups()[1])
                                            else:
                                                in_traceroute = None
                                        if 'StDev' in line:
                                            in_traceroute = 1
                                if len(problem_nodes) > 1:
                                    # Find first problem node (which also isn't the only problem node), look up ASN and add to problem_asns for cluster
                                    problem_asns.append(find_asn(problem_nodes[0]))
            # Now summarise cluster issues
            print "Cluster [%s], Alarms [%s], ASN list [%s]" % (cluster, ','.join(confirmed_alarms), pcnt_breakdown(problem_asns))

           
    session.close()

# Look up ASN for an IP address
def find_asn(ip):
    reverse_zone = 'ip6.arpa' if ':' in ip else 'in-addr.arpa'
    origin_zone  = 'origin6.asn.cymru.com' if ':' in ip else 'origin.asn.cymru.com'
    try:
        # Convert address into format that can be sent to cymru lookup service
        lookup_target = name.from_unicode(((str(reversename.from_address(ip)).replace(reverse_zone, origin_zone)).decode("utf-8")))
        # Run query to cymru
        lookup_result = resolver.query(lookup_target, 'TXT')
        # Add result if found
        if lookup_result:
            asn = str(lookup_result[0]).replace('"','').split(' | ')[0]
            return asn
    except:
        # Generic exception handler, should look at logging exceptions in the future TODO
        return None

# Get percentage breakdown for contributing ASN
def pcnt_breakdown(asns):
    result = []
    counter = Counter(asn for asn in asns).most_common(3)
    for countee in counter:
        (asn, count) = countee
        pcnt = int(100 * float(count) / float(len(asns)))
        result.append([asn, pcnt])
    return result

if __name__ == '__main__':
    main()
