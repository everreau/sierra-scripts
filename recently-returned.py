#!/usr/bin/python2.7
#

import psycopg2
import urllib2
import re, os
import json

from settings import *
from queries import *

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

def write_json(cursor, filename, title, q):
    cursor.execute(q)
    rows = cursor.fetchall()
    result = []
    for r in rows:
        link = image_link(r[3], r[4])
        if link:
            result.append({'title': r[1], 'img_link': link, 'link': ('http://encore.skokielibrary.info/iii/encore/record/C__Rb' + unicode(r[0]))})
    f = open("%s.json" % filename, 'w')
    json.dump(result, f)
    f.close()

try:
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' port='1032' password='%s' sslmode='require'" % (DB_NAME, DB_USER, DB_HOST, DB_PASSWORD,))
except psycopg2.Error as e:
    print "Unable to connect to database: " + unicode(e)

cursor = conn.cursor()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

for f in feeds:
    feed = feeds[f]
    write_json(cursor, f, feed['title'], base_feed_q % ((joins[f] if f in joins else ""), feed['days'], where[f]))
