import json
from urllib import request
import os
from datetime import datetime
import re

req = request.Request("https://www.duquesnelight.com/outages-safety/current-outages/GetReportedOutages/")
response = request.urlopen(req)
data = json.loads(response.read())

for outage_group in data.get("OutageGroups", []):
    if outage_group["Municipality"]["Zip"] == "15213":
        affected = outage_group["Affected"]
        m = re.search("(\d+)", outage_group["LastUpdated"])
        time = datetime.utcfromtimestamp(int(m.group(0)) / 1000).strftime("%I:%M %p")

        if affected > 50:
            data = {
                'text': "As of %s, there are %i Duquesne Light customers without power in 15213." % (time, affected),
                'username': "lightbot"
            }
            data = json.dumps(data)
            data = str(data)
            data = data.encode('utf-8')

            req = request.Request(os.environ['SLACK_WEBHOOK_URL'], data=data)
            resp = request.urlopen(req)
