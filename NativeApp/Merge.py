from datetime import datetime, timedelta
import sys
import pytz
import pandas as pd
import time
from PyQt5.QtWidgets import QApplication, QProgressBar, QProgressDialog, QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QCoreApplication
import sys 
import whois

data = {
    "Unknown": "Unspecified",
    "FTP_CONTROL": "Download",
    "POP3": "Email",
    "SMTP": "Email",
    "IMAP": "Email",
    "DNS": "Network",
    "IPP": "System",
    "HTTP": "Web",
    "MDNS": "Network",
    "NTP": "System",
    "NetBIOS": "System",
    "NFS": "DataTransfer",
    "SSDP": "System",
    "BGP": "Network",
    "SNMP": "Network",
    "XDMCP": "RemoteAccess",
    "SMBv1": "System",
    "Syslog": "System",
    "DHCP": "Network",
    "PostgreSQL": "Database",
    "MySQL": "Database",
    "Outlook": "Email",
    "Free22": "Potentially Dangerous Download",
    "POPS": "Email",
    "Tailscale": "VPN",
    "Free25": "Potentially Dangerous Download",
    "ntop": "Network",
    "COAP": "RPC",
    "VMware": "RemoteAccess",
    "SMTPS": "Email",
    "DTLS": "Web",
    "UBNTAC2": "Network",
    "Kontiki": "Potentially Dangerous Media",
    "Free33": "Potentially Dangerous Download",
    "Free34": "Potentially Dangerous Download",
    "Gnutella": "Potentially Dangerous Download",
    "eDonkey": "Download",
    "BitTorrent": "Download",
    "Skype_TeamsCall": "VoIP",
    "Signal": "Chat",
    "Memcached": "Network",
    "SMBv23": "System",
    "Mining": "Mining",
    "NestLogSink": "Cloud",
    "Modbus": "IoT-Scada",
    "WhatsAppCall": "VoIP",
    "DataSaver": "Web",
    "Xbox": "Game",
    "QQ": "Chat",
    "TikTok": "Social media",
    "RTSP": "Media",
    "IMAPS": "Email",
    "IceCast": "Media",
    "CPHA": "Network",
    "PPStream": "Video streaming",
    "Zattoo": "Video streaming",
    "Free56": "Music",
    "Free57": "Video streaming",
    "Discord": "Collaborative",
    "TVUplayer": "Video streaming",
    "MongoDB": "Database",
    "Pluralsight": "Video streaming",
    "Free62": "Download",
    "OCSP": "Network",
    "VXLAN": "Network",
    "IRC": "Chat",
    "MerakiCloud": "Network",
    "Jabber": "Web",
    "Nats": "RPC",
    "AmongUs": "Game",
    "Yahoo": "Web",
    "DisneyPlus": "Video streaming",
    "GooglePlus": "Social media",
    "VRRP": "Network",
    "Steam": "Game",
    "HalfLife2": "Game",
    "WorldOfWarcraft": "Game",
    "Telnet": "RemoteAccess",
    "STUN": "Network",
    "IPSec": "VPN",
    "GRE": "Network",
    "ICMP": "Network",
    "IGMP": "Network",
    "EGP": "Network",
    "SCTP": "Network",
    "OSPF": "Network",
    "IP_in_IP": "Network",
    "RTP": "Media",
    "RDP": "RemoteAccess",
    "VNC": "RemoteAccess",
    "Tumblr": "Social media",
    "TLS": "Web",
    "SSH": "RemoteAccess",
    "Usenet": "Web",
    "MGCP": "VoIP",
    "IAX": "VoIP",
    "TFTP": "DataTransfer",
    "AFP": "DataTransfer",
    "Free98": "Potentially Dangerous Download",
    "Free99": "Download",
    "SIP": "VoIP",
    "TruPhone": "VoIP",
    "ICMPV6": "Network",
    "DHCPV6": "Network",
    "Armagetron": "Game",
    "Crossfire": "RPC",
    "Dofus": "Game",
    "Free107": "Game",
    "Free108": "Game",
    "Guildwars": "Game",
    "AmazonAlexa": "VirtAssistant",
    "Kerberos": "Network",
    "LDAP": "System",
    "MapleStory": "Game",
    "MsSQL-TDS": "Database",
    "PPTP": "VPN",
    "Warcraft3": "Game",
    "WorldOfKungFu": "Game",
    "Slack": "Collaborative",
    "Facebook": "Social media",
    "Twitter": "Social media",
    "Dropbox": "Cloud",
    "GMail": "Email",
    "GoogleMaps": "Web",
    "YouTube": "Video streaming",
    "Skype_Teams": "VoIP",
    "Google": "Web",
    "RPC": "RPC",
    "NetFlow": "Network",
    "sFlow": "Network",
    "HTTP_Connect": "Web",
    "HTTP_Proxy": "Web",
    "Citrix": "Network",
    "NetFlix": "Video streaming",
    "LastFM": "Music",
    "Waze": "Web",
    "YouTubeUpload": "Video streaming",
    "Hulu": "Video streaming",
    "CHECKMK": "DataTransfer",
    "AJP": "Web",
    "Apple": "Safe",
    "Webex": "VoIP",
    "WhatsApp": "Chat",
    "AppleiCloud": "Web",
    "Viber": "VoIP",
    "AppleiTunes": "Video streaming",
    "Radius": "Network",
    "WindowsUpdate": "SoftwareUpdate",
    "TeamViewer": "RemoteAccess",
    "Tuenti": "VoIP",
    "LotusNotes": "Collaborative",
    "SAP": "Network",
    "GTP": "Network",
    "WSD": "Network",
    "LLMNR": "Network",
    "TocaBoca": "Game",
    "Spotify": "Music",
    "Messenger": "Chat",
    "H323": "VoIP",
    "OpenVPN": "VPN",
    "NOE": "VoIP",
    "CiscoVPN": "VPN",
    "TeamSpeak": "VoIP",
    "Tor": "Potentially Dangerous VPN",
    "CiscoSkinny": "VoIP",
    "RTCP": "VoIP",
    "RSYNC": "DataTransfer",
    "Oracle": "Database",
    "Corba": "RPC",
    "UbuntuONE": "Cloud",
    "Whois-DAS": "Network",
    "SD-RTN": "Media",
    "SOCKS": "Web",
    "Nintendo": "Game",
    "RTMP": "Media",
    "FTP_DATA": "Download",
    "Wikipedia": "Web",
    "ZeroMQ": "RPC",
    "Amazon": "Web",
    "eBay": "Shopping",
    "CNN": "News",
    "Megaco": "VoIP",
    "Redis": "Database",
    "Pinterest": "Social media",
    "VHUA": "VoIP",
    "Telegram": "Chat",
    "Vevo": "Music",
    "Pandora": "Video streaming",
    "QUIC": "Web",
    "Zoom": "Video streaming",
    "EAQ": "Network",
    "Ookla": "Network",
    "AMQP": "RPC",
    "KakaoTalk": "Chat",
    "KakaoTalk_Voice": "VoIP",
    "Twitch": "Video streaming",
    "DoH_DoT": "Network",
    "WeChat": "Chat",
    "MPEG_TS": "Media",
    "Snapchat": "Social media",
    "Sina(Weibo)": "Social media",
    "GoogleHangoutDuo": "VoIP",
    "IFLIX": "Video streaming",
    "Github": "Collaborative",
    "BJNP": "System",
    "Reddit": "Social media",
    "WireGuard": "VPN",
    "SMPP": "Download",
    "DNScrypt": "Network",
    "TINC": "VPN",
    "Deezer": "Music",
    "Instagram": "Social media",
    "Microsoft": "Cloud",
    "Starcraft": "Game",
    "Teredo": "Network",
    "HotspotShield": "VPN",
    "IMO": "VoIP",
    "GoogleDrive": "Cloud",
    "OCS": "Media",
    "Microsoft365": "Collaborative",
    "Cloudflare": "Web",
    "MS_OneDrive": "Cloud",
    "MQTT": "RPC",
    "RX": "RPC",
    "AppleStore": "SoftwareUpdate",
    "OpenDNS": "Web",
    "Git": "Collaborative",
    "DRDA": "Database",
    "PlayStore": "SoftwareUpdate",
    "SOMEIP": "RPC",
    "FIX": "RPC",
    "Playstation": "Game",
    "Pastebin": "Download",
    "LinkedIn": "Social media",
    "SoundCloud": "Music",
    "CSGO": "Game",
    "LISP": "Cloud",
    "Diameter": "Network",
    "ApplePush": "Cloud",
    "GoogleServices": "Web",
    "AmazonVideo": "Cloud",
    "GoogleDocs": "Collaborative",
    "WhatsAppFiles": "Download",
    "TargusDataspeed": "Network",
    "DNP3": "IoT-Scada",
    "IEC60870": "IoT-Scada",
    "Bloomberg": "Network",
    "CAPWAP": "Network",
    "Zabbix": "Network",
    "s7comm": "Network",
    "Teams": "Collaborative",
    "WebSocket": "Web",
    "AnyDesk": "RemoteAccess",
    "SOAP": "RPC",
    "AppleSiri": "VirtAssistant",
    "SnapchatCall": "VoIP",
    "HP_VIRTGRP": "Network",
    "GenshinImpact": "Game",
    "Activision": "Game",
    "FortiClient": "VPN",
    "Z3950": "Network",
    "Likee": "Social media",
    "GitLab": "Collaborative",
    "AVASTSecureDNS": "Network",
    "Cassandra": "Database",
    "AmazonAWS": "Cloud",
    "Salesforce": "Cloud",
    "Vimeo": "Video streaming",
    "FacebookVoip": "VoIP",
    "SignalVoip": "VoIP",
    "Fuze": "VoIP",
    "GTP_U": "Network",
    "GTP_C": "Network",
    "GTP_PRIME": "Network",
    "Alibaba": "Web",
    "Crashlytics": "DataTransfer",
    "Azure": "Cloud",
    "iCloudPrivateRelay": "VPN",
    "EthernetIP": "Network",
    "Badoo": "Social media",
    "AccuWeather": "Web",
    "GoogleClassroom": "Collaborative",
    "HSRP": "Network",
    "Cybersec": "Cybersecurity",
    "GoogleCloud": "Cloud",
    "Tencent": "Social media",
    "RakNet": "Game",
    "Xiaomi": "Web",
    "Edgecast": "Cloud",
    "Cachefly": "Cloud",
    "Softether": "VPN",
    "MpegDash": "Media",
    "Dazn": "Video streaming",
    "GoTo": "VoIP",
    "RSH": "RemoteAccess",
    "1kxun": "Video streaming",
    "PGM": "Network",
    "IP_PIM": "Network",
    "collectd": "System",
    "TunnelBear": "VPN",
    "CloudflareWarp": "VPN",
    "i3D": "Game",
    "RiotGames": "Game",
    "Psiphon": "VPN",
    "UltraSurf": "VPN",
    "Threema": "Chat",
    "AliCloud": "Cloud",
    "AVAST": "Network",
    "TiVoConnect": "Network",
    "Kismet": "Network",
    "FastCGI": "Network",
    "FTPS": "Download",
    "NAT-PMP": "Network",
    "Syncthing": "Download",
    "CryNetwork": "Game",
    "Line": "Chat",
    "LineCall": "VoIP",
    "AppleTVPlus": "Video streaming",
    "DirecTV": "Video streaming",
    "HBO": "Video streaming",
    "Vudu": "Video streaming",
    "Showtime": "Video streaming",
    "Dailymotion": "Video streaming",
    "Livestream": "Video streaming",
    "TencentVideo": "Video streaming",
    "IHeartRadio": "Music",
    "Tidal": "Music",
    "TuneIn": "Music",
    "SiriusXMRadio": "Music",
    "Munin": "System",
    "Elasticsearch": "System",
    "TuyaLP": "IoT-Scada",
    "TPLINK_SHP": "IoT-Scada"
}

# Helper function to 'clean' up the data and extract all relevant data
# from Dataframe
def extract_values(row):
    col0_values = row[0].split(',')
    return pd.Series([col0_values[0], col0_values[1], col0_values[2], col0_values[3], col0_values[4],
                      col0_values[5],col0_values[6],col0_values[7],col0_values[8],col0_values[9], col0_values[10], row[1], row[2], row[3]])

# This function updates the progress bar
def update_progress(progress_dialog, value):
    progress_dialog.setValue(value)
    QApplication.processEvents()

# This function extracts value from 'org' key 
# If 'org' is NONE, revert to 'registrant_name' or 'registrar' as fallbacks
def extract_organization(result):
    organization = result.get('org') or result.get('tech_organization') or result.get('registrant_name') or result.get('registrar', None)
    return organization

# This function takes a host name in the format subdomain.domain.tld
# and returns domain.tld 
def extract_domain_host(hostname):
    parts = hostname.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:]).strip()
    return None

# This function does WHOIS query on host and uses IP in the case that 
# org
def whois_lookup(host, fallback_ip):
    try:
        if fallback_ip:
            result = whois.whois(fallback_ip)
        else:
            result = whois.whois(host)

        organization = extract_organization(result)
        # print(f"{host} Registrant Org.:{organization}")
        return organization
    except Exception as e:
        print(f"Error during WHOIS lookup for {host}: {e}")
        return None

## Global Variables
connectionsFile = ""
flowFile = ""
timestamp = ""
pid = ""

## Max difference between connection epoch and pcmacct epoch
## TODO: Make the timeWindow an option in Transport.py
timeWindow = 120000

## Get args
def getOptions():
    if len(sys.argv) != 5:
        # All defaults
        print("Usage : Merge.py connections.csv flows.csv timestamp PID")
        exit(1)
    global connectionsFile
    connectionsFile = sys.argv[1]
    global flowFile
    flowFile = sys.argv[2]
    global timestamp 
    timestamp = sys.argv[3]
    global pid 
    pid = sys.argv[4]
    print("connectionsFile is : " + connectionsFile)
    print("flowFile is : " + flowFile)
    print("timestamp is: " + timestamp)
    print("PID is: " + pid)
    return

## Start
getOptions()

flows_data = []  # List to store data for DataFrame


## Open files
## Save original stdout to print messages
original_stdout = sys.stdout
with open(connectionsFile, 'r') as source1,\
     open(flowFile, 'r') as source2:
    flows = source2.readlines()
    for flow in flows:
        splitFlow = flow.split(',')
        flowClass = splitFlow[0]
        flowSourceIp = splitFlow[1]
        flowDestinationIp = splitFlow[2]
        flowSourcePort = splitFlow[3]
        flowDestinationPort = splitFlow[4]
        flowStartTime = splitFlow[6]
        flowCategory = data.get(flowClass, "Unknown")  
        # Skip the header fields
        if flowStartTime == "TIMESTAMP_START":
            continue
        # This is an adjustment to get mountain to UTC timestamp from pmacct
        # If your pmacct timestamps are in UTC then you will have to remove this.
        try:
            # Convert the local time string to a datetime object
            local_time = datetime.strptime(flowStartTime, "%Y-%m-%d %H:%M:%S.%f")

            # Get the local timezone
            # TODO: MAKE THIS NOT NEEDED
            local_tz = pytz.timezone('America/Denver')

            # Localize the datetime object to the local timezone
            localized_time = local_tz.localize(local_time, is_dst=None)

            # Convert the localized datetime to UTC
            utc_time = localized_time.astimezone(pytz.utc)

            # Calculate the flowEpoch timestamp
            flowEpoch = int((utc_time - datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds() * 1000)
        except Exception as e:
            print(f"Error: {e}")

        # print("flow:" + flowSourceIp + " " + flowDestinationIp + " " + flowSourcePort + " " + flowDestinationPort + " "  + str(flowEpoch) )
        source1.seek(0)
        connections = source1.readlines()

        # Flag to indicate if a match is found
        match_found = False

        for connection in connections:
            splitConnection = connection.split(',')
            connectionDestinationIp = splitConnection[0]
            connectionDestinationPort = splitConnection[1]
            connectionUserSelection = splitConnection[4]
            connectionEpoch = splitConnection[3]
            connectionHost = splitConnection[7]
            diff = abs(int(connectionEpoch) - flowEpoch)
            # print("connection:" + connectionSourceIp + " " +  connectionDestinationIp + " " + connectionSourcePort + " " + connectionDestinationPort + " " + connectionEpoch)
            if (
                flowDestinationIp == connectionDestinationIp
                and flowDestinationPort == connectionDestinationPort
                and abs(int(connectionEpoch) - flowEpoch) < timeWindow
            ):
                # print(flow + "," + connectionUserSelection + "," + connectionHost + "," +  flowCategory)
                flows_data.append([flow, connectionUserSelection, connectionHost, flowCategory])
                match_found = True
                break  # Break from the inner loop when a match is found

        # Check the flag before moving to the next item in source2
        if match_found:
            continue
# Convert list of lists to DataFrame
df = pd.DataFrame(flows_data)

df = df.apply(extract_values, axis=1)

# Give names to columns in pmacct format
df.columns = ['nDPI Label','SRC_IP','DST_IP','SRC_PORT','DST_PORT','PROTOCOL','TIMESTAMP_START','TIMESTAMP_END', 'TIMESTAMP_ARRIVAL', 'PACKETS','BYTES', 'Human Label', 'Host','Category']
print("Original dataframe: ")
print(df)

# Extract human label 
mainSel = None
for label in df['Human Label']:
    if label != 'ExternalHost':
        mainSel = label
        break
print("User sel: ")
print(mainSel)
# Create a subset dataframe consisting of only ExternalHost
# entries to analyze whether or not they are actually External
# or intended  
result_df = df[df['Human Label'] == 'ExternalHost'].copy()
# Create a subset dataframe consisting of only entries mapping 
# to human label (ground truth)
gt_df = df[df['Human Label'] == mainSel].copy()

# Apply extract_domain_host and filter out entries where it returns None
result_df['Host'] = result_df['Host'].apply(extract_domain_host)
result_df = result_df[result_df['Host'].notna()]  # Exclude entries with 'None'

# Create a new column to hold Organization data
result_df['Organization'] = None
print("result_df: ")
print(result_df)

gt_df['Organization'] = None

# We only need one row of gt_df as baseline
gt_row = gt_df.head(1).copy()
gt_row['Host'] = gt_row['Host'].apply(extract_domain_host)
gt_row = gt_row[gt_row['Host'].notna()]  # Exclude entries with 'None'
print("gt_row: ")
print(gt_row)
# Make sure to only do WHOIS on every host one time 
# WHOIS on all unique hosts
unique_hosts = result_df['Host'].unique()
print("Unique hosts:")
print(unique_hosts)

# Setup Progress Bar
app = QApplication([])
main_widget = QWidget()
layout = QVBoxLayout(main_widget)

progress = QProgressBar()
progress.setGeometry(450, 450, 500, 25)
progress.setMinimum(0)
progress.setMaximum(len(unique_hosts))
progress.setWindowFlag(Qt.WindowStaysOnTopHint)
progress.setValue(0)
progress.setWindowTitle("Performing WHOIS Queries")
progress.show()

# WHOIS on all unique hosts
for idx, host in enumerate(unique_hosts):
    fallback_ip = None
    
    organization = whois_lookup(host, fallback_ip)
    # print(f"Registrant org for {host}: {organization}")
    time.sleep(1)
    if organization is None:
        fallback_ip = result_df.loc[result_df['Host'] == host, 'DST_IP'].values[0]
        print(f"Whois failed! Using IP {fallback_ip}...")
        organization = whois_lookup(host, fallback_ip)
        print(f"Registrant org found for host {host} using IP: {fallback_ip}: {organization}")
        time.sleep(1)
    result_df.loc[result_df['Host'] == host, 'Organization'] = organization
    
    # Update the progress bar
    update_progress(progress, idx + 1)
progress.close()

organization_gt = None
# WHOIS on baseline host  
for host in gt_row['Host']:
    organization_gt = extract_organization(whois.whois(host))
    # print(f"Organization for GT host {host}:"+ organization)
    gt_row.loc[gt_row['Host'] == host, 'Organization'] = organization_gt
print("gt_row (with org): ")
print(gt_row)
# Extract organization from ground truth row
mainOrg = gt_row['Organization'].values[0]

# Compare every org to baseline to determine if orgs are the same
# if they are the same, we can assume the host is intended and append the 
# users ground truth label to the host's row in output
# if not, remain as external host
for index, row in result_df.iterrows():
    if row['Organization'] == mainOrg:
        result_df.loc[index, 'Human Label'] = mainSel
        
    else:
        pass

print("result_df after comparison to mainOrg: ")
print(result_df)    

for index, row in gt_df.iterrows():
    if row['Human Label'] == mainSel:
        gt_df.loc[index, 'Organization'] = mainOrg
    else:
        pass

print("gt_df after appending mainOrg: ")
print(gt_df)

# Combine updated dataframe with ground truth dataframe 
result_df = pd.concat([result_df, gt_df], ignore_index=True)


# Save output
result_df.to_csv(f'/opt/firefox/human_app_label/TrainData/{mainSel}/merged_connections_{pid}.{timestamp}.csv', index=False)

QCoreApplication.quit()