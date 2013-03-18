#!/usr/bin/python2.7
#

import psycopg2
import urllib2
import re, os
import json

from settings import *

def img_url(url):
    try:
        imgstr = urllib2.urlopen(url).read()
        if len(imgstr) > 100:
            return url
    except IOError:
        print "IOError : " + url
    return None

def image_link(isbn, upc):
    pattern = re.compile("^([0-9X]*).*")
    url = None
    if isbn:
        m = pattern.search(isbn)
        if m: 
            url = img_url("http://origin.syndetics.com/index.php?isbn=%s/MC.gif" % m.group(1))
    if not url and upc:
        m = pattern.search(upc)
        if m: 
            url = img_url("http://plus.syndetics.com/index.php?isbn=/mc.gif&client=skopl&upc=%s" % m.group(1))
    return url

def write_json(cursor, q, args, filename):
    cursor.execute(q % ("(" + " OR ".join(map(lambda x: "ipn.name = '%s'" % x, args)) + ")"))
    rows = cursor.fetchall()
    result = []
    for r in rows:
        link = image_link(r[2], r[3])
        if link:
            result.append({'title': r[1], 'img_link': link, 'link': ('http://encore.skokielibrary.info/iii/encore/record/C__Rb' + unicode(r[0]))})
    f = open(filename, 'w')
    json.dump(result, f)
    f.close()

youth_fiction = [ "Juvenile Fiction" ]
adult_fiction = ["Adult Hot Pics", "Adult 14-day Fiction", "Adult Fiction", "Adult Most Wanted"]
adult_dvd = ["Adult DVD-Nonfiction", "Adult DVD-Feature"]

q = """SELECT bv.record_num as bib_num, 
              bv.title as title, 
              MAX(isbn.content) as isbn,
              MAX(upc.content) as upc 
       FROM sierra_view.item_record as i
       JOIN sierra_view.varfield AS barcode ON (barcode.record_id = i.id AND barcode.varfield_type_code = 'b') 
       JOIN sierra_view.bib_record_item_record_link AS bil ON ( bil.item_record_id = i.id AND bil.bibs_display_order = 0 ) 
       JOIN sierra_view.itype_property as ip ON (i.itype_code_num = ip.code_num)
       JOIN sierra_view.itype_property_name as ipn ON (ip.id = ipn.itype_property_id)
       JOIN sierra_view.bib_view as bv ON (bv.id = bil.bib_record_id)
       LEFT JOIN sierra_view.subfield AS isbn ON (isbn.record_id = bil.bib_record_id AND isbn.marc_tag='020' AND isbn.tag = 'a') 
       LEFT JOIN sierra_view.subfield AS upc ON (upc.record_id = bil.bib_record_id AND upc.marc_tag='024' AND upc.tag = 'a') 
       WHERE i.last_checkin_gmt::date = current_date AND i.item_status_code = '-' AND %s
       GROUP BY bib_num, title"""

try:
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' port='1032' password='%s' sslmode='require'" % (DB_NAME, DB_USER, DB_HOST, DB_PASSWORD,))
except psycopg2.Error as e:
    print "Unable to connect to database: " + unicode(e)

cursor = conn.cursor()

write_json(cursor, q, youth_fiction, "yf.json")
write_json(cursor, q, adult_fiction, "af.json")
write_json(cursor, q, adult_dvd, "advd.json")
