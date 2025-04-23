#
# Copyright 2025 Amazon.com, Inc. and its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#   http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.
#

import boto3
from boto3.dynamodb.conditions import Key
import json
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

defaultResponse = {
    "status": "error",
    "response": "Sorry we couldn't locate you in our records with booking reference. Could you please check your details again?"
}

systemError = {
    "status": "error",
    "response": "We are currently unable to retrieve your booking. Please try again later."
}

def get_dynamodb_table_name():
    """
    Loads and returns the DynamoDB table name from environment variables.
    Raises:
        ValueError: If the table name is not set.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    if not table_name:
        raise ValueError("DYNAMODB_TABLE_NAME not found in .env file")
    return table_name

from datetime import datetime, timedelta, timezone

from datetime import datetime, timedelta, timezone

def submit_request(booking_reference: str, meal_type: str):
    """
    Books inflight services like meals or assistance, only if the departure time is more than 24 hours away.

    Args:
        booking_reference (str): Booking reference number.
        meal_type (str): Requested special meal type.

    Returns:
        dict: Updated booking information or error response.
    """
    meal_type = str(meal_type)
    booking_reference = str(booking_reference).replace(" ", "").replace("-", "").replace(".", "")
    
    # logger.info(f"Processing request - Booking Ref: {booking_reference}, Meal Type: {meal_type}")

    try:
        table_name = get_dynamodb_table_name()
        index_name = f"{table_name}-index"
        
        # session = boto3.Session()
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        # Query using the bookingReference GSI
        response = table.query(
            IndexName=index_name,
            KeyConditionExpression=Key('bookingReference').eq(booking_reference.upper())
        )

        items = response.get('Items', [])

        if not items:
            # logger.info(f"No booking records found for booking reference number {booking_reference}")
            # response_obj = defaultResponse.copy()
            # response_obj["response"] = response_obj["response"].format(search_value=booking_reference)
            # return response_obj
            return defaultResponse

        for item in items:
            departure_date_str = item.get('departureDate')
            departure_time_str = item.get('departureTime')

            if not departure_date_str or not departure_time_str:
                # logger.warning(f"Departure date/time missing for booking {booking_reference}")
                return {
                    "status": "error",
                    "response": "Departure date/time not available for this booking."
                }
            try:
                combined_datetime_str = f"{departure_date_str} {departure_time_str}"
                departure_time = datetime.strptime(combined_datetime_str, "%Y-%m-%d %H:%M")
                departure_time = departure_time.replace(tzinfo=timezone.utc)
            except ValueError:
                # logger.error(f"Invalid departure date/time format: {combined_datetime_str}")
                return {
                    "status": "error",
                    "response": "Invalid departure time format. Please contact support."
                }

            current_time = datetime.now(timezone.utc)
            if departure_time - current_time < timedelta(hours=24):
                # logger.info(f"Meal request rejected for {booking_reference}: Less than 24 hours to departure")
                return {
                    "status": "error",
                    "response": "Meal requests must be made at least 24 hours before departure."
                }

            pk = item.get('customerNumber')
            sk = item.get('bookingReference')

            update_response = table.update_item(
                Key={
                    'customerNumber': pk,
                    'bookingReference': sk
                },
                UpdateExpression="SET mealSelected = :meal",
                ExpressionAttributeValues={':meal': meal_type},
                ReturnValues="ALL_NEW"
            )

            updated_item = update_response.get('Attributes', {})
            return updated_item

    except (ProfileNotFound, NoCredentialsError) as e:
        logger.error(f"AWS credential error: {str(e)}")
        return systemError

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"DynamoDB ClientError: {error_code} - {error_message}")
        return systemError

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return systemError


def main(booking_reference: str, meal_type: str):
    """
    Main function to handle the booking update request.

    Args:
        booking_reference (str): The booking reference number.
        meal_type (str): The selected meal type.
 
    Returns:
        dict or None: Result of the booking update operation.
    """
    # logger.info(f"Received booking reference: {booking_reference} and meal type: {meal_type}")
    result = submit_request(booking_reference, meal_type)
    # logger.info(f"Result: {json.dumps(result)}")
    return result


# you can test this code by running python in_flight_services.py <booking_ref> <meal_type>
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <booking_reference> <meal_type>")
        sys.exit(1)

    booking_reference = sys.argv[1]
    meal_type = sys.argv[2]
    result = main(booking_reference, meal_type)

    sys.exit(0 if result and result.get("status", "") != "error" else 1)
