import psycopg2

from settings import *

try:
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' port='1032' password='%s' sslmode='require'" % (DB_NAME, DB_USER, DB_HOST, DB_PASSWORD,))
except psycopg2.Error as e:
    print "Unable to connect to database: " + unicode(e)

cursor = conn.cursor()

q = """SELECT * FROM (SELECT i.location_code, COUNT(*) FROM sierra_view.checkout as c LEFT JOIN sierra_view.item_record as i ON (i.id = c.item_record_id) GROUP BY i.location_code) as x JOIN (SELECT i.location_code, COUNT(*) FROM sierra_view.item_record as i GROUP BY i.location_code) as y ON (x.location_code = y.location_code) ORDER BY x.location_code"""

cursor.execute(q)
rows = cursor.fetchall()

f = open("percent_out.csv", "w")
    
for r in rows:
    f.write(",".join(map(unicode, r)))
    f.write("\n")

f.close()

conn.close()
