import base64
import hashlib
import json
from urllib import request, parse
import os
from datetime import datetime
from pytz import timezone

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
INCIDENT_TYPES = {
        "AA": "Auto Aid",
        "AC": "Aircraft Crash",
        "AE": "Aircraft Emergency",
        "AF": "Appliance Fire",
        "AED": "AED",
        "AES": "Aircraft Emergency Standby",
        "AI": "Arson Investigation",
        "AR": "Animal Rescue",
        "BT": "Bomb Threat",
        "CA": "Community Activity",
        "CB": "Controlled Burn/Prescribed Fire",
        "CF": "Commercial Fire",
        "CHIM": "Chimney Fire",
        "CL": "Commercial Lockout",
        "CMA": "Carbon Monoxide",
        "CR": "Cliff Rescue",
        "CSR": "Confined Space",
        "EE": "Electrical Emergency",
        "EF": "Extinguished Fire",
        "ELF": "Electrical Fire",
        "ELR": "Elevator Rescue",
        "EM": "Emergency",
        "EQ": "Earthquake",
        "ER": "Emergency Response",
        "EX": "Explosion",
        "FA": "Fire",
        "FIRE": "Fire",
        "FL": "Flooding",
        "FLW": "Flood Warning",
        "FULL": "Full Assignment",
        "FW": "Fire Watch",
        "GAS": "Gas Leak",
        "GF": "Garbage Fire",
        "HC": "Hazard Condition",
        "HMI": "Hazmat Investigation",
        "HMR": "Hazmat Response",
        "IF": "Illegal Fire",
        "IFT": "Interfacility Transfer",
        "INV": "Investigation",
        "LA": "Lift Assist",
        "LO": "Lockout",
        "LR": "Ladder Request",
        "LZ": "Landing Zone",
        "MA": "Alarm",
        "MCI": "Multi Casualty",
        "ME": "Medical",
        "MF": "Marine Fire",
        "MU": "Mutual Aid",
        "NO": "Notification",
        "OA": "Alarm",
        "OF": "Outside Fire",
        "OI": "Odor Investigation",
        "PA": "Police Assist",
        "PE": "Pipeline Emergency",
        "PF": "Pole Fire",
        "PS": "Public Service",
        "RES": "Rescue",
        "RF": "Residential Fire",
        "RL": "Residential Lockout",
        "RR": "Rope Rescue",
        "RTE": "Railroad/Train Emergency",
        "SD": "Smoke Detector",
        "SF": "Structure Fire",
        "SH": "Sheared Hydrant",
        "SI": "Smoke Investigation",
        "ST": "Strike Team/Task Force",
        "STDBY": "Standby",
        "TC": "Traffic collision",
        "TCE": "Expanded Traffic Collision",
        "TCS": "Traffic Collision Involving Structure",
        "TCT": "Traffic Collision Involving Train",
        "TD": "Tree Down",
        "TE": "Transformer explosion",
        "TEST": "Test",
        "TNR": "Trench Rescue",
        "TOW": "Tornado Warning",
        "TR": "Technical Rescue",
        "TRBL": "Trouble Alarm",
        "TRNG": "Training",
        "TSW": "Tsunami Warning",
        "UNK": "Unknown",
        "USAR": "Urban Search and Rescue",
        "VEG": "Vegetation Fire",
        "VF": "Vehicle Fire",
        "VL": "Vehicle Lockout",
        "VS": "Vessel Sinking",
        "WA": "Wires down",
        "WCF": "Working Commercial Fire",
        "WD": "Wires down",
        "WE": "Water Emergency",
        "WFA": "Waterflow Alarm",
        "WR": "Water Rescue",
        "WRF": "Working Residential Fire",
        "WSF": "Confirmed Structure Fire",
        "WVEG": "Confirmed Vegetation Fire",
}
TOKEN = "tombrady5rings"

req = request.Request("https://web.pulsepoint.org/DB/giba.php?agency_id=EMS1110")
response = request.urlopen(req)
data = json.loads(response.read())

ct = base64.b64decode(data.get("ct"))
iv = bytes.fromhex(data.get("iv"))
salt = bytearray.fromhex(data.get("s"))

# Calculate a key from the password
hasher = hashlib.md5()
key = b''
block = None
while len(key) < 32:
    if block:
        hasher.update(block)
    hasher.update(TOKEN.encode())
    hasher.update(salt)
    block = hasher.digest()

    hasher = hashlib.md5()
    key += block

# Create a cipher and decrypt the data
backend = default_backend()
cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
decryptor = cipher.decryptor()
out = decryptor.update(ct) + decryptor.finalize()

# Clean up output data
out = out[1:out.rindex(b'"')].decode()              # Strip off extra bytes and wrapper quotes
out = out.replace(r'\"', r'"')                      # Un-escape quotes

data = json.loads(out)
active_incidents = data.get("incidents", {}).get("active", {})

if active_incidents:
    for incident in active_incidents:
        latitude = float(incident.get('Latitude'))
        longitude = float(incident.get('Longitude'))

        if (latitude <= 79.97083333 and latitude >= 79.94583333 and longitude >= 40.42777778 and longitude <= 40.45000000):
            incident_type = INCIDENT_TYPES[incident.get("PulsePointIncidentCallType")]
            utc_time = timezone('UTC').localize(datetime.strptime(incident.get("CallReceivedDateTime"), DATE_FORMAT))
            local_time = utc_time.astimezone(timezone('US/Eastern'))

            location = ""
            if incident.get("CommonPlaceName"):
                location += incident.get("CommonPlaceName")
                location += " "
            location += incident.get("FullDisplayAddress")

            data = {
                'text': "%s @ %s" % (incident_type, location),
                'username': "911bot"
            }
            data = json.dumps(data)
            data = str(data)
            data = data.encode('utf-8')

            req = request.Request(os.environ['SLACK_WEBHOOK_URL'], data=data)
            resp = request.urlopen(req)
