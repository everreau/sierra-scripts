#!/usr/bin/python2.7
#
# Send emails to everyone who placed a hold since the last time this script ran
# We've decommissioned this script for now because we are now able to customize 
# the message that appears in encore after a hold is placed.
#
#

import psycopg2
import smtplib

import datetime

from settings import *

try:
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' port='1032' password='%s' sslmode='require'" % (DB_NAME, DB_USER, DB_HOST, DB_PASSWORD,))
except psycopg2.Error as e:
    print "Unable to connect to database: " + unicode(e)

cursor = conn.cursor()

f = open("last_holds_timestamp.txt", "r")
last_timestamp = f.read()
f.close()

q = """SELECT rmb.record_num as bib_num,
              h.placed_gmt as t,
              e.content as email,
              COALESCE(s.content, v.field_content) as title
FROM sierra_view.hold as h 
JOIN sierra_view.subfield_view as e ON (h.patron_record_id = e.record_id AND e.record_type_code = 'p' AND e.field_type_code = 'z') 
JOIN sierra_view.record_metadata AS rmb ON (rmb.id = h.record_id AND rmb.record_type_code = 'b') 
LEFT JOIN sierra_view.subfield AS s ON (s.record_id = rmb.id AND s.marc_tag='245' AND s.tag = 'a') 
LEFT JOIN sierra_view.varfield AS v ON (v.record_id = rmb.id AND v.varfield_type_code = 't' AND v.marc_tag IS NULL)
WHERE NOT h.is_ill AND placed_gmt > timestamp '%s' 
UNION
SELECT rmb.record_num as bib_num, 
       h.placed_gmt as t,
       e.content as email,  
       COALESCE(s.content, v.field_content) as title
FROM sierra_view.hold as h 
JOIN sierra_view.subfield_view as e ON (h.patron_record_id = e.record_id AND e.record_type_code = 'p' AND e.field_type_code = 'z') 
JOIN sierra_view.record_metadata AS rmi ON (rmi.id = h.record_id AND rmi.record_type_code = 'i') 
JOIN sierra_view.bib_record_item_record_link AS bil ON (bil.item_record_id = rmi.id AND bil.bibs_display_order = 0) 
LEFT JOIN sierra_view.subfield AS s ON (s.record_id = bil.bib_record_id AND s.marc_tag='245' AND s.tag = 'a') 
LEFT JOIN sierra_view.varfield AS v ON (v.record_id = bil.bib_record_id AND v.varfield_type_code = 't' AND v.marc_tag IS NULL)
JOIN sierra_view.record_metadata AS rmb ON (rmb.id = bil.bib_record_id AND rmb.record_type_code = 'b')
WHERE NOT h.is_ill AND placed_gmt > timestamp '%s'""" % (unicode(last_timestamp), unicode(last_timestamp),)

cursor.execute(q)
rows = cursor.fetchall()

cursor.close()
conn.close()

emails = {}

for r in rows:
    if last_timestamp == None or unicode(r[1]) > last_timestamp:
        last_timestamp = unicode(r[1])
    if r[3] != None:
        if r[2] in emails:
            emails[r[2]].append((r[3].strip(" :/."), r[0],))
        else:
            emails[r[2]] = [(r[3].strip(" :/."), r[0],)]

f = open("last_holds_timestamp.txt", "w")
f.write(unicode(last_timestamp))
f.close()

for email in emails:
    sender = CIRC_EMAIL
    receivers = [email]

    message = """From: %s
To: %s
Subject: Skokie Public Library Hold Confirmations

Skokie Public Library has received your hold request. Please wait until you are notified by email/phone that your item (s) is ready to be picked up.

""" % (sender, " ".join(receivers),)

    for info in emails[email]:
        message += "\t%s: http://encore.skokielibrary.info/iii/encore/record/C__Rb%s\n" % info

    try:
        smtp = smtplib.SMTP(EMAIL_HOST)
        smtp.sendmail(sender, receivers, message)         
    except smtplib.SMTPException:
        print "Unable to send email: %s" % " ".join(receivers)
