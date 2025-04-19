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
    "response": "Sorry we couldn't locate you in our records with booking reference {search_value}. Could you please check your details again?"
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


def submit_request(booking_reference: str, meal_type: str):
    """
    Books inflight services like meals or assistance.

    Args:
        booking_reference (str): Booking reference number.
        meal_type (str): Requested special meal type.

    Returns:
        dict: Updated booking information or error response.
    """
    meal_type = str(meal_type)
    booking_reference = str(booking_reference).replace(" ", "").replace("-", "").replace(".", "")
    
    logger.info(f"Processing request - Booking Ref: {booking_reference}, Meal Type: {meal_type}")

    try:
        table_name = get_dynamodb_table_name()
        index_name = f"{table_name}-index"
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        # Query using the bookingReference GSI
        response = table.query(
            IndexName=index_name,
            KeyConditionExpression=Key('bookingReference').eq(booking_reference)
        )

        items = response.get('Items', [])

        if not items:
            logger.info(f"No booking records found for booking reference number {booking_reference}")
            response_obj = defaultResponse.copy()
            response_obj["response"] = response_obj["response"].format(
                search_value=booking_reference
            )

        for item in items:
            pk = item.get('airpointsNumber')
            sk = item.get('bookingReference')

            update_response = table.update_item(
                Key={
                    'airpointsNumber': pk,
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

        if error_code == "ResourceNotFoundException":
            logger.error(f"DynamoDB table not found: {error_message}")
            return systemError
        elif error_code == "ProvisionedThroughputExceededException":
            logger.error(f"DynamoDB throughput exceeded: {error_message}")
            return systemError
        else:
            logger.error(f"DynamoDB error: {error_message}")
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
    logger.info(f"Received booking reference: {booking_reference} and meal type: {meal_type}")
    result = submit_request(booking_reference, meal_type)
    logger.info(f"Result: {json.dumps(result)}")
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <booking_reference> <meal_type>")
        sys.exit(1)

    booking_reference = sys.argv[1]
    meal_type = sys.argv[2]
    result = main(booking_reference, meal_type)

    sys.exit(0 if result and result.get("status", "") != "error" else 1)
