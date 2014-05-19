#!/usr/bin/python2.7
#

import psycopg2
import datetime
import os

from ftplib import  FTP
import smtplib
from email.mime.text import MIMEText

from settings import *

def strify(obj):
    if obj == None:
        return ''
    else:
        return "%s" % str(obj)

def put_file(ftp, filename, directory):
    try:
        if filename != None:
            print "sending " + filename
            f = open(filename, 'rb')
            ftp.storbinary(("STOR /%s/%s" % (directory, filename,)), f)
            f.close()
    except Exception, e:
        print e

title_row = 'itemid\tisbn\tbibrecordcallno\tbibrecordid\ttitle'
q = """SELECT ib.field_content as barcode, 
              COALESCE(isbn.content, upc.content) as isbn_field,
              COALESCE(cn1.content, cn2.field_content) as call_number, 
              'b' || rmb.record_num || 'a' as bib_num, 
              brp.best_title as title
FROM sierra_view.bib_record as b
LEFT JOIN sierra_view.record_metadata AS rmb ON (rmb.id = b.record_id AND rmb.record_type_code = 'b') 
LEFT JOIN sierra_view.bib_record_item_record_link AS bil ON (bil.bib_record_id = b.record_id AND bil.bibs_display_order = 0)
LEFT JOIN sierra_view.item_record AS i ON (bil.item_record_id = i.record_id)
LEFT JOIN sierra_view.varfield AS ib ON (ib.record_id = i.id AND ib.varfield_type_code = 'b') 
LEFT JOIN sierra_view.subfield AS isbn ON (isbn.record_id = bil.bib_record_id AND isbn.marc_tag = '020' AND isbn.tag = 'a') 
LEFT JOIN sierra_view.subfield AS upc ON (upc.record_id = bil.bib_record_id AND upc.marc_tag = '024' AND upc.tag = 'a') 
LEFT JOIN sierra_view.bib_record_property AS brp ON (b.record_id = brp.bib_record_id)
LEFT JOIN sierra_view.subfield AS cn1 ON (cn1.record_id = bil.bib_record_id AND cn1.marc_tag='092' AND cn1.tag = 'a')
LEFT JOIN sierra_view.varfield AS cn2 ON (cn2.record_id = bil.bib_record_id AND cn2.marc_tag='092')
WHERE LENGTH(ib.field_content) >= 10 AND NOT (isbn.content IS NULL AND upc.content IS NULL)"""

try:
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' port='1032' password='%s' sslmode='require'" % (DB_NAME, DB_USER, DB_HOST, DB_PASSWORD,))
except psycopg2.Error as e:
    print "Unable to connect to database: " + unicode(e)

cursor = conn.cursor()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
files = os.listdir(os.path.dirname(os.path.abspath(__file__)))
for f in files:
    if f.startswith("Skokie-3M-"):
        os.remove(f)

filename = ("Skokie-3M-%s-ISBNs.txt" % datetime.date.today().strftime("%Y%m%d"))

cursor.execute(q)
rows = cursor.fetchall()
    
f = open(filename, "w")

f.write(title_row)
f.write("\n")
    
for r in rows:
    f.write("\t".join(map(strify, r)))
    f.write("\n")
        
f.close()

try:
    ftp = FTP(NOVELIST_HOST)
    ftp.login(NOVELIST_USER, NOVELIST_PASSWORD)

    put_file(ftp, filename, "/skokie/")

    ftp.quit()
    message = "%s successfully uploaded to novelist." % filename
except Exception, e:
    print e
    message = "Novelist upload failed: %s." % unicode(e)

msg = MIMEText(message)

msg['Subject'] = "Novelist Select Item Export"
msg['From'] = NOVELIST_FROM
msg['To'] = NOVELIST_NOTIFICATION

s = smtplib.SMTP(EMAIL_HOST)
s.sendmail(msg['From'], [msg['To']], msg.as_string())
s.quit()
