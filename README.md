# ring-sqa-collector
NLNOG Ring SQA Collector

Config file is sqa_collector.conf

```
[output] 		<-- section defining HTML output for the collector 
max_results = 9999	<-- maximum results to display
per_page = 50		<-- and per page

[database]		<-- Section defining the database
connection_string = mysql://sqa_collector:sqa_collector@localhost/sqa_collector		<--- Database connection string
pool_recycle = 3600	<-- Database pool recycle seconds, this means all handles 
			    recycled after an hour, important for flaky databases, default for mysql

[correlator]		<-- section for the correlator
log_file = /var/log/sqa_correlator.log <-- logfile for the correlator
seek_hours = 2 		<-- how many hours to look back in window
seek_seconds = 60	<-- max delta time in seconds between alarms to consider them part of an event
seek_min = 10		<-- event must have this minimum number of alarms inside it to be a real event
nodes_min = 10		<-- an alarm must have this minimum number of affected nodes
trace_lmin = 10		<-- min packet loss to consider a traceroute to have a relevant alarm inside it
whois_servers = whois.ripe.net, whois.radb.net, whois.arin.net, whois.apnic.net, whois.lacnic.net, whois.afrinic.net  <-- whois servers to use
```
