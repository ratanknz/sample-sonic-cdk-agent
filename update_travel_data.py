#!/usr/bin/env python3
import boto3
import json

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='us-east-1')
table_name = 'sonic-demo-customerdata'

# Travel data to add to each customer record
travel_data = [
    {
        "flightNumber": "NZ101",
        "departureDate": "2025-04-25",
        "departureAirport": "AKL",
        "arrivalAirport": "SYD",
        "seatNumber": "12A",
        "bookingReference": "XYZ123"
    },
    {
        "flightNumber": "NZ202",
        "departureDate": "2025-05-10",
        "departureAirport": "SYD",
        "arrivalAirport": "WLG",
        "seatNumber": "15C",
        "bookingReference": "ABC789"
    }
]

# Convert travel data to DynamoDB format
travel_data_dynamo = {
    "L": [
        {
            "M": {k: {"S": v} for k, v in item.items()}
        } for item in travel_data
    ]
}

# Get all airpoints numbers from the table
print("Retrieving customer records from DynamoDB...")
response = dynamodb.scan(
    TableName=table_name,
    ProjectionExpression="airpointsNumber,fullName"
)

# Update each record with the travel data
for item in response['Items']:
    airpoints_number = item['airpointsNumber']['S']
    full_name = item.get('fullName', {}).get('S', 'Unknown')
    
    print(f"Updating travel data for {full_name} (Airpoints: {airpoints_number})")
    
    try:
        dynamodb.update_item(
            TableName=table_name,
            Key={'airpointsNumber': {'S': airpoints_number}},
            UpdateExpression="SET upcomingTravel = :travel",
            ExpressionAttributeValues={':travel': travel_data_dynamo}
        )
    except Exception as e:
        print(f"Error updating {airpoints_number}: {str(e)}")

print("All customer records updated with upcoming travel data!")
