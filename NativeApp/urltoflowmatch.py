from datetime import datetime
import sys
import pytz
import pandas as pd
import time
import whois
import os
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse
from ProgressBar import ProgressBar 


def whois_lookup(host, fallback_ip, fallback_whois):
    
    try:
        if fallback_ip:
            result = whois.whois(fallback_ip)
        else:
            result = whois.whois(host)
            
        organization = extract_organization(result, fallback_whois)

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

# This function takes a url and returns domain.tld 
def extract_domain_host(hostname):
     
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
    
def process_external(label, df, current_host, total_hosts):
    unique_hosts = df['Host'].unique()
    
    ret_vals = []
    
    for idx, host in enumerate(unique_hosts):
        
        fallback_ip = None
        fallback_whois = False
        result = whois_lookup(host, fallback_ip, fallback_whois)

        if isinstance(result, list):
            organization = result[0]
        else:
            organization = result
        if organization is not None and organization.strip() != '':
            print(f"Registrant org for {host}: {organization}")
        
        
        elif organization is None or organization.strip() == '':
            
            print(f'Whois failed for host {host}! Using webscrape...')
            time.sleep(1)
            result = whois_scraper(host)
            
            if isinstance(result, list):
                organization = result[0]
            else:
                organization = result
            if organization is not None and organization.strip() != '':
                print(f"Registrant org found for host {host} using webscrape: {organization}")
            
        
            elif organization is None or organization.strip() == '':
                print(f'Whois failed for host {host}! Trying again...')
                fallback_whois = True
                time.sleep(1)
                result = whois_lookup(host, fallback_ip, fallback_whois)
                
                if isinstance(result, list):
                    organization = result[0]
                else:
                    organization = result
                    
                if organization is not None and organization.strip() != '':
                    print(f"Registrant org for {host}: {organization}")
                
                
                elif organization is None or organization.strip == '':
                    fallback_ip = df.loc[df['Host'] == host, 'DST_IP'].values[0]
                    print(f"Whois failed! Using IP {fallback_ip}...")
                    time.sleep(1)
                    result = whois_lookup(host, fallback_ip, fallback_whois)
                 
                    if isinstance(result, list):
                        organization = result[0]
                    else:
                        organization = result
                    if organization is not None and organization.strip() != '':
                        print(f"Registrant org found for host {host} using IP: {fallback_ip}: {organization}")
                    time.sleep(1)
        
        
        if organization is not None:
            df.loc[df['Host'] == host, 'Organization'] = organization
            words = organization.split()
            first_word = words[0]
            cleaned_word = first_word.lower().strip().replace(",", "")
            df.loc[df['Host'] == host, 'Organization_tolower_stripped'] =  cleaned_word
        
            current_host += 1
            progress_percentage = int((current_host / total_hosts) * 100)
            progress_bar.update_progress(progress_percentage)
    ret_vals.append(df)
    ret_vals.append(current_host)
        
    return ret_vals
        
def check_duplicate(new_flows, prev_flows):
    if new_flows in prev_flows:
        return True
    else:
        return False

## Get args
def getOptions():
    if len(sys.argv) != 5:
        # All defaults
        print("Usage : Merge.py connections.csv flows.csv timestamp PID")
        sys.exit(1)
    global urlstream_file
    urlstream_file = sys.argv[1]
    global flowFile
    flowFile = sys.argv[2]
    global timestamp 
    timestamp = sys.argv[3]
    global pid 
    pid = sys.argv[4]
    print("urlstream_file is : " + urlstream_file)
    print("flowFile is : " + flowFile)
    print("timestamp is: " + timestamp)
    print("PID is: " + pid)
    return

## Global Variables
urlstream_file = ""
flowFile = ""
timestamp = ""
pid = ""
debugging = False
home_dir = os.path.expanduser("~")
## Max difference between connection epoch and pcmacct epoch
## TODO: Make the timeWindow an option in hals.conf
timeWindow = 30000

categories_file = '/opt/firefox/human_app_label/NativeApp/categories.json'

if debugging:
    urlstream_file = '/opt/firefox/human_app_label/NativeApp/work/urlstream.21058.20240429060059.csv'
    flowFile = '/opt/firefox/human_app_label/pmacct/flows/flows.21078.csv'
else:
    getOptions()

merged_flows = []
prev_flows = []


url_df = pd.read_csv(urlstream_file)
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
    host_url = url_row['URL']
    host_name = url_row['Host']
    

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
                merged_flows.append(list(flow_row.values) + [user_sel,host_url,host_name,origin_url,flow_category] )
                prev_flows.append(list(flow_row.values))
                break  # Break from the inner looop
    
progress_bar.update_progress(100)

progress_bar.close()

df = pd.DataFrame(merged_flows)

df.columns = ['nDPI Label','SRC_IP','DST_IP','SRC_PORT','DST_PORT','PROTOCOL',\
                        'TIMESTAMP_START','TIMESTAMP_END', 'TIMESTAMP_ARRIVAL', \
                            'PACKETS','BYTES', 'Human Label','Host URL','Host Name','Origin URL',\
                                'Category']

if debugging: 
    df.to_csv(f'{home_dir}/debugging.csv', index = False)
    # df = pd.read_csv(f'{home_dir}/debugging.csv')



# array of all unique human labels present in the output
unique_labels = df['Human Label'].unique()

# empty dictionary to hold multiple dataframes that map to human labels
dfs = {}
concat_gt_dfs = []

# assigning each label its own dataframe in the dictionary
for label in unique_labels: 
    dfs[label] = df[df['Human Label'] == label]

total_hosts = 0

for label, df in dfs.items():
    df['Host'] = df['Host URL'].apply(extract_domain_host)
    df = df[df['Host'].notna()] 
    if label == 'ExternalHost':
        total_hosts += len(df['Host'].unique())
    else: 
        total_hosts += len(df['Host'].unique())




current_host = 0
for label, df in dfs.items():
    
    if label == 'ExternalHost':
      
        df['Origin URL Parsed'] = df['Origin URL'].apply(extract_domain_host)
        df = df[df['Origin URL Parsed'].notna()]
        df['Organization'] = None
        df['Organization_tolower_stripped'] = None
        
        
        progress_bar.show('whois')
        time.sleep(0.1)
        progress_bar.update_progress(0)
        queries = 0
        externalhost_df, queries = process_external(label, df, current_host, total_hosts)
        current_host += queries
        continue
    else:
    
        df['Organization'] = None 
        df['Organization_tolower_stripped'] = None
        df['Origin URL Parsed'] = df['Origin URL'].apply(extract_domain_host)

        # gt_df holds on the unique hosts that are the ground truth
        gt_df = df.drop_duplicates(subset='Host')
        gt_df = gt_df[gt_df['Host'].notna()]
        gt_df = gt_df[gt_df['Origin URL Parsed'].notna()]
        gt_org = None

       
        for host in gt_df['Host']:
                
            fallback_ip = None
            fallback_whois = False
            result = whois_lookup(host, fallback_ip, fallback_whois)
    
            if isinstance(result, list):
                gt_org = result[0]
            else:
                gt_org = result
            
            if gt_org is not None and gt_org.strip() != '':
                print(f"Registrant org for {host}: {gt_org}")
            
            elif gt_org is None or gt_org.strip() == '':
                
                print(f'Whois failed for host {host}! Using webscrape...')
                time.sleep(1)
                result = whois_scraper(host)
                
                if isinstance(result, list):
                    gt_org = result[0]
                else:
                    gt_org = result
                
                if gt_org is not None and gt_org.strip() != '':
                    print(f"Registrant org found for host {host} using webscrape: {gt_org}")
                                    
                elif gt_org is None or gt_org.strip() == '':
                    print(f'Whois failed for host {host}! Trying again...')
                    fallback_whois = True
                    time.sleep(1)
                    result = whois_lookup(host, fallback_ip, fallback_whois)
                   
                    if isinstance(result, list):
                        gt_org = result[0]
                    else:
                        gt_org = result
                    if gt_org is not None and gt_org.strip() != '':
                        print(f"Registrant org for {host}: {gt_org}")
                                    
                    elif gt_org is None or gt_org.strip() == '':
                        fallback_ip = gt_df.loc[gt_df['Host'] == host, 'DST_IP'].values[0]
                        print(f"Whois failed! Using IP {fallback_ip}...")
                        time.sleep(1)
                        result = whois_lookup(host, fallback_ip, fallback_whois)
                     
                        if isinstance(result, list):
                            gt_org = result[0]
                        else:
                            gt_org = result
                            
                        if gt_org is not None and gt_org.strip() != '':
                            print(f"Registrant org found for host {host} using IP: {fallback_ip}: {gt_org}")
            
                
            current_host += 1
            progress_percentage = int((current_host / total_hosts) * 100)
            progress_bar.update_progress(progress_percentage)
            
            gt_df.loc[gt_df['Host'] == host, 'Organization'] = gt_org
            gt_df.loc[gt_df['Host'] == host, 'Organization_tolower_stripped'] = gt_org.split()[0].lower()
         
        progress_bar.update_progress(100)
        progress_bar.close()
        
        for index, row in df.iterrows():
            if row['Host'] in gt_df['Host'].values:
                    matching_organization = gt_df.loc[gt_df['Host'] == row['Host'], 'Organization'].values
                    df.loc[index, 'Organization'] = matching_organization[0] if len(matching_organization) > 0 else 'Unknown'
                    org_str = matching_organization[0]
                    org_words =org_str.split()
                    first_word = org_words[0]
                    cleaned_org = first_word.replace(',', '').lower().strip()
                    df.loc[index, 'Organization_tolower_stripped'] = cleaned_org if len(matching_organization) > 0 else 'Unknown'
                
    concat_gt_dfs.append(df)


if concat_gt_dfs: 
    gt_dfs = pd.concat(concat_gt_dfs, ignore_index = True)


try:   
    for index, row in externalhost_df.iterrows():
        current_external_origin = row['Origin URL Parsed']
        current_external_org = row['Organization_tolower_stripped']
        
        current_gt_origin = None
        current_gt_org = None
        
        for gt_index, gt_row in gt_dfs.iterrows():
            if current_external_org == gt_row['Organization_tolower_stripped']\
                and current_external_origin == gt_row['Origin URL Parsed']:
                    
                current_gt_origin = gt_row['Origin URL Parsed']
                current_gt_org = gt_row['Organization_tolower_stripped']
                current_gt_label = gt_row['Human Label']
                break
            
        if current_gt_origin and current_gt_org: 
            if (current_external_org == current_gt_org) and \
                (current_external_origin == current_gt_origin):
                externalhost_df.loc[index, 'Human Label'] = current_gt_label
            else:
                pass
except Exception as e:
    print(e)

final_df = pd.concat([gt_dfs, externalhost_df], ignore_index = True)
columns_to_drop = ['Organization_tolower_stripped', 'Origin URL Parsed', 'Host']

final_df = final_df.drop(columns=columns_to_drop)

# Save output
if debugging:
    final_df.to_csv(f'{home_dir}/mergedflows_debugging.csv', index=False) 
else:
    final_df.to_csv(f'/opt/firefox/human_app_label/data/mergedflows_{pid}_{timestamp}.csv', index=False)
