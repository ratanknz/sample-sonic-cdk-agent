"""
Script to read records from voiceBot-CustomerData DynamoDB table and populate
voiceBot-BookingRecord table with booking information.
"""

import boto3
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
source_table = dynamodb.Table('voiceBot-CustomerData')
target_table = dynamodb.Table('voiceBot-BookingRecord')

def process_customer_data():
    """
    Reads all records from voiceBot-CustomerData and extracts booking information
    to populate the voiceBot-BookingRecord table.
    """
    try:
        # Scan the source table to get all customer records
        response = source_table.scan()
        items = response.get('Items', [])
        
        # Process additional pages if available
        while 'LastEvaluatedKey' in response:
            response = source_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        logger.info(f"Found {len(items)} customer records to process")
        
        # Counter for successful writes
        successful_writes = 0
        
        # Process each customer record
        for customer in items:
            airpoints_number = customer.get('airpointsNumber')
            full_name = customer.get('fullName', '')
            email = customer.get('emailID', '')
            
            # Check if customer has upcoming travel information
            upcoming_travel = customer.get('upcomingTravel', [])
            
            if not airpoints_number or not upcoming_travel:
                logger.warning(f"Skipping record - missing required data: {customer}")
                continue
            
            # Process each booking in the customer's upcoming travel
            for travel in upcoming_travel:
                # Extract booking details
                booking_ref = travel.get('bookingReference')
                if not booking_ref:
                    logger.warning(f"Skipping travel record - missing booking reference: {travel}")
                    continue
                
                # Create a new record for the booking
                booking_record = {
                    'airpointsNumber': airpoints_number,
                    'bookingReference': booking_ref,
                    'fullName': full_name,
                    'emailID': email,
                    'flightNumber': travel.get('flightNumber', ''),
                    'departureDate': travel.get('departureDate', ''),
                    'departureTime': travel.get('departureTime', ''),
                    'departureAirport': travel.get('departureAirport', ''),
                    'arrivalAirport': travel.get('arrivalAirport', ''),
                    'seatNumber': travel.get('seatNumber', '')
                }
                
                # Write the booking record to the target table
                target_table.put_item(Item=booking_record)
                successful_writes += 1
                logger.info(f"Added booking record: {airpoints_number} - {booking_ref}")
        
        logger.info(f"Successfully added {successful_writes} booking records")
        return successful_writes
        
    except ClientError as e:
        logger.error(f"Error processing customer data: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting to populate booking records")
    try:
        record_count = process_customer_data()
        logger.info(f"Script completed successfully. Added {record_count} booking records.")
    except Exception as e:
        logger.error(f"Script failed: {e}")
