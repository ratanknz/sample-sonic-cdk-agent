#!/usr/bin/env python3

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
import json
import logging
import os
import sys
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)
# Load environment variables from .env file
load_dotenv()


def get_dynamodb_table_name():
    """
    Loads and returns the DynamoDB table name from the .env file.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME")

    if not table_name:
        raise ValueError("DYNAMODB_TABLE_NAME not found in .env file")

    return table_name


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
            logger.info("No DDB entry found for Airpoints number")
            return "Sorry we couldn't locate you in our records. Could you please check your details again?"

    except (ProfileNotFound, NoCredentialsError) as e:
        logger.error(f"AWS credential error: {str(e)}")
        raise ValueError(f"AWS credential error: {str(e)}")

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

    except ConnectionError as e:
        logger.error(f"Network error connecting to AWS: {str(e)}")
        raise ConnectionError(f"Network error connecting to AWS: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error querying DynamoDB: {str(e)}")
        raise RuntimeError(f"Error querying DynamoDB: {str(e)}")


def main(airpoints_number: str):
    """
    Main function to process Airpoints number lookup requests.

    Args:
        airpoints_number (str): The Airpoints number to look up

    Returns:
        dict or int: Lookup result if successful, or error code (1) if failed
    """
    if not airpoints_number:
        logger.error("No Airpoints number provided")
        error = {"error": "No Airpoints number provided"}
        print(json.dumps(error, indent=2))
        return 1

    try:
        clean_number = str(airpoints_number).replace("-", "").strip()

        if not clean_number.isalnum():
            logger.debug("Invalid Airpoints number format.")
            return 1

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

    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        error = {"error": f"Configuration error: {str(e)}"}
        print(json.dumps(error, indent=2))
        return 1

    except ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        error = {"error": f"Connection error: {str(e)}", "retriable": True}
        print(json.dumps(error, indent=2))
        return 1

    except RuntimeError as e:
        logger.error(f"Service error: {str(e)}")
        error = {"error": f"Service error: {str(e)}"}
        print(json.dumps(error, indent=2))
        return 1

    except Exception as e:
        logger.exception(f"Unexpected error in Airpoints number lookup: {str(e)}")
        error = {"error": f"Unexpected error: {str(e)}"}
        print(json.dumps(error, indent=2))
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <airpoints_number>")
        sys.exit(1)

    airpoints_number = sys.argv[1]
    sys.exit(main(airpoints_number))
