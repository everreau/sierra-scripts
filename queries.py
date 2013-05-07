base_isbn_q = """SELECT MAX(isbn.content) as isbn
FROM sierra_view.bib_record as b
LEFT JOIN sierra_view.record_metadata AS rmb ON (rmb.id = b.record_id AND rmb.record_type_code = 'b') 
LEFT JOIN sierra_view.bib_record_item_record_link AS bil ON (bil.bib_record_id = b.record_id AND bil.bibs_display_order = 0)
LEFT JOIN sierra_view.item_record AS i ON (bil.item_record_id = i.record_id)
JOIN sierra_view.subfield AS isbn ON (isbn.record_id = bil.bib_record_id AND isbn.marc_tag = '020') 
LEFT JOIN sierra_view.subfield as d ON (b.record_id = d.record_id AND (d.marc_tag = '260' OR d.marc_tag = '264') and d.tag = 'c')
%s
WHERE d.content SIMILAR TO '%%201(3|2)%%' AND %s
GROUP BY rmb.record_num ORDER BY rmb.record_num DESC LIMIT 20"""

base_upc_q = """SELECT MAX(upc.content) as upc
FROM sierra_view.bib_record as b
LEFT JOIN sierra_view.record_metadata AS rmb ON (rmb.id = b.record_id AND rmb.record_type_code = 'b') 
LEFT JOIN sierra_view.bib_record_item_record_link AS bil ON (bil.bib_record_id = b.record_id AND bil.bibs_display_order = 0)
LEFT JOIN sierra_view.item_record AS i ON (bil.item_record_id = i.record_id)
JOIN sierra_view.subfield AS upc ON (upc.record_id = bil.bib_record_id AND upc.marc_tag = '024' AND tag = 'a') 
LEFT JOIN sierra_view.subfield as d ON (b.record_id = d.record_id AND (d.marc_tag = '260' OR d.marc_tag = '264') and d.tag = 'c') 
WHERE d.content SIMILAR TO '%%201(3|2)%%' AND %s
GROUP BY rmb.record_num ORDER BY rmb.record_num DESC LIMIT 20"""

base_feed_q = """SELECT rmb.record_num as bib_num, brp.best_title as title, brp.best_author as author, MAX(isbn.content) as isbn, MAX(upc.content) as upc, cataloging_date_gmt 
FROM sierra_view.bib_record as b
LEFT JOIN sierra_view.record_metadata AS rmb ON (rmb.id = b.record_id AND rmb.record_type_code = 'b') 
LEFT JOIN sierra_view.bib_record_item_record_link AS bil ON (bil.bib_record_id = b.record_id AND bil.bibs_display_order = 0)
LEFT JOIN sierra_view.item_record AS i ON (bil.item_record_id = i.record_id)
LEFT JOIN sierra_view.subfield AS isbn ON (isbn.record_id = bil.bib_record_id AND isbn.marc_tag = '020') 
LEFT JOIN sierra_view.subfield AS upc ON (upc.record_id = bil.bib_record_id AND upc.marc_tag = '024' AND upc.tag = 'a') 
LEFT JOIN sierra_view.subfield as d ON (b.record_id = d.record_id AND (d.marc_tag = '260' OR d.marc_tag = '264') and d.tag = 'c') 
LEFT JOIN sierra_view.bib_record_property AS brp ON (b.record_id = brp.bib_record_id)
%s
WHERE (current_date - cataloging_date_gmt::date) < %i AND d.content SIMILAR TO '%%201(3|2)%%' AND %s 
GROUP BY cataloging_date_gmt, rmb.record_num, brp.best_title, brp.best_author ORDER BY cataloging_date_gmt DESC"""

call_number = """LEFT JOIN sierra_view.subfield as c ON (b.record_id = c.record_id AND (c.marc_tag = '092') and c.tag = 'a')"""

isbn_qs = { "adult-nonfiction":
                ["""LEFT JOIN sierra_view.subfield as bad ON (b.record_id = bad.record_id AND bad.marc_tag = '022')""",
                 """language_code = 'eng' AND bcode2 = 'n' AND i.location_code = 'annw' AND bad.record_id IS NULL"""], 
            "adult-audiobooks": ["", """(i.location_code = 'acdf' OR i.location_code = 'acdn')"""],
            "adult-biographies":["", """language_code = 'eng' AND bcode2 = 'b' AND (i.location_code = 'abio' OR i.location_code = 'annw')"""],
            "computer-books":["", """i.location_code = 'ancp'"""],
            "graphic-novels":["", """i.location_code = 'anfg'"""],
            "large-type-books":["", """bcode2 = 'l'"""],
            "junior-high-fiction":["", """NOT bcode2 = 'o' AND i.location_code = 'jfjh'"""],
            "teen-fiction":["", """(i.location_code = 'aucf' OR i.location_code = 'zucf')"""],
            "youth-audio":["", """bcode2 = 'i' AND i.location_code LIKE 'jcd%'"""],
            "youth-fiction":["", """(i.location_code = 'jfic' OR i.location_code = 'jfcm')"""],
            "youth-nonfiction":["", """(i.location_code = 'jnf' OR i.location_code = 'jnfe')"""],
            "youth-picture-books":["", """bcode2 = 'p'"""],
            "adult-fiction":[call_number, """i.location_code = 'afnw' AND c.content LIKE 'FICTION%'"""],
            "adult-romances":[call_number, """i.location_code = 'afnw' AND c.content LIKE 'ROMANCE%'"""],
            "adult-science-fiction":[call_number, """i.location_code = 'afnw' AND c.content LIKE 'SCIENCE FICTION%'"""], 
            "adult-mysteries": [call_number, """i.location_code = 'afnw' AND c.content LIKE 'MYSTERY%'"""]}

upc_qs =  { "youth-dvds": "language_code = 'eng' AND i.location_code LIKE 'jdvd%'",
            "adult-cds": "language_code = 'eng' AND i.location_code = 'acd'",
            "adult-dvds": "language_code = 'eng' AND (i.location_code = 'advdf' OR i.location_code = 'advdn')",
            "video-games": "bcode2 = 'm'"}


isbn_info = { "adult-biographies": {'title': "Adult Biographies", 'days': 30}, 
              "computer-books": {'title': "Computer Books", 'days': 30},
              "adult-nonfiction": {'title': "Adult Nonfiction", 'days': 30},
            "adult-audiobooks": {'title': "Adult Audiobooks", 'days': 30},            
            "graphic-novels": {'title': "Graphic Novels", 'days': 90},
            "large-type-books": {'title': "Large Type Books", 'days': 30},
            "junior-high-fiction": {'title': "Junior High Fiction", 'days': 60},
            "teen-fiction": {'title': "Teen Fiction", 'days': 60},
            "youth-audio": {'title': "Youth Audiobooks", 'days': 30},
            "youth-fiction": {'title': "Youth Fiction", 'days': 30},
            "youth-nonfiction": {'title': "Youth Nonfiction", 'days': 30},
            "youth-picture-books": {'title': "Youth Picture Books", 'days': 30},
            "adult-fiction": {'title': "Adult Fiction", 'days': 30},
            "adult-romances": {'title': "Adult Romances", 'days': 30},
            "adult-science-fiction": {'title': "Adult Science Fiction", 'days': 30},
            "adult-mysteries": {'title': "Adult Mysteries", 'days': 30}}

upc_info =  { "adult-cds": {'title': "Adult CDs", 'days': 30},

"youth-dvds": {'title': "Youth DVDs", 'days': 30},
              
              "adult-dvds": {'title': "Adult DVDs", 'days': 30},
              "video-games": {'title': "Video Games", 'days': 60}}
