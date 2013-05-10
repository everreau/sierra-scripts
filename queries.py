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
%s
WHERE d.content SIMILAR TO '%%201(3|2)%%' AND %s
GROUP BY rmb.record_num ORDER BY rmb.record_num DESC LIMIT 20"""

base_feed_q = """SELECT rmb.record_num as bib_num, brp.best_title as title, brp.best_author as author, MAX(isbn.content) as isbn, MAX(upc.content) as upc, cataloging_date_gmt 
FROM sierra_view.bib_record as b
LEFT JOIN sierra_view.record_metadata AS rmb ON (rmb.id = b.record_id AND rmb.record_type_code = 'b') 
LEFT JOIN sierra_view.bib_record_item_record_link AS bil ON (bil.bib_record_id = b.record_id AND bil.bibs_display_order = 0)
LEFT JOIN sierra_view.item_record AS i ON (bil.item_record_id = i.record_id)
LEFT JOIN sierra_view.subfield AS isbn ON (isbn.record_id = bil.bib_record_id AND isbn.marc_tag = '020' AND isbn.tag = 'a') 
LEFT JOIN sierra_view.subfield AS upc ON (upc.record_id = bil.bib_record_id AND upc.marc_tag = '024' AND upc.tag = 'a') 
LEFT JOIN sierra_view.subfield as d ON (b.record_id = d.record_id AND (d.marc_tag = '260' OR d.marc_tag = '264') and d.tag = 'c') 
LEFT JOIN sierra_view.bib_record_property AS brp ON (b.record_id = brp.bib_record_id)
%s
WHERE (current_date - cataloging_date_gmt::date) < %i AND d.content SIMILAR TO '%%201(3|2)%%' AND %s 
GROUP BY cataloging_date_gmt, rmb.record_num, brp.best_title, brp.best_author ORDER BY cataloging_date_gmt DESC"""

call_number = """LEFT JOIN sierra_view.subfield as c ON (b.record_id = c.record_id AND (c.marc_tag = '092') and c.tag = 'a')"""

encore_searches = { "adult-nonfiction": base_isbn_q,
                    "adult-audiobooks": base_isbn_q,
                    "adult-biographies": base_isbn_q,
                    "computer-books": base_isbn_q,
                    "graphic-novels": base_isbn_q,
                    "large-type-books": base_isbn_q,
                    "junior-high-fiction": base_isbn_q,
                    "teen-fiction": base_isbn_q,
                    "youth-audio": base_isbn_q,
                    "youth-fiction": base_isbn_q,
                    "youth-nonfiction": base_isbn_q,
                    "youth-picture-books": base_isbn_q,
                    "adult-fiction": base_isbn_q,
                    "adult-romances": base_isbn_q,
                    "adult-science-fiction": base_isbn_q,
                    "adult-mysteries": base_isbn_q,
                    "youth-dvds": base_upc_q,
                    "adult-cds": base_upc_q,
                    "adult-dvds": base_upc_q,
                    "video-games": base_upc_q}

joins = {"adult-nonfiction": """LEFT JOIN sierra_view.subfield as bad ON (b.record_id = bad.record_id AND bad.marc_tag = '022')""",
         "adult-fiction": call_number,
         "adult-romances": call_number,
         "adult-science-fiction": call_number,
         "adult-mysteries": call_number,
         "adult-nonfiction-dvds": call_number,
         "blu-rays": call_number,
         "tv-series-dvds": call_number}

where = { "adult-audiobooks": """(i.location_code = 'acdf' OR i.location_code = 'acdn')""",
          "adult-biographies": """language_code = 'eng' AND bcode2 = 'b' AND (i.location_code = 'abio' OR i.location_code = 'annw')""",
          "adult-cds": "language_code = 'eng' AND i.location_code = 'acd'",
          "computer-books" :"""i.location_code = 'ancp'""",          
          "adult-dvds": "language_code = 'eng' AND (i.location_code = 'advdf' OR i.location_code = 'advdn')",          
          "adult-feature-dvds": "language_code = 'eng' AND i.location_code LIKE '%advdf%'",
          "adult-fiction-audiobooks": "i.location_code LIKE '%acdf%'",
          "adult-fiction": """i.location_code = 'afnw' AND c.content LIKE 'FICTION%'""",
          "adult-graphic-novels": "i.location_code = 'anfg'",
          "large-type-books": """bcode2 = 'l'""",
          "adult-mysteries": """i.location_code = 'afnw' AND c.content LIKE 'MYSTERY%'""",
          "adult-nonfiction-audiobooks": "i.location_code LIKE '%acdn%'",
          "adult-nonfiction": """language_code = 'eng' AND bcode2 = 'n' AND i.location_code = 'annw' AND bad.record_id IS NULL""", 
          "adult-nonfiction-dvds": "i.location_code = 'advdn' AND (c.content < '791.4571' OR c.content > '791.4573')",
          "adult-romances":"""i.location_code = 'afnw' AND c.content LIKE 'ROMANCE%'""",
          "adult-science-fiction": """i.location_code = 'afnw' AND c.content LIKE 'SCIENCE FICTION%'""", 
          "adult-reference-books": "i.location_code LIKE '%arf%'",
          "blu-rays": "bcode2 = 'd' AND c.content LIKE '%BLU-RAY%'",
          "graphic-novels": """bcode2 = 'o'""",
          "junior-high-fiction": """NOT bcode2 = 'o' AND i.location_code = 'jfjh'""",
          "teen-fiction": """(i.location_code = 'aucf' OR i.location_code = 'zucf')""",
          "teen-graphic-novels-manga": "i.location_code = 'aucg'",
          "teen-video-games": "i.location_code = 'avg'",
          "tv-series-dvds": "i.location_code LIKE '%advdn%' AND c.content >= '791.4572' AND c.content < '791.4573'",
          "video-games": "bcode2 = 'm'",
          "youth-audio": """bcode2 = 'i' AND i.location_code LIKE 'jcd%'""",
          "youth-biographies": "(i.location_code = 'jbio' OR i.location_code = 'jbie')",
          "youth-dvds": "language_code = 'eng' AND i.location_code LIKE 'jdvd%'",
          "youth-easy-readers": "(i.location_code = 'jrd' OR i.location_code = 'jrdn')",
          "youth-feature-dvds": "i.location_code = 'jdvdf'",
          "youth-fiction-audiobooks": "i.location_code = 'jcdf'",
          "youth-fiction": """(i.location_code = 'jfic' OR i.location_code = 'jfcm')""",
          "youth-nonfiction": """(i.location_code = 'jnf' OR i.location_code = 'jnfe')""",
          "youth-picture-books": """bcode2 = 'p'""", 
          "youth-video-games": "i.location_code = 'jvg'"}

feeds = { "adult-biographies": {'title': "Adult Biographies", 'days': 30}, 
          "computer-books": {'title': "Computer Books", 'days': 30},
          "adult-cds": {'title': "Adult CDs", 'days': 30},
          "adult-feature-dvds": {'title': "Adult Feature DVDs", 'days': 30},
          "adult-fiction-audiobooks": {'title': "Adult Fiction Audiobooks", 'days': 30},
          "adult-fiction": {'title': "Adult Fiction", 'days': 30},
          "adult-graphic-novels": {'title': "Adult Graphic Novels", 'days': 90},
          "large-type-books": {'title': "Large Type Books", 'days': 30},
          "adult-mysteries": {'title': "Adult Mysteries", 'days': 30},
          "adult-nonfiction-audiobooks": {'title': "Adult Nonfiction Audiobooks", 'days': 45},
          "adult-nonfiction": {'title': "Adult Nonfiction", 'days': 30},
          "adult-nonfiction-dvds": {'title': "Adult Nonfiction DVDs", 'days': 90},
          "adult-reference-books": {'title': "Adult Reference Books", 'days': 60},
          "adult-romances": {'title': "Adult Romances", 'days': 30},
          "adult-science-fiction": {'title': "Adult Science Fiction", 'days': 30},
          "blu-rays": {'title': "Blu-rays", 'days': 60},
          "junior-high-fiction": {'title': "Junior High Fiction", 'days': 60},
          "teen-fiction": {'title': "Teen Fiction", 'days': 60},
          "teen-graphic-novels-manga": {'title': "Teen Graphic Novels & Manga", 'days': 90},
          "teen-video-games": {'title': "Teen Video Games", 'days': 90},
          "tv-series-dvds": {'title': "TV Series", 'days': 60},
          "youth-biographies": {'title': "Youth Biographies", 'days': 90},
          "youth-easy-readers": {'title': "Youth Easy Readers", 'days': 90},
          "youth-feature-dvds": {'title': "Youth Feature DVDs", 'days': 60},
          "youth-fiction-audiobooks": {'title': "Youth Fiction Audiobooks", 'days': 90},
          "youth-fiction": {'title': "Youth Fiction", 'days': 30},
          "youth-nonfiction": {'title': "Youth Nonfiction", 'days': 30},
          "youth-picture-books": {'title': "Youth Picture Books", 'days': 30},
          "youth-video-games": {'title': "Youth Video Games", 'days': 90}}
