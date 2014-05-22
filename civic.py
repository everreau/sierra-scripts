#!/usr/bin/python2.7
#
# Export information about daily checkouts as required by Civic Technologies and send to contact person
#
#

import psycopg2
import datetime
import os

import smtplib
import string

from email import Encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formatdate

from settings import *

def strify(obj):
    if obj == None:
        return '\"\"'
    else:
        return "\"%s\"" % str(obj)

title_row = "\"RECORD #(PATRON)\",\"OUT DATE\",\"LOCATION\",\"MAT TYPE\",\"OUT LOC\",\"RECORD #(ITEM)\",\"CALL #(BIBLIO)\",\"OCLC #\",\"RECORD #(BIBLIO)\",\"LCCN\",\"LANG\""
q = """SELECT 'p' || rmp.record_num || 'a' as patron_record_num, 
       to_char(c.checkout_gmt,'MM-DD-YYYY HH:MI') as checkout_date, 
       i.location_code as item_location, 
       brp.material_code as material_type, 
       i.checkout_statistic_group_code_num as item_checkout_location,
       'i' || rmi.record_num || 'a',
       COALESCE(cn1.content, cn2.field_content) as call_number, 
       oclc.field_content as oclc_number, 
       'b' || rmb.record_num || 'a' AS bib_record_number, 
       COALESCE(lccn2.content, lccn1.field_content) as lccn, 
       b.language_code as language
FROM sierra_view.checkout as c 
JOIN sierra_view.record_metadata AS rmp ON (rmp.id = c.patron_record_id AND rmp.record_type_code = 'p')
JOIN sierra_view.item_record AS i ON (i.id = c.item_record_id)
JOIN sierra_view.record_metadata AS rmi ON ( rmi.id = i.id AND rmi.record_type_code = 'i') 
LEFT JOIN sierra_view.bib_record_item_record_link AS bil ON (bil.item_record_id = i.id)
LEFT JOIN sierra_view.bib_record_property AS brp ON (brp.bib_record_id = bil.bib_record_id)
LEFT JOIN sierra_view.subfield AS cn1 ON (cn1.record_id = bil.bib_record_id AND cn1.marc_tag='092' AND cn1.tag = 'a')
LEFT JOIN sierra_view.varfield AS cn2 ON (cn2.record_id = bil.bib_record_id AND cn2.marc_tag='092')
LEFT JOIN sierra_view.varfield AS oclc ON (oclc.record_id = bil.bib_record_id AND oclc.marc_tag='001')
LEFT JOIN sierra_view.record_metadata as rmb ON (rmb.id = bil.bib_record_id AND rmb.record_type_code = 'b')
LEFT JOIN sierra_view.varfield AS lccn1 ON (lccn1.record_id = bil.bib_record_id AND lccn1.marc_tag='010')
LEFT JOIN sierra_view.subfield AS lccn2 ON (lccn2.record_id = bil.bib_record_id AND lccn2.marc_tag='010' AND lccn2.tag = 'a')
JOIN sierra_view.bib_record as b ON (b.record_id = bil.bib_record_id)
WHERE c.checkout_gmt::date = current_date"""

try:
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' port='1032' password='%s' sslmode='require'" % (DB_NAME, DB_USER, DB_HOST, DB_PASSWORD,))
except psycopg2.Error as e:
    print "Unable to connect to database: " + unicode(e)

cursor = conn.cursor()

os.chdir(CIVIC_DIR)

archive_limit = datetime.datetime.today() - datetime.timedelta(days=60)

for f in os.listdir("."):
    fullpath = os.path.abspath(f)
    ctime = datetime.datetime.fromtimestamp(os.stat(fullpath).st_ctime)
    if ctime < archive_limit and f.endswith(".csv"):
        print "deleting: " + fullpath
        os.remove(fullpath)

filename = ("skokie_checkouts_%s.csv" % datetime.date.today().strftime("%Y%m%d"))

cursor.execute(q)
rows = cursor.fetchall()
    
f = open(filename, "w")

f.write(title_row)
f.write("\n")
    
for r in rows:
    f.write(",".join(map(strify, r)))
    f.write("\n")
        
f.close()

SUBJECT = "Civic Technologies Checkout Data File"

msg = MIMEMultipart()
msg["From"] = CIVIC_FROM
msg["To"] = CIVIC_TO
msg["Subject"] = SUBJECT
msg["Date"] = formatdate(localtime=True)

part = MIMEBase('application', "octet-stream")
part.set_payload(open(filename, "rb").read())
Encoders.encode_base64(part)
part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(filename))
msg.attach(part)

server = smtplib.SMTP(EMAIL_HOST)

try:
    failed = server.sendmail(msg["From"], msg["To"], msg.as_string())
    server.close()
except Exception, e:
    msg = "Unable to send email. Error: %s" % str(e)
