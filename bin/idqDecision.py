#!/usr/bin/python
import json
import sys

import numpy as np

from ligo.gracedb.rest import GraceDb

#=================================================

ifos = ["H1", "L1"]

jFAP_thr = 1e-2

annotate_gracedb = True

allowed_pipelines = ['cwb', 'lib']

#=================================================

gdb = GraceDb()

alert = json.loads( sys.stdin.read() )

if alert['alert_type'] != 'update':
    print "not an update alert"
    sys.exit(0)
elif 'minimum glitch-FAP for' not in alert['object']['comment']:
    print "not a iDQ glitch-FAP update"
    print alert['object']['comment']
    sys.exit(0)

gid = alert['uid']
print "graceid : "+gid

labels = [label['name'] for label in gdb.labels( gid ).json()['labels'] ]
print "labels : "+", ".join(labels)
if "DQV" in labels:
    print "already labeled DQV"
    sys.exit(0)

event = gdb.event( gid ).json()
print "pipeline : "+event['pipeline']
if event['pipeline'].lower() not in allowed_pipelines:
    print "  not allowed to label this pipeline"
    sys.exit(1)

logs = gdb.logs( gid ).json()['log']
result = dict( (ifo, 1) for ifo in ifos )
for log in logs: 
    comment = log['comment']
    if "minimum glitch-FAP for" in comment:
        gFAP = float(comment.split()[-1])
        for ifo in ifos:
            if ifo in comment:
                result[ifo] = gFAP
                break

jFAP = np.prod( result.values() ) ### take product of gFAPs for 2 IFOs

if jFAP <= jFAP_thr:
    message = "iDQ veto generator computed joint glitch-FAP : %.3e <= %.3e; <b>This is probably a glitch</b> and I am applying a DQV label"%(jFAP, jFAP_thr)
    if annotate_gracedb:
        gdb.writeLabel( gid, 'DQV' )
        gdb.writeLog( gid, message=message, tagname=['data_quality'] )
    print message
else:
    message = "iDQ veto generator computed joint glitch-FAP : %.3e > %.3e; <b>This is probably not a glitch</b> and I am not applying a label"%(jFAP, jFAP_thr)
    if annotate_gracedb:
        gdb.writeLog( gid, message=message, tagname=['data_quality'] )
    print message
