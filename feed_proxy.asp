<%
feed_name = Request.QueryString("feed")
url = "http://artemis.skokielibrary.info/new-feeds/" & feed_name & ".xml"

dim xml_http
set xml_http = Server.CreateObject("Microsoft.XMLHTTP")
xml_http.open "GET", url, false
xml_http.send

set xml_doc = Server.CreateObject("Microsoft.XMLDOM")
xml_doc.async = false
xml_doc.LoadXml(xml_http.responseText)

if xml_doc.parseError.errorcode<>0 then
	response.write xml_doc.parseError.reason
else
    Session.CodePage = 65001
	response.CharSet = "utf-8"
	response.ContentType = "application/xml"
	response.write xml_doc.xml
end if

set xml_http = nothing
set xml_doc = nothing
%>