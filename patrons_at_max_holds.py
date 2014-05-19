#!/usr/bin/python2.7
#
# Collect number of patrons at max holds and who those patrons are
#
# We used this script temporarily to determine if it made sense to raise the holds limit
# Not currently in use
#
#

import psycopg2

from settings import *

try:
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' port='1032' password='%s' sslmode='require'" % (DB_NAME, DB_USER, DB_HOST, DB_PASSWORD,))
except psycopg2.Error as e:
    print "Unable to connect to database: " + unicode(e)

cursor = conn.cursor()

q = """SELECT current_date, count(*), avg(current_date - last_hold) FROM (SELECT patron_record_id, MAX(placed_gmt::date) as last_hold FROM sierra_view.hold WHERE NOT is_ill GROUP BY patron_record_id HAVING count(*) >= 15) as h LEFT JOIN sierra_view.patron_record as p ON (h.patron_record_id = p.id) WHERE NOT p.ptype_code = 15"""

cursor.execute(q)
rows = cursor.fetchall()

f = open("max_holds.csv", "a")

for r in rows:
    f.write(",".join(map(unicode,r)))
    f.write("\n")

f.close()

q = """
SELECT current_date, patron_record_id, (current_date - MAX(placed_gmt::date)) as wait_time 
FROM sierra_view.hold as h, sierra_view.patron_record as p
WHERE h.patron_record_id = p.id AND NOT h.is_ill AND NOT p.ptype_code = 15 
GROUP BY patron_record_id 
HAVING count(*) >= 15
"""

cursor.execute(q)
rows = cursor.fetchall()

f = open("patrons_at_max_holds.csv", "a")

for r in rows:
    f.write(",".join(map(unicode,r)))
    f.write("\n")

f.close()


