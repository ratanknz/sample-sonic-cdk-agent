#!/usr/bin/env python3
import csv
import json
import subprocess
import sys

def clean_json_string(json_str):
    # Replace double quotes within the JSON string
    return json_str.replace('\"\"', '"')

def import_to_dynamodb(csv_file, table_name):
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Clean and parse the upcomingTravel JSON
            if 'upcomingTravel' in row:
                row['upcomingTravel'] = clean_json_string(row['upcomingTravel'])
            
            # Create the item in DynamoDB
            item = {
                'airpointsNumber': {'S': row['airpointsNumber']},
                'emailID': {'S': row['emailID']},
                'fullName': {'S': row['fullName']},
                'locationCountry': {'S': row['locationCountry']}
            }
            
            # Add upcomingTravel if it exists
            if 'upcomingTravel' in row:
                item['upcomingTravel'] = {'S': row['upcomingTravel']}
            
            # Convert the item to JSON
            item_json = json.dumps(item)
            
            # Use AWS CLI to put the item
            cmd = [
                'aws', 'dynamodb', 'put-item',
                '--table-name', table_name,
                '--item', item_json,
                '--region', 'us-east-1'
            ]
            
            print(f"Importing item: {row['airpointsNumber']}")
            subprocess.run(cmd, check=True)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python import_csv_to_dynamodb.py <csv_file> <table_name>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    table_name = sys.argv[2]
    
    import_to_dynamodb(csv_file, table_name)
    print("Import completed successfully!")
