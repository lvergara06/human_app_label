import csv
import json

csv_filename = "flows.csv"
json_filename = "connections.json"

# Load the JSON data
with open(json_filename, "r") as json_file:
    json_data = json.load(json_file)

# Open the CSV file
with open(csv_filename, "r") as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        dst_ip = row["DST_IP"]
        dst_port = row["DST_PORT"]
        if dst_ip == json_data["destinationIp"] and dst_port == json_data["destinationPort"]:
            # Merge the CSV row with JSON data
            row.update(json_data)
            
            # Convert integer values to strings
            row = {key: str(value) for key, value in row.items()}
            # Print the merged CSV row
            csv_row = ",".join(row.values())
            print(csv_row)
