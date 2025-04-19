import os
import sys
import json
import logging
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Default responses
defaultResponse = {
    "status": "error",
    "response": "Sorry we couldn't locate you in our records with {search_type}# {search_value}. Could you please check your details again?"
}

systemError = {
    "status": "error",
    "response": "We are currently unable to retrieve your booking. Please try again later."
}


def get_dynamodb_table_name():
    """Loads and returns the DynamoDB table name from the .env file."""
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    if not table_name:
        raise ValueError("DYNAMODB_TABLE_NAME not found in .env file")
    return table_name


def search_booking_record(search_type, search_value):
    """
    Search for booking records by either airpointsNumber or bookingReference.

    Args:
        search_type (str): 'airpoints' or 'booking'
        search_value (str): Search value

    Returns:
        dict: Lookup result or error response
    """
    table_name = get_dynamodb_table_name()
    index_name = f"{table_name}-index"
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    search_value = str(search_value).replace(" ", "").replace("-", "").replace(".", "")
    logger.info(f"search_booking_record: search_type={search_type}, search_value={search_value}")

    try:
        if search_type.lower() == 'airpoints':
            response = table.query(
                KeyConditionExpression=Key('airpointsNumber').eq(search_value)
            )
        elif search_type.lower() == 'booking':
            response = table.query(
                IndexName=index_name,
                KeyConditionExpression=Key('bookingReference').eq(search_value.upper())
            )
        else:
            raise ValueError("search_type must be either 'airpoints' or 'booking'")

        logger.info(f"Query result: {json.dumps(response)}")

        if response['Count'] > 0:
            now = datetime.now()
            upcoming_flights = []

            for item in response['Items']:
                dep_str = f"{item['departureDate']} {item['departureTime']}"
                dep_datetime = datetime.strptime(dep_str, "%Y-%m-%d %H:%M")

                if dep_datetime > now:
                    upcoming_flights.append(item)

            sorted_flights = sorted(
                upcoming_flights,
                key=lambda x: (x['departureDate'], x['departureTime'])
            )

            result = {"status": "success", "response": sorted_flights}
            logger.info(f"Upcoming flights found: {json.dumps(result)}")
            return result

        logger.info(f"No booking records found for {search_type}: {search_value}")
        response_obj = defaultResponse.copy()
        response_obj["response"] = response_obj["response"].format(
            search_type=search_type,
            search_value=search_value
        )
        return response_obj

    except (ProfileNotFound, NoCredentialsError) as e:
        logger.error(f"AWS credential error: {str(e)}")
        return systemError

    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        logger.error(f"DynamoDB ClientError: {code} - {msg}")
        return systemError

    except ConnectionError as e:
        logger.error(f"Network error: {str(e)}")
        return systemError

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return systemError


def main(search_type: str, search_value: str):
    """
    Main function to process lookup requests.

    Args:
        search_type (str): 'airpoints' or 'booking'
        search_value (str): ID value to search

    Returns:
        dict: Lookup result or error response
    """
    if not search_type or not search_value:
        logger.error("Missing search_type or search_value")
        print(json.dumps({"error": "Missing search_type or search_value"}, indent=2))
        return defaultResponse

    try:
        clean_value = str(search_value).replace("-", "").strip()

        if not clean_value.isalnum():
            logger.debug("Invalid input format.")
            return defaultResponse

        result = search_booking_record(search_type, clean_value)

        output = {
            "search_type": search_type,
            "search_value": search_value,
            "clean_value": clean_value,
            "found": bool(result and result.get("status") == "success"),
            "data": result
        }

        print(json.dumps(output, indent=2))
        return result

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise RuntimeError(f"Error querying DynamoDB: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <search_type: booking|airpoints> <search_value>")
        sys.exit(1)

    search_type_arg = sys.argv[1]
    search_value_arg = sys.argv[2]

    result = main(search_type_arg, search_value_arg)
    sys.exit(0 if result and result.get("status") == "success" else 1)
