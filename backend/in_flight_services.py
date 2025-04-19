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
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
# Load environment variables from .env file
load_dotenv()

defaultResponse = {
    "status": "error",
    "response": "Sorry we are unable to fulfill your request at this moment. Please try via manage bookings or contact our customer support."
} 

def get_dynamodb_table_name():
    """
    Loads and returns the DynamoDB table name from the .env file.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME")

    if not table_name:
        raise ValueError("DYNAMODB_TABLE_NAME not found in .env file")

    return table_name

def submit_request(booking_reference, mealType):
    """
    Book inflight services like meal, assistance and others 

    Parameters:
    booking_reference (str): booking reference number
    mealType (str): requested special meal type
    Returns:
        Updated flight details with inflight services added to it.
    """
    
    mealType = str(mealType)
    
    # Remove any space, - or dot in search value
    booking_reference = str(booking_reference)
    booking_reference = booking_reference.replace(" ", "").replace("-", "").replace(".", "")
    logger.info(f"Inside in_flight_services:submit_request: booking ref: {booking_reference} and meal type: {mealType}")
    
    try:
        table_name = get_dynamodb_table_name()
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        # Query GSI where bookingReference matches
        response = table.query(
            IndexName='bookingReference-index',
            KeyConditionExpression=Key('bookingReference').eq(booking_reference)
        )

        items = response.get('Items', [])

        if not items:
        # return an error so Sonic can allow user to retry with correct reference number    
            defaultResponse = {
                "status": "error",
                "response": "We couldn't locate your booking by booking reference number {bookingReference}. Could you please double check?"
            } 
            defaultResponse["response"] = defaultResponse["response"].format(
                bookingReference=booking_reference,
            )    
            return defaultResponse             
        else:
        # else booking with requestedMeal type
            for item in items:
                # Replace 'PK' and 'SK' with your actual primary key names
                pk = item['airpointsNumber']
                sk = item['bookingReference']  # Remove this if your table doesn't use sort keys

                # Update meal field for each item
                update_response = table.update_item(
                    Key={
                        'airpointsNumber': pk,
                        'bookingReference': sk  
                    },
                    UpdateExpression="SET mealSelected = :meal",
                    ExpressionAttributeValues={
                        ':meal': mealType
                    },
                    ReturnValues="ALL_NEW"  # This returns the updated item
                )

                updated_item = update_response.get('Attributes', {})
                return updated_item
                
    except Exception as e:
        logger.error(f"Error processing meal request: {e}")
        return defaultResponse
    
    # TODO: you must return a response for Sonic indicating there is some sort of catastrophic failure and we cannot serve the user at this time.
    except (ProfileNotFound, NoCredentialsError) as e:
        logger.error(f"retrieve_user_profile.search_booking_record: AWS credential error: {str(e)}")
        return defaultResponse
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        if error_code == "ResourceNotFoundException":
            table_name = get_dynamodb_table_name()
            logger.error(f"retrieve_user_profile.search_booking_record: Table {table_name} not found: {error_message}")
            raise RuntimeError(f"retrieve_user_profile.search_booking_record: DynamoDB table not found: {error_message}")
        elif error_code == "ProvisionedThroughputExceededException":
            logger.error(f"retrieve_user_profile.search_booking_record: DynamoDB throughput exceeded: {error_message}")
            raise ConnectionError(f"retrieve_user_profile.search_booking_record: DynamoDB throughput exceeded: {error_message}")
        else:
            logger.error(f"retrieve_user_profile.search_booking_record: DynamoDB ClientError: {error_code} - {error_message}")
            raise RuntimeError(f"retrieve_user_profile.search_booking_record: DynamoDB error: {error_message}")
    except ConnectionError as e:
        logger.error(f"retrieve_user_profile.search_booking_record: Network error connecting to AWS: {str(e)}")
        raise ConnectionError(f"Network error connecting to AWS: {str(e)}")


def main(airpoints_number: str):
    """
    Main function to process Airpoints number lookup requests.

    Args:
        airpoints_number (str): The Airpoints number to look up

    Returns:
        dict or int: Lookup result if successful, or error description
    """
    return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <airpoints_number>")
        sys.exit(1)        

    airpoints_number = sys.argv[1]
    sys.exit(main(airpoints_number))
