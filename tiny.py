#!/usr/bin/env python3

import argparse
import json
import logging
import math
import os
import sys
import time

LOG_FORMAT = "[%(asctime)s] [%(levelname)s]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
VALID_FIELDS = ["bannerUrl", "category", "description", "developer", "frontBoxArt", "iconUrl", "id", "intro", "isDemo", "key", "language", "languages", "name", "nsuId",
                "numberOfPlayers", "publisher", "rank", "rating", "ratingContent", "region", "regions", "releaseDate", "rightsId", "screenshots", "size", "version"]

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)


def parse_args() -> argparse.Namespace:
    """Parse the arguments passed to the script

    Returns:
        argparse.Namespace: Object containing output_file, input_file and fields arguments
    """
    parser = argparse.ArgumentParser(description="Reduce the size of the titleDB JSON file by removing entries without a name and only keeping the specified fields.")
    parser.add_argument("input_file", help="The JSON file to process")  # required argument
    parser.add_argument("-o", "--output_file", help="The file to output_file to. Defaults to the input file if not provided")  # optional arguments
    parser.add_argument("-f", "--fields", nargs="*", help="List of fields to keep in the output_file, defaults to all fields. Separate fields with a space e.g -f name description rating")
    return parser.parse_args()


def validate_fields(fields: list):
    """Validate the fields provided in the fields argument

    Ensures that all each field provided is a valid field

    Args:
        fields (list): List of fields to validate
    """
    if fields and not all(field in VALID_FIELDS for field in fields):
        # if any of the fields are not valid, log an error and exit
        invalid_fields = ', '.join(set(fields) - set(VALID_FIELDS))
        logging.error(f"Invalid field [{invalid_fields}]. Valid fields are {', '.join(VALID_FIELDS)}")
        sys.exit(1)


def read_json_file(file_path: str) -> dict | None:
    """Read the contents of a JSON file and return it as a dictionary

    Args:
        file_path (str): path to the file to read

    Returns:
        dict | None: returns contents of the file as a dictionary or None if failed to read the file
    """
    if not os.path.exists(file_path):
        # if the file does not exist, log an error and exit
        logging.error(f"File {file_path} does not exist")
        sys.exit(1)

    try:
        # read the file and return the data
        with open(file_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # if the file is not a valid JSON file, log an error and exit
        logging.error(f"{file_path} is not a valid JSON file. {e}")
        sys.exit(1)


def write_to_file(output_file: str, new_data: dict) -> None:
    """Write a dictionary to a file as JSON

    Args:
        output_file (str): path to the file to write to
        new_data (dict): data to write to the file
    """
    try:
        # write the new data to the output_file file
        with open(output_file, "w") as f:
            json.dump(new_data, f, separators=(",", ":"))  # use separators to remove whitespaces
    except Exception as e:
        # if there is an error writing to the output_file file, log an error and exit
        logging.error(f"Error writing to {output_file}. {e}")
        sys.exit(1)


def trim_titledb(data: dict, fields: list) -> dict:
    """Trim titledb by removing entries without a name and only keeping the fields in the fields list

    Args:
        data (dict): title data to reduce
        fields (list): fields to keep in the output_file

    Returns:
        dict: reduced title data
    """
    new_data = {}  # new dictionary to store the reduced data
    for count, (title_id, title_data) in enumerate(data.items(), start=1):
        if title_data.get("name"):  # only include titles with a name
            # only include the fields that are in the fields list or all fields if fields not provided
            new_data[title_id] = {field: title_data[field] for field in (fields or title_data) if field in title_data}

        # log progress every 10% or when the count reaches the length of the data
        if count % (((len(data) // 10)) if len(data) > 10 else 1) == 0 or count == len(data):
            logging.info(f"Progress: {int(math.floor(count/len(data)*100))}% - {count}/{len(data)}")
    return new_data  # return the reduced data


if __name__ == "__main__":
    start_time = time.perf_counter()
    logging.info("[START] tiny.py started")

    # parse the arguments
    args = parse_args()

    # get the input_file file, output_file file and fields from the arguments
    titledb_path = args.input_file
    output_file = args.input_file if args.output_file is None else args.output_file
    fields = VALID_FIELDS if args.fields is None else args.fields

    # ensure the given fields are valid
    validate_fields(fields)

    # read the data from the input_file file
    logging.info(f"Starting tiny.py with input file: {titledb_path}, output_file file: {output_file}, fields: {"All" if fields == VALID_FIELDS else fields}")
    logging.info(f"Reading from {titledb_path}")
    data = read_json_file(titledb_path)

    start_size = os.path.getsize(titledb_path)
    logging.info(f"Read {len(data)} titles from {titledb_path} ({start_size/1024/1024:.1f} MB)")

    # trim the data
    new_data = trim_titledb(data, fields)

    # write the new data to the output_file file
    logging.info(f"Writing {len(new_data)} titles to {output_file}")
    write_to_file(output_file, new_data)

    logging.info(f"tiny.py completed in {(time.perf_counter() - start_time):.4f} seconds and reduced the file size by {(((start_size - os.path.getsize(output_file)) / start_size) * 100):.1f}% from {
                 (start_size/1024/1024):.1f} MB to {(os.path.getsize(output_file)/1024/1024):.1f} MB.")
    logging.info("[END] tiny.py completed")
