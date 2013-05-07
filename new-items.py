import psycopg2
import re, os

from settings import *

from queries import *

def do_it(cursor, filename, q):
    pattern = re.compile("([0-9X]*)")

    cursor.execute(q)
    rows = cursor.fetchall()

    f = open("%s.txt" % filename, "w")
    f.write(" | ".join(map(lambda x: pattern.match(x[0]).group(1), filter(lambda x: type(x[0]) == str, rows))))
    f.close()

try:
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' port='1032' password='%s' sslmode='require'" % (DB_NAME, DB_USER, DB_HOST, DB_PASSWORD,))
except psycopg2.Error as e:
    print "Unable to connect to database: " + unicode(e)

cursor = conn.cursor()

os.chdir(os.getcwd())

for filename in isbn_qs:
    do_it(cursor, filename, base_isbn_q % tuple(isbn_qs[filename]))

for filename in upc_qs:
    do_it(cursor, filename, base_upc_q % upc_qs[filename])
