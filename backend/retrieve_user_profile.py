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
    "response": "Sorry we couldn't locate you in our records with {search_type}# {search_value}. Could you please check your details again?"
}

def get_dynamodb_table_name():
    """
    Loads and returns the DynamoDB table name from the .env file.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME")

    if not table_name:
        raise ValueError("DYNAMODB_TABLE_NAME not found in .env file")

    return table_name

def search_booking_record(search_type, search_value):
    """
    Search for booking records by either airpointsNumber or bookingReference

    Parameters:
    search_type (str): Either 'airpoints' or 'booking'
    search_value (str): The value to search for

    Returns:
    list: List of matching booking records or return defaultResponse if none found
    """
    
    search_value = str(search_value)
    
    # Remove any space, - or dot in search value
    search_value = search_value.replace(" ", "").replace("-", "").replace(".", "")
    logger.info(f"Inside retrieve_user_profile:search_booking_record: search_type: {search_type} and search_value: {search_value}")
    
    if search_value.isdigit():
        search_type = "airpoints"
    else:
        search_type = "booking"

    try:
        table_name = get_dynamodb_table_name()
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)
        
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
            raise ValueError("search_type must be either 'airpoints' or 'booking reference'")

        if response['Count'] > 0:
            # Step 2: Get current datetime
            now = datetime.now()
            # return response 
            # Step 3: Filter and sort
            # Assumes 'departureDate' is 'YYYY-MM-DD' and 'departureTime' is 'HH:MM' (24-hour)
            upcoming_flights = []

            for item in response['Items']:
                dep_datetime_str = f"{item['departureDate']} {item['departureTime']}"
                dep_datetime = datetime.strptime(dep_datetime_str, "%Y-%m-%d %H:%M")
                
                if dep_datetime > now:
                    upcoming_flights.append(item)

            # Step 4: Sort upcoming flights
            sorted_flights = sorted(
                upcoming_flights,
                key=lambda x: (x['departureDate'], x['departureTime'])
            )
            lookupResult = {"status": "success", "response": sorted_flights}
            logger.info(f"retrieved user profile: {json.dumps(lookupResult)}")
            return lookupResult
        else:
            logger.info(f"No booking records found for {search_type}: {search_value}")
            defaultResponse["response"] = defaultResponse["response"].format(
                search_type=search_type,
                search_value=search_value
            )            
            return defaultResponse
    
    except Exception as e:
        logger.error(f"Error during user profile search: {e}")
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

def lookup_airpoints_number(airpoints_number: str):
    """
    Looks up an airpoints number in DynamoDB where it's the primary key.

    Args:
        airpoints_number (str): The Airpoints number to look up

    Returns:
        dict: The item found in DynamoDB

    Raises:
        ValueError, ConnectionError, RuntimeError
    """

    try:
        table_name = get_dynamodb_table_name()
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        response = table.get_item(Key={"airpointsNumber": airpoints_number})

        if "Item" in response:
            return response["Item"]
        else:
            logger.info(f"No DDB entry found for Airpoints number {airpoints_number}")
            return defaultResponse

    except (ProfileNotFound, NoCredentialsError) as e:
        logger.error(f"AWS credential error: {str(e)}")
        return defaultResponse

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        if error_code == "ResourceNotFoundException":
            table_name = get_dynamodb_table_name()
            logger.error(f"Table {table_name} not found: {error_message}")
            raise RuntimeError(f"DynamoDB table not found: {error_message}")
        elif error_code == "ProvisionedThroughputExceededException":
            logger.warning(f"DynamoDB throughput exceeded: {error_message}")
            raise ConnectionError(f"DynamoDB throughput exceeded: {error_message}")
        else:
            logger.error(f"DynamoDB ClientError: {error_code} - {error_message}")
            raise RuntimeError(f"DynamoDB error: {error_message}")
        return defaultResponse
    except ConnectionError as e:
        logger.error(f"Network error connecting to AWS: {str(e)}")
        raise ConnectionError(f"Network error connecting to AWS: {str(e)}")
        return defaultResponse
    except Exception as e:
        logger.error(f"Unexpected error querying DynamoDB: {str(e)}")
        raise RuntimeError(f"Error querying DynamoDB: {str(e)}")
        return defaultResponse

def main(airpoints_number: str):
    """
    Main function to process Airpoints number lookup requests.

    Args:
        airpoints_number (str): The Airpoints number to look up

    Returns:
        dict or int: Lookup result if successful, or error description
    """
    if not airpoints_number:
        logger.error("No Airpoints number provided")
        error = {"error": "No Airpoints number provided"}
        print(json.dumps(error, indent=2))
        return defaultResponse
    try:
        clean_number = str(airpoints_number).replace("-", "").strip()

        if not clean_number.isalnum():
            logger.debug("Invalid Airpoints number format.")
            return defaultResponse

        result = lookup_airpoints_number(clean_number)

        if result:
            output = {
                "airpointsNumber": airpoints_number,
                "clean_number": clean_number,
                "found": True,
                "data": result,
            }
        else:
            output = {
                "airpointsNumber": airpoints_number,
                "clean_number": clean_number,
                "found": False,
            }

        print(json.dumps(output, indent=2))
        return result

    except (ProfileNotFound, NoCredentialsError) as e:
        logger.error(f"AWS credential error: {str(e)}")
        raise ValueError(f"AWS credential error: {str(e)}")
        return defaultResponse

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        if error_code == "ResourceNotFoundException":
            logger.error(f"Table {table_name} not found: {error_message}")
            raise RuntimeError(f"DynamoDB table not found: {error_message}")
        elif error_code == "ProvisionedThroughputExceededException":
            logger.warning(f"DynamoDB throughput exceeded: {error_message}")
            raise ConnectionError(f"DynamoDB throughput exceeded: {error_message}")
        else:
            logger.error(f"DynamoDB ClientError: {error_code} - {error_message}")
            raise RuntimeError(f"DynamoDB error: {error_message}")
        return defaultResponse

    except ConnectionError as e:
        logger.error(f"Network error connecting to AWS: {str(e)}")
        raise ConnectionError(f"Network error connecting to AWS: {str(e)}")
        return defaultResponse

    except Exception as e:
        logger.error(f"Unexpected error querying DynamoDB: {str(e)}")
        raise RuntimeError(f"Error querying DynamoDB: {str(e)}")
        return defaultResponse


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <airpoints_number>")
        sys.exit(1)        

    airpoints_number = sys.argv[1]
    sys.exit(main(airpoints_number))
