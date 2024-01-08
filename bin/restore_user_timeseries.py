import logging
import argparse
import uuid
from datetime import datetime
import emission.core.wrapper.user as ecwu
import emission.core.get_database as edb
import emission.core.wrapper.pipelinestate as ecwp
import emission.core.wrapper.pipelinestate as ecwp
import emission.storage.pipeline_queries as esp
import pandas as pd
import pymongo
from bson import ObjectId
import json

def restoreUserTimeseries(filename):
    # df = pd.read_csv(filename)
    # df['_id'] = df['_id'].apply(lambda x: ObjectId(x))
    # data = df.to_dict(orient='records')
    # print(df)
    # result = edb.get_timeseries_db().insert_many(data)

    with open(filename, 'r') as file:
        data = json.load(file)
    result = edb.get_timeseries_db().insert_many(data)

    logging.info("{} documents successfully inserted".format(len(result.inserted_ids)))
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(prog="restore_user_timeseries")
    parser.add_argument(
        "-f", "--file_name", 
        help="Path to the CSV file containing data to be imported"
    )

    args = parser.parse_args()
    restoreUserTimeseries(args.file_name)