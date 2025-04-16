import boto3
from boto3.dynamodb.conditions import Key
import json
import logging 

# Configure logging
logger = logging.getLogger(__name__)

defaultResponse = {"emailID": "", "airpointsNumber": "", "fullName": "", 
                   "locationCountry": "", "status":"error", 
                   "errorDescription":"Sorry we couldn't locate you in our records. Could you please check your details again?"
                   }


def search_booking_record(search_type, search_value):
    """
    Search for booking records by either airpointsNumber or bookingReference
    
    Parameters:
    search_type (str): Either 'airpoints' or 'booking'
    search_value (str): The value to search for
    
    Returns:
    list: List of matching booking records
    """
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('voiceBot-BookingRecord')
    
    if search_type.lower() == 'airpoints':
        # Search by airpointsNumber (partition key)
        response = table.query(
            KeyConditionExpression=Key('airpointsNumber').eq(search_value)
        )
    elif search_type.lower() == 'booking':
        # Search by bookingReference using the GSI
        response = table.query(
            IndexName='bookingReference-index',
            KeyConditionExpression=Key('bookingReference').eq(search_value)
        )
    else:
        raise ValueError("search_type must be either 'airpoints' or 'booking'")
    
    return response.get('Items', [])

def pretty_print_results(results):
    """Print results in a readable format"""
    if not results:
        print("No matching records found.")
        return
    
    print(f"Found {len(results)} matching record(s):")
    for item in results:
        print(json.dumps(item, indent=2))

def search_booking_record1(search_type, search_value):
    """
    Search for booking records by either airpointsNumber or bookingReference

    Parameters:
    search_type (str): Either 'airpoints' or 'booking'
    search_value (str): The value to search for

    Returns:
    list: List of matching booking records or return defaultResponse if none found
    """
    # logger.info(f"Inside retrieve_user_profile:search_booking_record: search_type: {search_type} and search_value: {search_value}")
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('voiceBot-BookingRecord')
        if search_type.lower() == 'airpoints':
            # Search by airpointsNumber (partition key)
            response = table.query(
                KeyConditionExpression=Key('airpointsNumber').eq(search_value)
            )
            logger.info(f"Inside retrieve_user_profile:search_booking_record: search result returned: {json.dumps(response)}")
            # return response
        elif search_type.lower() == 'booking':
            # Search by bookingReference using the GSI, reference numbers are stored in DB in uppercase.
            search_value = search_value.upper()

            response = table.query(
                IndexName='bookingReference-index',
                KeyConditionExpression=Key('bookingReference').eq(search_value)
            )
            logger.info(f"Inside retrieve_user_profile:search_booking_record: search result returned: {json.dumps(response)}")
            # return response 
        else:
            raise ValueError("search_type must be either 'airpoints' or 'booking'")

        if response['Count'] > 0:
            return response
        else:
            logger.info(f"No booking records found for {search_type}: {search_value}")
            return defaultResponse

        # print(json.dumps(response))    
        # items = response.get('Items')
        # print(json.dumps(items)) 
        # if not items:
        #     # logger.info(f"No booking records found for {search_type}: {search_value}")
        #     return 'not found'
        # return items if items else 'not found'
    
    except Exception as e:
        # logger.error(f"Error during user profile search: {e}")
        return 'exeception'


# Example usage:
if __name__ == "__main__":
    # Example 1: Search by Airpoints number
    airpoints_number = "123456780"  # Replace with actual airpoints number
    results = search_booking_record1('airpoints', airpoints_number)
    # print(f"\nSearch results for Airpoints number: {airpoints_number}")
    # pretty_print_results(results)
    
    # Example 2: Search by Booking reference
    booking_ref = "MWOWM"  # Replace with actual booking reference
    # results = search_booking_record1('booking', booking_ref)
    # print(f"\nSearch results for Booking reference: {booking_ref}")
    # pretty_print_results(results)
    print(json.dumps(results))