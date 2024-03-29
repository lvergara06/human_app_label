from datetime import datetime, timedelta
import sys
import pytz
import pandas as pd
import time
from PyQt5.QtWidgets import QApplication, QProgressBar, QProgressDialog, QWidget, QVBoxLayout, QSizePolicy, QLabel, QDesktopWidget
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon, QPixmap
import sys 
import whois
import requests
from bs4 import BeautifulSoup
import sys
import json
from urllib.parse import urlparse
debugging = False

# nDPI Protocol --> Category mapping 
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
    return pd.Series([col0_values[0], col0_values[1], col0_values[2], \
                      col0_values[3], col0_values[4], col0_values[5], \
                          col0_values[6],col0_values[7],col0_values[8], \
                              col0_values[9], col0_values[10], row[1], row[2],\
                                  row[3], row[4]])

# This function updates the progress bar
def update_progress(progress_dialog, value):
    progress_dialog.setValue(value)
    QApplication.processEvents()
    
# This function does WHOIS query on host and uses IP in the case that 
# org
def whois_lookup(host, fallback_ip, fallback_whois):
    
    try:
        if fallback_ip:
            result = whois.whois(fallback_ip)
        else:
            result = whois.whois(host)
            
       
        organization = extract_organization(result, fallback_whois)
        # print(f"{host} Registrant Org.:{organization}")
        return organization
    except Exception as e:
        print(f"Error during WHOIS lookup for {host}: {e}")
        return None

def whois_scraper(domain):
    url = f"https://www.whois.com/whois/{domain}"

    response = requests.get(url)
    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # if soup and soup.find('Registrant Organization'):
        # print(soup)
        if soup and soup.find('pre', {'id': 'registrarData'}) or soup.find('pre', {'id':'registryData'}):
            registry_data = soup.find('pre', {'id': 'registryData'})
            registrar_data = soup.find('pre', {'id': 'registrarData'})
            
            if registry_data:
                raw_whois_data = soup.find('pre', {'id': 'registryData'}).text
            elif registrar_data:
                raw_whois_data = soup.find('pre', {'id': 'registrarData'}).text
            try:
                # Find the line containing "Registrant Organization" and extract the value
                registrant_organization_line = next(
                    line for line in raw_whois_data.split('\n') if 'Registrant Organization' in line
                )
                parts = registrant_organization_line.split(': ', 1)
                
                if len(parts) >= 2:
                    # Extract the value after the ":" in the line
                    
                    
                    registrant_organization = parts[1]
                    return registrant_organization
                else:
                    return None
            except StopIteration:
                return None
        else: 
            return None
    else:
        print(f"Failed to retrieve information. Status code: {response.status_code}")
        return None

    
# This function extracts value from 'org' key 
def extract_organization(result, fallback):
    if not fallback:
        organization = result.get('org', None)
    else:
        organization = result.get('tech_organization') or result.get('registrant_name') or result.get('registrar', None)
    return organization

# This function takes a host name or url and returns domain.tld 
def extract_domain_host(hostname, is_url):
    if url: 
        parsed_url = urlparse(hostname)
        if parsed_url.netloc:
            # Split the domain into parts
            domain_parts = parsed_url.netloc.split('.')
            if len(domain_parts) >= 2:
                return '.'.join(domain_parts[-2:]).strip()
        return None
    else:
        parts = hostname.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:]).strip()
        return None
    
def print_df(df):
    if debugging:
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(df)
    else:
        pass

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

## Global Variables
connectionsFile = ""
flowFile = ""
timestamp = ""
pid = ""

## Max difference between connection epoch and pcmacct epoch
## TODO: Make the timeWindow an option in Transport.py
timeWindow = 120000

if debugging:
    connectionsFile = '/opt/firefox/human_app_label/NativeApp/work/connections.14935.20240206065613.csv'
    flowFile = '/opt/firefox/human_app_label/pmacct/flows/flows.14945.csv'
else:
    getOptions()

flows_data = []  # List to store data for DataFrame

# Initialize QApplication
app = QApplication([])
widget = QWidget()
layout = QVBoxLayout()

# Initialize progress bar
progress_dialog = QProgressBar()
progress_dialog.setFixedHeight(20)
progress_dialog.setFixedWidth(500)
title_label = QLabel("Matching URLs")

matching_icon = QLabel()
icon_path = "/opt/firefox/human_app_label/NativeApp/matching.png"
pixmap = QPixmap(icon_path)
# pixmap = pixmap.scaledToWidth(25)
pixmap = pixmap.scaledToHeight(60)  
matching_icon.setPixmap(pixmap)


layout.addWidget(title_label, alignment=Qt.AlignCenter)
layout.addWidget(matching_icon, alignment=Qt.AlignCenter)
layout.addWidget(progress_dialog, alignment=Qt.AlignCenter)
widget.setLayout(layout)

# Get the screen geometry to position the progress bar in the center
screen_rect = QDesktopWidget().screenGeometry()
widget_width = 500
widget_height = 30
widget.setGeometry(
    screen_rect.width() // 2 - widget_width // 2,
    screen_rect.height() // 2 - widget_height // 2,
    widget_width,
    widget_height
)

widget.setWindowFlags(widget.windowFlags() | Qt.WindowStaysOnTopHint)

widget.show()

## Open files
## Save original stdout to print messages
# TODO: Implement using Dataframes, not file opener interface
original_stdout = sys.stdout
with open(connectionsFile, 'r') as source1,\
      open(flowFile, 'r') as source2:
    connections = source1.readlines()
    total_connections = len(connections)
    current_connection = 0
    for connection in connections:
        current_connection += 1
        progress_percentage = int((current_connection / total_connections) * 100)
        update_progress(progress_dialog, progress_percentage)
        splitConnection = connection.split(',')
        connectionDestinationIp = splitConnection[0]
        connectionDestinationPort = splitConnection[1]
        connectionUserSelection = splitConnection[4]
        connectionOriginURL = splitConnection[5]
        connectionEpoch = splitConnection[3]
        connectionHost = splitConnection[7]
        source2.seek(0)
        flows = source2.readlines()
      
        match_found = False
        
        for flow in flows:
            splitFlow = flow.split(',')
            flowClass = splitFlow[0]
            flowSourceIp = splitFlow[1]
            flowDestinationIp = splitFlow[2]
            flowSourcePort = splitFlow[3]
            flowDestinationPort = splitFlow[4]
            flowStartTime = splitFlow[6]
            flowCategory = data.get(flowClass, "Unknown")  
        
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
                
            if ( (connectionDestinationIp == flowDestinationIp and connectionDestinationPort == flowDestinationPort and abs(int(connectionEpoch) - flowEpoch) <= timeWindow) or (connectionDestinationIp == flowSourceIp and connectionDestinationPort == flowSourcePort and abs(int(connectionEpoch) - flowEpoch) <= timeWindow) ):
                flows_data.append([flow, connectionUserSelection, connectionHost, connectionOriginURL, flowCategory])
                match_found = True
                break  # Break from the inner loop when a match is found

        # Check the flag before moving to the next item in flows file
        if match_found:
            continue
    update_progress(progress_dialog, 100)

widget.close()

df = pd.DataFrame(flows_data)
df = df.apply(extract_values, axis=1)

# Give names to columns in pmacct format
df.columns = ['nDPI Label','SRC_IP','DST_IP','SRC_PORT','DST_PORT','PROTOCOL','TIMESTAMP_START','TIMESTAMP_END', 'TIMESTAMP_ARRIVAL', 'PACKETS','BYTES', 'Human Label', 'Host','Origin URL','Category']


if debugging:
    df = pd.read_csv('debugging.csv')
    df.to_csv('debugging.csv', index = False)
    
# list of all unique human labels present in the output
unique_labels = df['Human Label'].unique()



# empty dictionary to hold multiple dataframes that map to human labels
dfs = {}

# assigning each label its own dataframe in the dictionary
for label in unique_labels: 
    dfs[label] = df[df['Human Label'] == label]

# Dynamically create a dataframe for each label that is present in the output
# social_media_df
# information_browsing_df
# news_df
# video_streaming_df
# shopping_df
# externalhost_df
for label, df_split in dfs.items():
    try:
        exec(f"{label.replace(' ', '_').lower()}_df = df_split")
       
        print(f"Successfully saved DataFrame for {label} to {label.replace(' ', '_').lower()}_df.")
    except Exception as e:
        print(f"Failed to save DataFrame for {label} due to {e}.")
################## explicit Dataframe assignment ##############################
try:
    video_streaming_df = video_streaming_df
except Exception as e: 
    print(e)
    
try:
    shopping_df = shopping_df
except Exception as e: 
    print(e)

try: 
    information_browsing_df = information_browsing_df
except Exception as e:
    print(e)

try:
    externalhost_df = externalhost_df
except Exception as e: 
    print(e)
    
try:
    email_df = email_df
except Exception as e: 
    print(e)

try:
    news_df = news_df
except Exception as e: 
    print(e)
    
try: 
    sm_df = social_media_df
except Exception as e: 
    print(e)

################################ Formatting ###################################
try:  
    url = False
    video_streaming_df['Host'] = video_streaming_df['Host'].apply(extract_domain_host, is_url = url)
    video_streaming_df = video_streaming_df[video_streaming_df['Host'].notna()] 
    video_streaming_df['Organization'] = None 
    video_streaming_df['Organization_tolower_stripped'] = None
    gt_row_streaming = video_streaming_df.drop_duplicates(subset='Host')
    gt_row_streaming['Host'] = gt_row_streaming['Host'].apply(extract_domain_host, is_url = url)
    gt_row_streaming = gt_row_streaming[gt_row_streaming['Host'].notna()] 
    url = True
    gt_row_streaming['URL Parsed'] = gt_row_streaming['Origin URL'].apply(extract_domain_host, is_url = url)
    gt_row_streaming = gt_row_streaming[gt_row_streaming['URL Parsed'].notna()]
    org_gt_streaming = None
except Exception as e: 
    print(e)
    
try:   
    url = False     
    shopping_df['Host'] = shopping_df['Host'].apply(extract_domain_host, is_url = url)
    shopping_df = shopping_df[shopping_df['Host'].notna()]  
    shopping_df['Organization'] = None
    shopping_df['Organization_tolower_stripped'] = None
    gt_row_shopping = shopping_df.drop_duplicates(subset='Host')
    gt_row_shopping['Host'] = gt_row_shopping['Host'].apply(extract_domain_host, is_url = url)
    gt_row_shopping = gt_row_shopping[gt_row_shopping['Host'].notna()] 
    url = True
    gt_row_shopping['URL Parsed'] = gt_row_shopping['Origin URL'].apply(extract_domain_host, is_url = url)
    gt_row_shopping = gt_row_shopping[gt_row_shopping['URL Parsed'].notna()]
    org_gt_shopping = None      
except Exception as e: 
    print(e)

try:    
    url = False    
    email_df['Host'] = email_df['Host'].apply(extract_domain_host, is_url = url)
    email_df = email_df[email_df['Host'].notna()] 
    email_df['Organization'] = None
    email_df['Organization_tolower_stripped'] = None
    gt_row_email = email_df.drop_duplicates(subset='Host')
    gt_row_email['Host'] = gt_row_email['Host'].apply(extract_domain_host, is_url = url)
    gt_row_email = gt_row_email[gt_row_email['Host'].notna()]
    url = True
    gt_row_email['URL Parsed'] = gt_row_email['Origin URL'].apply(extract_domain_host,is_url = url)
    gt_row_email = gt_row_email[gt_row_email['URL Parsed'].notna()]
    org_gt_email = None
    
except Exception as e: 
    print(e)
    
try:
    url = False      
    information_browsing_df['Host'] = information_browsing_df['Host'].apply(extract_domain_host, is_url = url)
    information_browsing_df = information_browsing_df[information_browsing_df['Host'].notna()] 
    information_browsing_df['Organization'] = None
    information_browsing_df['Organization_tolower_stripped'] = None
    gt_row_browsing = information_browsing_df.drop_duplicates(subset='Host')
    gt_row_browsing['Host'] = gt_row_browsing['Host'].apply(extract_domain_host, is_url = url)
    gt_row_browsing = gt_row_browsing[gt_row_browsing['Host'].notna()] 
    url = True
    gt_row_browsing['URL Parsed'] = gt_row_browsing['Origin URL'].apply(extract_domain_host, is_url = url)
    gt_row_browsing = gt_row_browsing[gt_row_browsing['URL Parsed'].notna()]
    org_gt_browsing = None 
    
except Exception as e: 
    print(e)
    
try:   
    url = False     
    news_df['Host'] = news_df['Host'].apply(extract_domain_host, is_url = url)
    news_df = news_df[news_df['Host'].notna()] 
    news_df['Organization'] = None
    news_df['Organization_tolower_stripped'] = None
    gt_row_news = news_df.drop_duplicates(subset='Host')
    gt_row_news['Host'] = gt_row_news['Host'].apply(extract_domain_host, is_url = url)
    gt_row_news = gt_row_news[gt_row_news['Host'].notna()]
    url = True
    gt_row_news['URL Parsed'] = gt_row_news['Origin URL'].apply(extract_domain_host, is_url = url)
    gt_row_news = gt_row_news[gt_row_news['URL Parsed'].notna()]
    org_gt_news = None 
except Exception as e: 
    print(e)
    
try: 
    url = False       
    sm_df['Host'] = sm_df['Host'].apply(extract_domain_host, is_url = url)
    sm_df = sm_df[sm_df['Host'].notna()] 
    sm_df['Organization'] = None
    sm_df['Organization_tolower_stripped'] = None
    sm_df['URL Parsed'] = None
    gt_row_sm = sm_df.drop_duplicates(subset='Host')
    gt_row_sm['Host'] = gt_row_sm['Host'].apply(extract_domain_host, is_url = url)
    gt_row_sm = gt_row_sm[gt_row_sm['Host'].notna()]
    url = True
    gt_row_sm['URL Parsed'] = gt_row_sm['Origin URL'].apply(extract_domain_host, is_url = url)
    gt_row_sm = gt_row_sm[gt_row_sm['URL Parsed'].notna()]
    org_gt_sm = None 
except Exception as e: 
    print(e)
    
try:        
    url = False
    externalhost_df['Host'] = externalhost_df['Host'].apply(extract_domain_host, is_url = url)
    externalhost_df = externalhost_df[externalhost_df['Host'].notna()] 
    url = True
    externalhost_df['URL Parsed'] = externalhost_df['Origin URL'].apply(extract_domain_host, is_url = url)
    externalhost_df = externalhost_df[externalhost_df['URL Parsed'].notna()]
    externalhost_df['Organization'] = None
    externalhost_df['Organization_tolower_stripped'] = None
    
    ## TODO: Make sure program works with no external hosts
    unique_hosts = externalhost_df['Host'].unique()
    if debugging:
        print('Unique external hosts: ')
        print(unique_hosts)
except Exception as e: 
    print(e)

################################ WHOIS #######################################
try: 
    for host in gt_row_streaming['Host']:
        fallback_ip = None
        fallback_whois = False
        result = whois_lookup(host, fallback_ip, fallback_whois)

        if isinstance(result, list):
            org_gt_streaming = result[0]
        else:
            org_gt_streaming = result
        
        if org_gt_streaming is not None:
            print(f"Registrant org for {host}: {org_gt_streaming}")
        time.sleep(1)
        
        if org_gt_streaming is None or org_gt_streaming.strip() == '':
            
            print(f'Whois failed for host {host}! Using webscrape...')
            result = whois_scraper(host)
            
            if isinstance(result, list):
                org_gt_streaming = result[0]
            else:
                org_gt_streaming = result
            
            if org_gt_streaming is not None:
                print(f"Registrant org found for host {host} using webscrape: {org_gt_streaming}")
                
            time.sleep(1)
            
        if org_gt_streaming is None or org_gt_streaming.strip() == '':
            print(f'Whois failed for host {host}! Trying again...')
            fallback_whois = True
            result = whois_lookup(host, fallback_ip, fallback_whois)
           
            if isinstance(result, list):
                org_gt_streaming = result[0]
            else:
                org_gt_streaming = result
            if org_gt_streaming is not None:
                print(f"Registrant org for {host}: {org_gt_streaming}")
                
            time.sleep(1)
            
        if org_gt_streaming is None or org_gt_streaming.strip() == '':
            fallback_ip = gt_row_streaming.loc[gt_row_streaming['Host'] == host, 'DST_IP'].values[0]
            print(f"Whois failed! Using IP {fallback_ip}...")
            result = whois_lookup(host, fallback_ip, fallback_whois)
         
            if isinstance(result, list):
                org_gt_streaming = result[0]
            else:
                org_gt_streaming = result
                
            if org_gt_streaming is not None:
                print(f"Registrant org found for host {host} using IP: {fallback_ip}: {org_gt_streaming}")
            time.sleep(1)
    
        gt_row_streaming.loc[gt_row_streaming['Host'] == host, 'Organization'] = org_gt_streaming
        gt_row_streaming.loc[gt_row_streaming['Host'] == host, 'Organization_tolower_stripped'] = org_gt_streaming.split()[0].lower()
except Exception as e: 
    print(e)
    
try: 
    for host in gt_row_shopping['Host']:
        fallback_ip = None
        fallback_whois = False
        result = whois_lookup(host, fallback_ip, fallback_whois)

        if isinstance(result, list):
            org_gt_shopping = result[0]
            
        else:
            org_gt_shopping = result
        if org_gt_shopping is not None:
            print(f"Registrant org for {host}: {org_gt_shopping}")
        time.sleep(1)
        
        if org_gt_shopping is None or org_gt_shopping.strip() == '':
            
            print(f'Whois failed for host {host}! Using webscrape...')
            result = whois_scraper(host)
            
            if isinstance(result, list):
                org_gt_shopping = result[0]
                
            else:
                org_gt_shopping = result
                
            if org_gt_shopping is not None:
                print(f"Registrant org found for host {host} using webscrape: {org_gt_shopping}")
            time.sleep(1)
            
        if org_gt_shopping is None or org_gt_shopping.strip() == '':
            print(f'Whois failed for host {host}! Trying again...')
            fallback_whois = True
            result = whois_lookup(host, fallback_ip, fallback_whois)
            
            if isinstance(result, list):
                org_gt_shopping = result[0]
            else:
                org_gt_shopping = result
            if org_gt_shopping is not None:
                print(f"Registrant org for {host}: {org_gt_shopping}")
            time.sleep(1)
            
        if org_gt_shopping is None or org_gt_shopping.strip() == '': 
            fallback_ip = gt_row_shopping.loc[gt_row_shopping['Host'] == host, 'DST_IP'].values[0]
            print(f"Whois failed! Using IP {fallback_ip}...")
            result = whois_lookup(host, fallback_ip, fallback_whois)
         
            if isinstance(result, list):
                org_gt_shopping = result[0]
            else:
                org_gt_shopping = result
            if org_gt_shopping is not None:
                print(f"Registrant org found for host {host} using IP: {fallback_ip}: {org_gt_shopping}")
            time.sleep(1)
           
        gt_row_shopping.loc[gt_row_shopping['Host'] == host, 'Organization'] = org_gt_shopping
        gt_row_shopping.loc[gt_row_shopping['Host'] == host, 'Organization_tolower_stripped'] = org_gt_shopping.split()[0].lower()
        
except Exception as e: 
    print(e)

try: 
    for host in gt_row_email['Host']:
        fallback_ip = None
        fallback_whois = False
        result = whois_lookup(host, fallback_ip, fallback_whois)

        if isinstance(result, list):
            org_gt_email = result[0]
        else:
            org_gt_email = result
        if org_gt_email is not None:
            print(f"Registrant org for {host}: {org_gt_email}")
        time.sleep(1)
        
        if org_gt_email is None or org_gt_email.strip() == '':
            
            print(f'Whois failed for host {host}! Using webscrape...')
            result = whois_scraper(host)
            
            if isinstance(result, list):
                org_gt_email = result[0]
            else:
                org_gt_email = result
            if org_gt_email is not None:
                print(f"Registrant org found for host {host} using webscrape: {org_gt_email}")
            time.sleep(1)
            
        if org_gt_email is None or org_gt_email.strip() == '':
            print(f'Whois failed for host {host}! Using fallback methods...')
            fallback_whois = True
            result = whois_lookup(host, fallback_ip, fallback_whois)
            
            if isinstance(result, list):
                org_gt_email = result[0]
            else:
                org_gt_email = result
            if org_gt_email is not None:
                print(f"Registrant org for {host}: {org_gt_email}")
            time.sleep(1)
            
        if org_gt_email is None or org_gt_email.strip() == '':
            fallback_ip = gt_row_email.loc[gt_row_email['Host'] == host, 'DST_IP'].values[0]
            print(f"Whois failed for host {host}! Trying again...")
            result = whois_lookup(host, fallback_ip, fallback_whois)
         
            if isinstance(result, list):
                org_gt_email = result[0]
            else:
                org_gt_email = result
                
            if org_gt_email is not None:
                print(f"Registrant org found for host {host} using IP: {fallback_ip}: {org_gt_email}")
            time.sleep(1)
        
        gt_row_email.loc[gt_row_email['Host'] == host, 'Organization'] = org_gt_email
        gt_row_email.loc[gt_row_email['Host'] == host, 'Organization_tolower_stripped'] = org_gt_email.split()[0].lower()
except Exception as e: 
    print(f'{e}')
    
try: 
    for host in gt_row_browsing['Host']:
        fallback_ip = None
        fallback_whois = False
        result = whois_lookup(host, fallback_ip, fallback_whois)

        if isinstance(result, list):
            org_gt_browsing = result[0]
        else:
            org_gt_browsing = result
            
        if org_gt_browsing is not None:
            print(f"Registrant org for {host}: {org_gt_browsing}")
        
        time.sleep(1)
        
        if org_gt_browsing is None or org_gt_browsing.strip() == '':
            
            print(f'Whois failed for host {host}! Using webscrape...')
            result = whois_scraper(host)
            
            if isinstance(result, list):
                org_gt_browsing = result[0]
            else:
                org_gt_browsing = result
                
            if org_gt_browsing is not None:
                print(f"Registrant org found for host {host} using webscrape: {org_gt_browsing}")
            time.sleep(1)
            
        if org_gt_browsing is None or org_gt_browsing.strip() == '':
            print(f'Whois failed for {host}! Trying again...')
            fallback_whois = True
            result = whois_lookup(host, fallback_ip, fallback_whois)
            
            if isinstance(result, list):
                org_gt_browsing = result[0]
            else:
                org_gt_browsing = result
            if org_gt_browsing is not None:
                print(f"Registrant org for {host}: {org_gt_browsing}")
                
            time.sleep(1)
        if org_gt_browsing is None or org_gt_browsing.strip() == '':
            fallback_ip = gt_row_browsing.loc[gt_row_browsing['Host'] == host, 'DST_IP'].values[0]
            print(f"Whois failed! Using IP {fallback_ip}...")
            result = whois_lookup(host, fallback_ip, fallback_whois)
         
            if isinstance(result, list):
                org_gt_browsing = result[0]
            else:
                org_gt_browsing = result
            if org_gt_email is not None:
                print(f"Registrant org found for host {host} using IP: {fallback_ip}: {org_gt_browsing}")
            time.sleep(1)
            
        gt_row_browsing.loc[gt_row_browsing['Host'] == host, 'Organization'] = org_gt_browsing
        gt_row_browsing.loc[gt_row_browsing['Host'] == host, 'Organization_tolower_stripped'] = org_gt_browsing.split()[0].lower()
except Exception as e: 
    print(e)

try: 
    for host in gt_row_news['Host']:
        fallback_ip = None
        fallback_whois = False
        result = whois_lookup(host, fallback_ip, fallback_whois)

        if isinstance(result, list):
            org_gt_news = result[0]
        else:
            org_gt_news = result
        
        if org_gt_news is not None:
            print(f"Registrant org for {host}: {org_gt_news}")
        time.sleep(1)
        
        if org_gt_news is None or org_gt_news.strip() == '':
            
            print(f'Whois failed for host {host}! Using webscrape...')
            result = whois_scraper(host)
            
            if isinstance(result, list):
                org_gt_news = result[0]
            else:
                org_gt_news = result
                
            if org_gt_news is not None: 
                print(f"Registrant org found for host {host} using webscrape: {org_gt_news}")
            time.sleep(1)
            
        if org_gt_news is None or org_gt_news.strip() == '':
            print(f'Whois failed for host {host}! Trying again...')
            fallback_whois = True
            result = whois_lookup(host, fallback_ip, fallback_whois)    
            
            if isinstance(result, list):
                org_gt_news = result[0]
            else:
                org_gt_news = result
                
            if org_gt_news is not None:
                print(f"Registrant org for {host}: {org_gt_news}")
            time.sleep(1)
            
        if org_gt_news is None or org_gt_news.strip() == '':
            fallback_ip = org_gt_news.loc[org_gt_news['Host'] == host, 'DST_IP'].values[0]
            print(f"Whois failed! Using IP {fallback_ip}...")
            result = whois_lookup(host, fallback_ip, fallback_whois)
         
            if isinstance(result, list):
                org_gt_news = result[0]
            else:
                org_gt_news = result
                
            if org_gt_news is not None:
                print(f"Registrant org found for host {host} using IP: {fallback_ip}: {org_gt_news}")
            time.sleep(1)
        
        gt_row_news.loc[gt_row_news['Host'] == host, 'Organization'] = org_gt_news
        gt_row_news.loc[gt_row_news['Host'] == host, 'Organization_tolower_stripped'] = org_gt_news.split()[0].lower()

except Exception as e: 
    print(e)

try: 
    for host in gt_row_sm['Host']:
        fallback_ip = None
        fallback_whois = False
        result = whois_lookup(host, fallback_ip, fallback_whois)

        if isinstance(result, list):
            org_gt_sm = result[0]
        else:
            org_gt_sm = result
        
        if org_gt_sm is not None:
            print(f"Registrant org for {host}: {org_gt_sm}")
        time.sleep(1)
        
        if org_gt_sm is None or org_gt_sm.strip() == '':
            
            print(f'Whois failed for host {host}! Using webscrape...')
            result = whois_scraper(host)
            
            if isinstance(result, list):
                org_gt_sm = result[0]
            else:
                org_gt_sm = result
                
            if org_gt_sm is not None: 
                print(f"Registrant org found for host {host} using webscrape: {org_gt_sm}")
            time.sleep(1)
            
        if org_gt_sm is None or org_gt_sm.strip() == '':
            print(f'Whois failed for host {host}! Trying again...')
            fallback_whois = True
            result = whois_lookup(host, fallback_ip, fallback_whois)    
            
            if isinstance(result, list):
                org_gt_sm = result[0]
            else:
                org_gt_sm = result
                
            if org_gt_sm is not None:
                print(f"Registrant org for {host}: {org_gt_sm}")
            time.sleep(1)
            
        if org_gt_sm is None or org_gt_sm.strip() == '':
            fallback_ip = org_gt_sm.loc[org_gt_sm['Host'] == host, 'DST_IP'].values[0]
            print(f"Whois failed! Using IP {fallback_ip}...")
            result = whois_lookup(host, fallback_ip, fallback_whois)
         
            if isinstance(result, list):
                org_gt_sm = result[0]
            else:
                org_gt_sm = result
                
            if org_gt_sm is not None:
                print(f"Registrant org found for host {host} using IP: {fallback_ip}: {org_gt_news}")
            time.sleep(1)
        gt_row_sm.loc[gt_row_sm['Host'] == host, 'Organization'] = org_gt_sm
        gt_row_sm.loc[gt_row_sm['Host'] == host, 'Organization_tolower_stripped'] = org_gt_sm.split()[0].lower()
except Exception as e: 
    print(e)
    
################### ExternalHost WHOIS ############################

widget = QWidget()
layout = QVBoxLayout()

progress_dialog = QProgressBar()
progress_dialog.setFixedHeight(20) 
progress_dialog.setFixedWidth(500)  
title_label = QLabel("Making WHOIS Queries")

matching_icon = QLabel()
icon_path = "/opt/firefox/human_app_label/NativeApp/whois.png"
pixmap = QPixmap(icon_path)
# pixmap = pixmap.scaledToWidth(25)  
pixmap = pixmap.scaledToHeight(60)  
matching_icon.setPixmap(pixmap)


layout.addWidget(title_label, alignment=Qt.AlignCenter)
layout.addWidget(matching_icon, alignment=Qt.AlignCenter)
layout.addWidget(progress_dialog, alignment=Qt.AlignCenter)
widget.setLayout(layout)

screen_rect = QDesktopWidget().screenGeometry()
widget_width = 500
widget_height = 30
widget.setGeometry(
    screen_rect.width() // 2 - widget_width // 2,
    screen_rect.height() // 2 - widget_height // 2,
    widget_width,
    widget_height
)

widget.setWindowFlags(widget.windowFlags() | Qt.WindowStaysOnTopHint)

widget.show()
total_hosts = len(unique_hosts)
current_host = 0

for idx, host in enumerate(unique_hosts):
    
    current_host += 1
    progress_percentage = int((current_host / total_hosts) * 100)
    update_progress(progress_dialog, progress_percentage)
    
    fallback_ip = None
    fallback_whois = False
    result = whois_lookup(host, fallback_ip, fallback_whois)

    if isinstance(result, list):
        organization = result[0]
    else:
        organization = result
    if organization is not None:
        print(f"Registrant org for {host}: {organization}")
    time.sleep(1)
    
    if organization is None or organization.strip() == '':
        
        print(f'Whois failed for host {host}! Using webscrape...')
        result = whois_scraper(host)
        
        if isinstance(result, list):
            organization = result[0]
        else:
            organization = result
        if organization is not None:
            print(f"Registrant org found for host {host} using webscrape: {organization}")
        time.sleep(1)
    
    if organization is None or organization.strip() == '':
        print(f'Whois failed for host {host}! Trying again...')
        fallback_whois = True
        result = whois_lookup(host, fallback_ip, fallback_whois)
        
        if isinstance(result, list):
            organization = result[0]
        else:
            organization = result
        if organization is not None:
            print(f"Registrant org for {host}: {organization}")
        time.sleep(1)
        
    if organization is None or organization.strip() == '':
        fallback_ip = externalhost_df.loc[externalhost_df['Host'] == host, 'DST_IP'].values[0]
        print(f"Whois failed! Using IP {fallback_ip}...")
        result = whois_lookup(host, fallback_ip, fallback_whois)
     
        if isinstance(result, list):
            organization = result[0]
        else:
            organization = result
        if organization is not None:
            print(f"Registrant org found for host {host} using IP: {fallback_ip}: {organization}")
        time.sleep(1)
    
    
    externalhost_df.loc[externalhost_df['Host'] == host, 'Organization'] = organization
    if organization is not None:
        externalhost_df.loc[externalhost_df['Host'] == host, 'Organization_tolower_stripped'] =  organization.split()[0].lower()
        
update_progress(progress_dialog, 100)
widget.close()
    
################## Org Assignment (gt) ######################################
dfs_to_concat = []

try:
    for index, row in video_streaming_df.iterrows():
        if row['Host'] in gt_row_streaming['Host'].values:
            matching_organization = gt_row_streaming.loc[gt_row_streaming['Host'] == row['Host'], 'Organization'].values
            video_streaming_df.loc[index, 'Organization'] = matching_organization[0] if len(matching_organization) > 0 else 'Unknown'
        else:
            pass
    dfs_to_concat.append(video_streaming_df)
except Exception as e: 
    print(e)
    
try: 
    for index, row in email_df.iterrows():
        if row['Host'] in gt_row_email['Host'].values:
            matching_organization = gt_row_email.loc[gt_row_email['Host'] == row['Host'], 'Organization'].values
            email_df.loc[index, 'Organization'] = matching_organization[0] if len(matching_organization) > 0 else 'Unknown'
    
        else:
            pass
    dfs_to_concat.append(email_df)
   
except Exception as e: 
    print(e)
    
try: 
    for index, row in shopping_df.iterrows():
        if row['Host'] in gt_row_shopping['Host'].values:
            matching_organization = gt_row_shopping.loc[gt_row_shopping['Host'] == row['Host'], 'Organization'].values
            shopping_df.loc[index, 'Organization'] = matching_organization[0] if len(matching_organization) > 0 else 'Unknown'
        else:
            pass
    dfs_to_concat.append(shopping_df)
except Exception as e: 
    print(e)

try: 
    for index, row in sm_df.iterrows():
        if row['Host'] in gt_row_sm['Host'].values:
            matching_organization = gt_row_sm.loc[gt_row_sm['Host'] == row['Host'], 'Organization'].values
            sm_df.loc[index, 'Organization'] = matching_organization[0] if len(matching_organization) > 0 else 'Unknown'
        else:
            pass
    dfs_to_concat.append(sm_df)
except Exception as e: 
    print(e)

try: 
    for index, row in news_df.iterrows():
        if row['Host'] in gt_row_news['Host'].values:
            matching_organization = gt_row_news.loc[gt_row_news['Host'] == row['Host'], 'Organization'].values
            news_df.loc[index, 'Organization'] = matching_organization[0] if len(matching_organization) > 0 else 'Unknown'
        else:
            pass
    dfs_to_concat.append(news_df)
except Exception as e: 
    print(e)
    
try: 
    for index, row in information_browsing_df.iterrows():
        if row['Host'] in gt_row_browsing['Host'].values:
            matching_organization = gt_row_browsing.loc[gt_row_browsing['Host'] == row['Host'], 'Organization'].values
            information_browsing_df.loc[index, 'Organization'] = matching_organization[0] if len(matching_organization) > 0 else 'Unknown'
        else:
            pass
    dfs_to_concat.append(information_browsing_df)
except Exception as e: 
    print(e)
    
############## Label Assignment (External) ####################################
try: 
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_host = extract_domain_host(row['Origin URL'], url)
        streaming_origin = gt_row_streaming['URL Parsed'].values
        
        if (row['Organization_tolower_stripped'] in gt_row_streaming['Organization_tolower_stripped'].values) and (row['URL Parsed'] in streaming_origin):
            externalhost_df.loc[index, 'Human Label'] = 'Video streaming'
        else:
            pass
except Exception as e: 
    print(e)

try: 
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_host = extract_domain_host(row['Origin URL'], url)
        shopping_origin = gt_row_shopping['URL Parsed'].values

        if (row['Organization_tolower_stripped'] in gt_row_shopping['Organization_tolower_stripped'].values) and (row['URL Parsed'] in shopping_origin):
                externalhost_df.loc[index, 'Human Label'] = 'Shopping'
        else:
            pass
except Exception as e: 
    print(e)

try: 
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_host = extract_domain_host(row['Origin URL'], url)
        email_origin = gt_row_email['URL Parsed'].values

        if (row['Organization_tolower_stripped'] in gt_row_email['Organization_tolower_stripped'].values) and (row['URL Parsed'] in email_origin):
            externalhost_df.loc[index, 'Human Label'] = 'Email'
        else:
            pass
except Exception as e: 
    print(e)

try: 
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_host = extract_domain_host(row['Origin URL'], url)
        browsing_origin = gt_row_browsing['URL Parsed'].values

        if (row['Organization_tolower_stripped'] in gt_row_browsing['Organization_tolower_stripped'].values) and (row['URL Parsed'] in browsing_origin):
            externalhost_df.loc[index, 'Human Label'] = 'Information browsing'
        else:
            pass
except Exception as e: 
    print(e)


try: 
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_host = extract_domain_host(row['Origin URL'], url)
        news_origin = gt_row_news['URL Parsed'].values

        if (row['Organization_tolower_stripped'] in gt_row_news['Organization_tolower_stripped'].values) and (row['URL Parsed'] in news_origin):
            externalhost_df.loc[index, 'Human Label'] = 'News'
        else:
            pass
except Exception as e: 
    print(e)
    
try:
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_host = extract_domain_host(row['Origin URL'], url)
        sm_origin = gt_row_sm['URL Parsed'].values
        
        if (row['Organization_tolower_stripped'] in gt_row_sm['Organization_tolower_stripped'].values) and (row['URL Parsed'] in sm_origin):
            externalhost_df.loc[index, 'Human Label'] = 'Social media'
        else:
            pass
except Exception as e: 
    print(e)

########################## End game ##########################################

if dfs_to_concat: 
    result_df = pd.concat(dfs_to_concat, ignore_index = True)
    
result_df2 = pd.concat([result_df, externalhost_df], ignore_index = True)
columns_to_drop = ['Organization_tolower_stripped', 'URL Parsed']

result_df2 = result_df2.drop(columns=columns_to_drop)

# Save output
# if debugging:
#     result_df2.to_csv('/home/herman/human_app_label_testing/merged_conn.csv', index=False)

# else:
result_df2.to_csv(f'/opt/firefox/human_app_label/NativeApp/mergedOutput/merged_connections_{pid}_{timestamp}.csv', index=False)
