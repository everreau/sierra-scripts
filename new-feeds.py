import psycopg2
import PyRSS2Gen
import xml.etree.ElementTree as ET

import re, os
import datetime
import urllib2

from settings import *
from queries import *

def write_rss(cursor, filename, q, img_url, img_field, summary_url):
    cursor.execute(q)
    rows = cursor.fetchall()

    rss = PyRSS2Gen.RSS2(
        title = "New %s at Skokie Public Library" % filename,
        link = "http://encore.skokielibrary.info",
        description = "These are the lastest titles added to the collection",
        language = "eng",
        lastBuildDate = datetime.datetime.now(),
        items = [])

    for r in rows:
        summary = ""
        f = urllib2.urlopen(summary_url % r[img_field])
        xml = f.read()
        f.close()
        try:
            root = ET.fromstring(xml)
            summary = ""
            for i in root.iter("Fld520"):
                summary = i[0].text[:1000]
                if len(i[0].text) > 1000:
                    summary += ("... <a href='http://www.syndetics.com/index.aspx?isbn=%s/summary.html&client=skopl'>read more</a>" % r[3])
            item = PyRSS2Gen.RSSItem(
                title = r[1],
                link = "http://encore.skokielibrary.info/iii/encore/record/C__Rb%s" % r[0],
                description = """<p><img src="%s" align="left" style="margin: 5px;">%s</p>""" % ((img_url % r[img_field]), summary,),
                guid = PyRSS2Gen.Guid(r[3])
                )
            rss.items.append(item)
        except: #if something goes wrong with the syndetics stuff just put a generic entry
            item = PyRSS2Gen.RSSItem(
                title = r[1],
                link = "http://encore.skokielibrary.info/iii/encore/record/C__Rb%s" % r[0],
                description = """<p><img src="%s" align="left" style="margin: 5px;"></p>""" % (img_url % r[img_field]),
                guid = PyRSS2Gen.Guid(r[3])
                )
            rss.items.append(item) 

    f = open("%s.xml" % filename, "w")
    rss.write_xml(f, encoding='utf-8')
    f.close()

try:
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' port='1032' password='%s' sslmode='require'" % (DB_NAME, DB_USER, DB_HOST, DB_PASSWORD,))
except psycopg2.Error as e:
    print "Unable to connect to database: " + unicode(e)

cursor = conn.cursor()

os.chdir(os.getcwd())

for filename in isbn_qs:
    write_rss(cursor, filename, base_book_feed_q % isbn_qs[filename], "http://www.syndetics.com/index.aspx?isbn=%s/SC.GIF&client=skopl", 3, "http://www.syndetics.com/index.aspx?isbn=%s/summary.xml&client=skopl")

for filename in upc_qs:
    write_rss(cursor, filename, base_av_feed_q % upc_qs[filename], "http://plus.syndetics.com/index.php?isbn=/sc.gif&client=skopl&upc=%s", 4, "http://plus.syndetics.com/index.php?isbn=/avsummary.xml&client=skopl&upc=%s")

