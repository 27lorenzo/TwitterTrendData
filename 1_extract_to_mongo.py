from pymongo import MongoClient
import argparse
import config
import json
import logging

client = None
database = "projects"


def create_client(mongo_server):
    global client
    if not client:
        client = MongoClient(host=[mongo_server])


def log(verbose, s):
    if verbose:
        print(s)


def load_data(filename, verbose=False):
    try:
        db = client[database]
        collection = db[filename]
        json_file = filename + ".json"

        data = []
        with open(json_file, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    json_data = json.loads(line)
                    data.append(json_data)
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON in line: {line}")

        collection.insert_many(data)
    except Exception as e:
        logging.error(f"Error loading data: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description='Fetch the latest changes for a dataset.')
    parser.add_argument('filename', metavar='NAME', type=str, default='', help='The name of the filename to insert')
    parser.add_argument('-verbose', '-v', dest='verbose', action='store_true', default=False)
    return parser.parse_args()


def main():
    try:
        create_client(mongo_server)
        args = parse_args()
        load_data(**vars(args))
    finally:
        if client:
            client.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    c = config.config()
    mongo_server = c.readh('mongodb', 'server') or 'localhost'
    main()
