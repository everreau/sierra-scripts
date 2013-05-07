import psycopg2
import PyRSS2Gen
import xml.etree.ElementTree as ET

import re, os
import datetime
import urllib2

from settings import *
from queries import *

def read_summary(url):
    summary = ""
    f = urllib2.urlopen(url)
    xml = f.read()
    f.close()
    try:
        root = ET.fromstring(xml)
        for i in root.iter("Fld520"):
            summary = i[0].text[:500]
            if len(i[0].text) > 500:
                summary += ("... <a href='%s'>read more</a>" % url)
    except:
        pass
    return summary

def get_summary(isbn, upc):
    summary = ""
    if isbn != None:
        summary = read_summary("http://www.syndetics.com/index.aspx?isbn=%s/summary.xml&client=skopl" % isbn)
    if len(summary) < 1 and upc != None:
        summary = read_summary("http://plus.syndetics.com/index.php?isbn=/avsummary.xml&client=skopl&upc=%s" % upc)
    return summary

def test_img_url(url):
    try:
        imgstr = urllib2.urlopen(url).read()
        if len(imgstr) > 100:
            return url
    except IOError:
        print "IOError : " + url
    return None

def image_url(isbn, upc):
    img_link = None
    if not isbn == None:
        img_link = test_img_url("http://www.syndetics.com/index.aspx?isbn=%s/SC.GIF&client=skopl" % isbn)
    if not img_link and not upc == None:
        img_link = test_img_url("http://plus.syndetics.com/index.php?isbn=/sc.gif&client=skopl&upc=%s" % upc)
    return img_link

def write_rss(cursor, filename, title, q):
    cursor.execute(q)
    rows = cursor.fetchall()

    rss = PyRSS2Gen.RSS2(
        title = "New %s at Skokie Public Library" % title,
        link = "http://encore.skokielibrary.info",
        description = "These are the lastest titles added to the collection",
        language = "eng",
        lastBuildDate = datetime.datetime.now(),
        items = [])

    for r in rows:
          item = PyRSS2Gen.RSSItem(
            title = "%s / %s" % (r[1], r[2]) if r[2] and len(r[2]) > 0 else r[1],
            link = "http://encore.skokielibrary.info/iii/encore/record/C__Rb%s" % r[0],
            description = """<p><img src="%s" align="left" style="margin: 5px;">%s</p>""" % (image_url(r[3], r[4]), get_summary(r[3], r[4]),),
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

for filename in isbn_info:
    info = isbn_info[filename]
    p = isbn_qs[filename]
    p.insert(1, info['days'])
    q = (base_feed_q % tuple(p))
    write_rss(cursor, filename, info['title'], q)

for filename in upc_info:
    info = upc_info[filename]
    write_rss(cursor, filename, info['title'], base_feed_q % ("", info['days'], upc_qs[filename],))
