#!/bin/bash

# DynamoDB table name
TABLE_NAME="sonic-demo-customerdata"
REGION="us-east-1"

# Get all airpoints numbers from the table
echo "Retrieving customer records from DynamoDB..."
AIRPOINTS_NUMBERS=$(aws dynamodb scan \
  --table-name $TABLE_NAME \
  --projection-expression "airpointsNumber" \
  --region $REGION \
  --query "Items[*].airpointsNumber.S" \
  --output text)

# Update each record with the travel data
for AIRPOINTS_NUMBER in $AIRPOINTS_NUMBERS; do
  echo "Updating travel data for customer with Airpoints Number: $AIRPOINTS_NUMBER"
  
  aws dynamodb update-item \
    --table-name $TABLE_NAME \
    --key '{"airpointsNumber": {"S": "'$AIRPOINTS_NUMBER'"}}' \
    --update-expression "SET upcomingTravel = :travel" \
    --expression-attribute-values '{":travel": {"L": [
      {"M": {
        "flightNumber": {"S": "NZ101"},
        "departureDate": {"S": "2025-04-25"},
        "departureAirport": {"S": "AKL"},
        "arrivalAirport": {"S": "SYD"},
        "seatNumber": {"S": "12A"},
        "bookingReference": {"S": "XYZ123"}
      }},
      {"M": {
        "flightNumber": {"S": "NZ202"},
        "departureDate": {"S": "2025-05-10"},
        "departureAirport": {"S": "SYD"},
        "arrivalAirport": {"S": "WLG"},
        "seatNumber": {"S": "15C"},
        "bookingReference": {"S": "ABC789"}
      }}
    ]}}' \
    --region $REGION
done

echo "All customer records updated with upcoming travel data!"
