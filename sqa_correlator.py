#!/usr/bin/env python
import ConfigParser, dns.resolver, logging, os, re, socket, sys
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

## Config variables

# Log file location
try:
    log_file = config.get('correlator', 'log_file')
except (NoOptionError, NoSectionError):
    log_file = '/var/log/sqa_correlator.log'

# Database connector string
try:
    db_conn_str = config.get('database', 'connection_string')
except (NoOptionError, NoSectionError):
    db_conn_str = 'mysql://sqa_collector:sqa_collector@localhost/sqa_collector'

# Hours to look back
try:
    seek_hours = config.get('correlator', 'seek_hours')
except (NoOptionError, NoSectionError):
    seek_hours   = 99999

# Seconds to compare for delta
try:
    seek_seconds = config.get('correlator', 'seek_seconds')
except (NoOptionError, NoSectionError):
    seek_seconds = 30

# Min number of events per cluster
try:
    seek_min = config.get('correlator', 'seek_min')
except (NoOptionError, NoSectionError):
    seek_min = 10

# Min number of nodes down per cluster event
try:
    nodes_min = config.get('correlator', 'nodes_min')
except (NoOptionError, NoSectionError):
    nodes_min = 10

# Traceroute min packet loss to be of concern
try:
    trace_lmin = config.get('correlator', 'trace_lmin')
except (NoOptionError, NoSectionError):
    trace_lmin = 10

# List of whois servers to try
try:
    whois_servers = str(config.get('correlator', 'whois_servers')).split(',')
except (NoOptionError, NoSectionError):
    whois_servers = ['whois.ripe.net', 'whois.radb.net', 'whois.arin.net', 'whois.apnic.net', 'whois.lacnic.net', 'whois.afrinic.net']


# Set up DB Engine and session
engine = create_engine(db_conn_str)
DECLARATIVE_BASE.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Start of code
def main():

    # Start logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(process)d %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=log_file,
                        filemode='w')

    # Bring logging to console if -d provided
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d':
            console = logging.StreamHandler()
            console.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S')
            console.setFormatter(formatter)
            logging.getLogger('').setLevel(logging.DEBUG)
            logging.getLogger('').addHandler(console)

    # Get the last hour of events
    alarmbuf = {'cluster':{}}
    clusterid = None
    nextclusterid = 1
    alarms = session.query(SqaCollector).filter(SqaCollector.started>=(datetime.today() - timedelta(hours = int(seek_hours))))
    if alarms:
        for alarm in alarms:
            if alarmbuf.get('lastid'):
                delta = alarm.started - alarmbuf['lasttime']
                if delta.seconds <= int(seek_seconds):
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
        if len(alarmbuf['cluster'][cluster]) >= int(seek_min):
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
                            if nodes_down.groups()[0] >= int(nodes_min):
                                #Note a confirmed alarm
                                confirmed_alarms.append(str(sqa_id))
                                #Start analysing the traceroutes
                                problem_nodes = []
                                if 'mtr' in alarm.long:
                                    in_traceroute = None
                                    last_problem_node = None
                                    for line in alarm.long.splitlines():
                                        if in_traceroute == 1:
                                            line_parse = re.search(r'^\s+(\d+)\.\|--\s+(\S+)\s+(\S+)%\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$', line)
                                            if line_parse:
                                                # If you find a traceroute line with more than min packet loss, stash it
                                                # Next time we come around, if next line is non-zero also, then store it
                                                # We believe this makes the algorithm steenbergen compliant.
                                                if last_problem_node and float(line_parse.groups()[2]) > 0:
                                                    logging.debug("In cluster %s, on alarm %s and Found compliant problem node %s" % (cluster, sqa_id, last_problem_node))
                                                    problem_nodes.append(last_problem_node)
                                                    last_problem_node = None
                                                if int(line_parse.groups()[0]) > 1 and float(line_parse.groups()[2]) > int(trace_lmin):
                                                    logging.debug("In cluster %s, on alarm %s and Found potential problem node %s" % (cluster, sqa_id, line_parse.groups()[1]))
                                                    last_problem_node = line_parse.groups()[1]
                                            else:
                                                in_traceroute = None
                                        if 'mtr' in line or 'StDev' in line:
                                            in_traceroute = 1
                                if len(problem_nodes) > 1:
                                    # Find first problem node (which also isn't the only problem node), look up ASN and add to problem_asns for cluster
                                    problem_asns.append(find_asn(problem_nodes[0]))
            # Now summarise cluster issues
            if len(confirmed_alarms) > 0:
                logging.info("Cluster [%s], Alarms [%s], ASN list [%s]" % (cluster, ','.join(confirmed_alarms), pcnt_breakdown(problem_asns)))

           
    session.close()

# Look up ADN for an IP address using multiple means
def find_asn(ip):
    asn = find_asn_cymru(ip)
    if asn:
        return 'asn:' + asn
    else:
        netname = find_asn_whois(ip)
        if netname:
            return 'netname+' + netname
        else:
            return 'unknown'

# Look up ASN for an IP address against Cymru, only works if the IP space is routed
# Advantages = fast, cacheable
def find_asn_cymru(ip):
    logging.debug("called find_asn_cymru(%s)" % ip)
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
    except dns.resolver.NXDOMAIN:
        return None
    except:
        # Generic exception handler, should look at logging exceptions in the future TODO
        logging.error("some kind of exception in find_asn_cymru", exc_info=True)
        return None

# Look up ASN for an IP address against RADB instead
def find_asn_whois(ip):
    logging.debug("called find_asn_whois(%s)" % ip)
    for whois_server in whois_servers:
        msg = whois(whois_server, ip)
        if msg:
            m = re.search(r'(?i)netname:\s+(\S+)', msg)
            if m:
                # The RIPE, APNIC and LACNIC Responses for IPv6 space when it doesn't know and doesn't issue a referral
                if m.groups()[0] == 'IANA-BLK' or m.groups()[0] == 'ROOT':
                    continue
                return m.groups()[0]
    return None

def whois(server, ip):
    logging.debug("called whois(%s, %s)" % (server, ip))
    try:
        s = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        s.connect((server , 43))
        if server == 'whois.arin.net':
            s.send('n + ')
        s.send(ip + '\r\n')
        msg = ''
        while len(msg) < 10000:
            chunk = s.recv(100)
            if(chunk == ''):
                break
            msg = msg + chunk
        return msg
    except:
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
