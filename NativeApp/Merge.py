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
import whois
import sys
import json
from urllib.parse import urlparse
from ProgressBar import ProgressBar 
debugging = False

    
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
    
    if is_url: 
        parsed_url = urlparse(hostname)
        
        if parsed_url.netloc:
            # Split the domain into parts
            domain_parts = parsed_url.netloc.split('.')
            
            if len(domain_parts) >= 2:
                if 'ext-' in domain_parts[-2]:
                    domain_parts[-2] = domain_parts[-2].replace('ext-','')
                   
                return '.'.join(domain_parts[-2:]).strip()
        else:
            print(f'parsed_url.netloc is returning None for {hostname}!')
            return None
    else:
        parts = hostname.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:]).strip()
        else:
            return None
        
def check_duplicate(new_flows, prev_flows):
    if new_flows in prev_flows:
        return True
    else:
        return False
    
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
timeWindow = 30000

categories_file = '/opt/firefox/human_app_label/NativeApp/data.json'

if debugging:
    connectionsFile = '/opt/firefox/human_app_label/NativeApp/work/connections.23952.20240410035036.csv'
    flowFile = '/opt/firefox/human_app_label/pmacct/flows/flows.23962.csv'
else:
    getOptions()

merged_flows = []
prev_flows = []


url_df = pd.read_csv(connectionsFile)
flows_df = pd.read_csv(flowFile)


data = {} # Dict to store nDPI label --> category mappings

with open(categories_file, 'r') as file:
    data = json.load(file)

progress_bar = ProgressBar()
progress_bar.show('url')

total_connections= url_df.shape[0]
current_connection = 0
dup_flow = None

for url_index, url_row in url_df.iterrows(): 
    current_connection += 1
    progress_percentage = int((current_connection / total_connections) * 100)
    progress_bar.update_progress(progress_percentage)
    server_IP = url_row['serverIP']
    server_port = url_row['serverPort']
    user_sel = url_row['Human Label']
    origin_url = url_row['originURL']
    connection_epoch = url_row['Timestamp (Unix epoch)']
    remote_host = url_row['URL']
    

    for flow_index, flow_row in flows_df.iterrows():
        flow_class = flow_row['CLASS']
        flow_src_ip = flow_row['SRC_IP']
        flow_dst_ip = flow_row['DST_IP']
        flow_src_port = flow_row['SRC_PORT']
        flow_dst_port = flow_row['DST_PORT']
        flow_start_time = flow_row['TIMESTAMP_START']
        flow_category = data.get(flow_class, "Unknown")  
        
        if flow_start_time == "TIMESTAMP_START":
            continue
        # This is an adjustment to get mountain to UTC timestamp from pmacct
        # If your pmacct timestamps are in UTC then you will have to remove this.
        try:
            # Convert the local time string to a datetime object
            local_time = datetime.strptime(flow_start_time, "%Y-%m-%d %H:%M:%S.%f")

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
            
            
        
        if ( (server_IP == flow_dst_ip and \
              server_port == flow_dst_port and\
                  abs(int(connection_epoch) - flowEpoch) <= timeWindow) or\
            (server_IP == flow_src_ip and \
              server_port == flow_src_port and \
                  abs(int(connection_epoch) - flowEpoch) <= timeWindow) ):
            dup_flow = check_duplicate(list(flow_row.values), prev_flows)
            if dup_flow:
                continue # ignore this entry in the flows file, evaluate next flow
            else:
                merged_flows.append(list(flow_row.values) + [user_sel,remote_host,origin_url,flow_category] )
                prev_flows.append(list(flow_row.values))
                break  # Break from the inner looop
    
progress_bar.update_progress(100)

progress_bar.close()

df = pd.DataFrame(merged_flows)

df.columns = ['nDPI Label','SRC_IP','DST_IP','SRC_PORT','DST_PORT','PROTOCOL',\
                        'TIMESTAMP_START','TIMESTAMP_END', 'TIMESTAMP_ARRIVAL', \
                            'PACKETS','BYTES', 'Human Label', 'Host','Origin URL',\
                                'Category']

if debugging: 
    df.to_csv('/home/herman/human_app_label_testing/output/debugging.csv', index = False)
    # df = pd.read_csv('/home/herman/human_app_label_testing/output/debugging.csv')



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
    url = True
    video_streaming_df['Host'] = video_streaming_df['Host'].apply(extract_domain_host, is_url = url)
    video_streaming_df = video_streaming_df[video_streaming_df['Host'].notna()] 
    video_streaming_df['Organization'] = None 
    video_streaming_df['Organization_tolower_stripped'] = None
    gt_row_streaming = video_streaming_df.drop_duplicates(subset='Host')
    gt_row_streaming = gt_row_streaming[gt_row_streaming['Host'].notna()] 
    gt_row_streaming['URL Parsed'] = gt_row_streaming['Origin URL'].apply(extract_domain_host, is_url = url)
    gt_row_streaming = gt_row_streaming[gt_row_streaming['URL Parsed'].notna()]
    org_gt_streaming = None
except Exception as e: 
    print(e)
    
try:   
    url = True     
    shopping_df['Host'] = shopping_df['Host'].apply(extract_domain_host, is_url = url)
    shopping_df = shopping_df[shopping_df['Host'].notna()]  
    shopping_df['Organization'] = None
    shopping_df['Organization_tolower_stripped'] = None
    gt_row_shopping = shopping_df.drop_duplicates(subset='Host')
    gt_row_shopping = gt_row_shopping[gt_row_shopping['Host'].notna()] 
    gt_row_shopping['URL Parsed'] = gt_row_shopping['Origin URL'].apply(extract_domain_host, is_url = url)
    gt_row_shopping = gt_row_shopping[gt_row_shopping['URL Parsed'].notna()]
    org_gt_shopping = None 
   
         
except Exception as e: 
    print(e)

try:    
    url = True    
    email_df['Host'] = email_df['Host'].apply(extract_domain_host, is_url = url)
    email_df = email_df[email_df['Host'].notna()] 
    email_df['Organization'] = None
    email_df['Organization_tolower_stripped'] = None
    gt_row_email = email_df.drop_duplicates(subset='Host')
    gt_row_email = gt_row_email[gt_row_email['Host'].notna()]
    gt_row_email['URL Parsed'] = gt_row_email['Origin URL'].apply(extract_domain_host,is_url = url)
    gt_row_email = gt_row_email[gt_row_email['URL Parsed'].notna()]
    org_gt_email = None
    
except Exception as e: 
    print(e)
    
try:
    url = True      
    information_browsing_df['Host'] = information_browsing_df['Host'].apply(extract_domain_host, is_url = url)
    information_browsing_df = information_browsing_df[information_browsing_df['Host'].notna()] 
    information_browsing_df['Organization'] = None
    information_browsing_df['Organization_tolower_stripped'] = None
    gt_row_browsing = information_browsing_df.drop_duplicates(subset='Host')
    gt_row_browsing = gt_row_browsing[gt_row_browsing['Host'].notna()] 
    gt_row_browsing['URL Parsed'] = gt_row_browsing['Origin URL'].apply(extract_domain_host, is_url = url)
    gt_row_browsing = gt_row_browsing[gt_row_browsing['URL Parsed'].notna()]
    org_gt_browsing = None 
    
except Exception as e: 
    print(e)
    
try:   
    url = True     
    news_df['Host'] = news_df['Host'].apply(extract_domain_host, is_url = url)
    news_df = news_df[news_df['Host'].notna()] 
    news_df['Organization'] = None
    news_df['Organization_tolower_stripped'] = None
    gt_row_news = news_df.drop_duplicates(subset='Host')
    gt_row_news = gt_row_news[gt_row_news['Host'].notna()]
    gt_row_news['URL Parsed'] = gt_row_news['Origin URL'].apply(extract_domain_host, is_url = url)
    gt_row_news = gt_row_news[gt_row_news['URL Parsed'].notna()]
    org_gt_news = None 
except Exception as e: 
    print(e)
    
try: 
    url = True    
    sm_df['Host'] = sm_df['Host'].apply(extract_domain_host, is_url = url)
    sm_df = sm_df[sm_df['Host'].notna()] 
    sm_df['Organization'] = None
    sm_df['Organization_tolower_stripped'] = None
    sm_df['URL Parsed'] = None
    gt_row_sm = sm_df.drop_duplicates(subset='Host')
    gt_row_sm = gt_row_sm[gt_row_sm['Host'].notna()]
    gt_row_sm['URL Parsed'] = gt_row_sm['Origin URL'].apply(extract_domain_host, is_url = url)
    gt_row_sm = gt_row_sm[gt_row_sm['URL Parsed'].notna()]
    org_gt_sm = None 
except Exception as e: 
    print(e)
    
try:        
    url = True
    externalhost_df['Host'] = externalhost_df['Host'].apply(extract_domain_host, is_url = url)
    externalhost_df = externalhost_df[externalhost_df['Host'].notna()] 
    externalhost_df['URL Parsed'] = externalhost_df['Origin URL'].apply(extract_domain_host, is_url = url)
    externalhost_df = externalhost_df[externalhost_df['URL Parsed'].notna()]
    externalhost_df['Organization'] = None
    externalhost_df['Organization_tolower_stripped'] = None
    
    ## TODO: Make sure program works with no external hosts
    unique_hosts = externalhost_df['Host'].unique()
    
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
                if org_gt_shopping == '':
                    print('in if!!!')
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
        
        if org_gt_news is not None :
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
# progress_bar = ProgressBar('whois')
progress_bar.update_progress(0)
progress_bar.show('whois')

total_hosts = len(unique_hosts)
current_host = 0

for idx, host in enumerate(unique_hosts):
    
    current_host += 1
    progress_percentage = int((current_host / total_hosts) * 100)
    progress_bar.update_progress(progress_percentage)
    
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
        
    if organization is None or organization.strip == '':
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
        
        
progress_bar.update_progress(100)
progress_bar.close()
    
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
        current_external_origin = row['URL Parsed']
        current_external_org = row['Organization_tolower_stripped']
        
        
        current_gt_origin = None
        current_gt_org = None
    
        for gt_index, gt_row in gt_row_streaming.iterrows():
            if current_external_org == gt_row['Organization_tolower_stripped']\
                and current_external_origin == gt_row['URL Parsed']:
                current_gt_origin = gt_row['URL Parsed']
                current_gt_org = gt_row['Organization_tolower_stripped']
                break
        if current_gt_origin and current_gt_org: 
           if (current_external_org == current_gt_org) and \
               (current_external_origin == current_gt_origin):
               externalhost_df.loc[index, 'Human Label'] = 'Video streaming'
           else:
               pass
       
except Exception as e: 
    print(e)

try: 
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_origin = row['URL Parsed']
        current_external_org = row['Organization_tolower_stripped']
        
        
        current_gt_origin = None
        current_gt_org = None
        for gt_index, gt_row in gt_row_shopping.iterrows():
            if current_external_org == gt_row['Organization_tolower_stripped']\
                and current_external_origin == gt_row['URL Parsed']:
                current_gt_origin = gt_row['URL Parsed']
                current_gt_org = gt_row['Organization_tolower_stripped']
                break
        if current_gt_origin and current_gt_org: 
            if (current_external_org == current_gt_org) and \
                (current_external_origin == current_gt_origin):
                    externalhost_df.loc[index, 'Human Label'] = 'Shopping'
            else:
                pass
except Exception as e: 
    print(e)

try: 
   
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_origin = row['URL Parsed']
        current_external_org = row['Organization_tolower_stripped']
        
        
        current_gt_origin = None
        current_gt_org = None
        
        for gt_index, gt_row in gt_row_email.iterrows():
            if current_external_org == gt_row['Organization_tolower_stripped']\
                and current_external_origin == gt_row['URL Parsed']:
                current_gt_origin = gt_row['URL Parsed']
                current_gt_org = gt_row['Organization_tolower_stripped']
                break
        if current_gt_origin and current_gt_org: 
            if (current_external_org == current_gt_org) and \
                (current_external_origin == current_gt_origin):
                externalhost_df.loc[index, 'Human Label'] = 'Email'
   
            else:
                pass
except Exception as e: 
    print(e)

try: 
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_origin = row['URL Parsed']
        current_external_org = row['Organization_tolower_stripped']
        
        
        current_gt_origin = None
        current_gt_org = None

        for gt_index, gt_row in gt_row_browsing.iterrows():
            if current_external_org == gt_row['Organization_tolower_stripped']\
                and current_external_origin == gt_row['URL Parsed']:
                current_gt_origin = gt_row['URL Parsed']
                current_gt_org = gt_row['Organization_tolower_stripped']
                break
        if current_gt_origin and current_gt_org: 
            if (current_external_org == current_gt_org) and \
                (current_external_origin == current_gt_origin):
                    externalhost_df.loc[index, 'Human Label'] = 'Information browsing'
            else:
                pass
except Exception as e: 
    print(e)


try: 
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_origin = row['URL Parsed']
        current_external_org = row['Organization_tolower_stripped']
       
       
        current_gt_origin = None
        current_gt_org = None
        for gt_index, gt_row in gt_row_news.iterrows():
            if current_external_org == gt_row['Organization_tolower_stripped']\
                and current_external_origin == gt_row['URL Parsed']:
                current_gt_origin = gt_row['URL Parsed']
                current_gt_org = gt_row['Organization_tolower_stripped']
                break
        if current_gt_origin and current_gt_org: 
            if (current_external_org == current_gt_org) and \
                (current_external_origin == current_gt_origin):
                    externalhost_df.loc[index, 'Human Label'] = 'News'
            else:
                pass
except Exception as e: 
    print(e)
    
try:
    for index, row in externalhost_df.iterrows():
        url = True
        current_external_origin = row['URL Parsed']
        current_external_org = row['Organization_tolower_stripped']
        
        
        current_gt_origin = None
        current_gt_org = None
        for gt_index, gt_row in gt_row_sm.iterrows():
            if current_external_org == gt_row['Organization_tolower_stripped']\
                and current_external_origin == gt_row['URL Parsed']:
                current_gt_origin = gt_row['URL Parsed']
                current_gt_org = gt_row['Organization_tolower_stripped']
                break
        if current_gt_origin and current_gt_org: 
            if (current_external_org == current_gt_org) and \
                (current_external_origin == current_gt_origin):
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
if debugging:
    # result_df2.to_csv('/home/herman/human_app_label_testing/merged_conn_6676.csv', index=False) 
    result_df2.to_csv('/home/herman/human_app_label_testing/merged_connections_23952_20240410035036.csv', index=False) 


else:
    result_df2.to_csv(f'/opt/firefox/human_app_label/NativeApp/mergedOutput/merged_connections_{pid}_{timestamp}.csv', index=False)
