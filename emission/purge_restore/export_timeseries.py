import logging
logging.basicConfig(level=logging.DEBUG)
import gzip
import os 
import copy

import uuid
import json
import emission.storage.json_wrappers as esj
import emission.storage.timeseries.timequery as estt
import emission.storage.timeseries.abstract_timeseries as esta
import emission.storage.timeseries.cache_series as estcs
import emission.net.usercache.abstract_usercache as enua

def get_with_retry(retrieve_call, in_query):
    # Let's clone the query since we are going to modify it
    query = copy.copy(in_query)
    # converts "data.ts" = ["data", "ts"]
    timeTypeSplit = query.timeType.split(".")
    list_so_far = []
    done = False
    while not done:
        # if we don't sort this here, we simply concatenate the entries in the
        # two timeseries and analysis databases so we could end up with a later
        # timestamp from the analysis database as opposed to the timeseries
        (curr_count, curr_batch_cursor) = retrieve_call(query)
        # If this is the first call (as identified by `len(list_so_far) == 0`
        # the count is the total count
        total_count = curr_count if len(list_so_far) == 0 else total_count
        curr_batch = list(curr_batch_cursor)
        if len(list_so_far) > 0 and len(curr_batch) > 0 and curr_batch[0]["_id"] == list_so_far[-1]["_id"]:
            logging.debug(f"first entry {curr_batch[0]['_id']} == last entry so far {list_so_far[-1]['_id']}, deleting")
            del curr_batch[0]
        list_so_far.extend(curr_batch)
        logging.debug(f"Retrieved batch of size {len(curr_batch)}, cumulative {len(list_so_far)} entries of total {total_count} documents for {query}")
        if len(list_so_far) >= total_count:
            done = True
        else:
            query.startTs = curr_batch[-1][timeTypeSplit[0]][timeTypeSplit[1]]

    return list_so_far[:501]

def get_from_all_three_sources_with_retry(user_id, in_query, databases=None):
    import emission.storage.timeseries.builtin_timeseries as estb

    ts = estb.BuiltinTimeSeries(user_id)

    sort_key = ts._get_sort_key(in_query)
    source_db_calls = []

    logging.info("In get_from_all_three_sources_with_retry: Databases = %s" % databases)

    if databases is None or 'timeseries_db' in databases:
        logging.info("Fetching from timeseries_db")
        base_ts_call = lambda tq: ts._get_entries_for_timeseries(ts.timeseries_db, None, tq,
            geo_query=None, extra_query_list=None, sort_key = sort_key)
        source_db_calls.append(base_ts_call)

    retry_lists = []
    for source_db_call in source_db_calls:
        retry_lists = retry_lists + get_with_retry(source_db_call, in_query)

    return retry_lists

def export(user_id, ts, start_ts, end_ts, file_name, databases=None):
    logging.info("In export: Databases = %s" % databases)
    print("In export: Databases = %s" % databases)

    logging.info("Extracting timeline for user %s day %s -> %s and saving to file %s" %
                 (user_id, start_ts, end_ts, file_name))
    print("Extracting timeline for user %s day %s -> %s and saving to file %s" %
                 (user_id, start_ts, end_ts, file_name))

    loc_time_query = estt.TimeQuery("data.ts", start_ts, end_ts)
    loc_entry_list = get_from_all_three_sources_with_retry(user_id, loc_time_query, databases)
    # trip_time_query = estt.TimeQuery("data.start_ts", start_ts, end_ts)
    # trip_entry_list = get_from_all_three_sources_with_retry(user_id, trip_time_query, databases)
    # place_time_query = estt.TimeQuery("data.enter_ts", start_ts, end_ts)
    # place_entry_list = get_from_all_three_sources_with_retry(user_id, place_time_query, databases)
    
    # combined_list = loc_entry_list + trip_entry_list + place_entry_list 
    combined_list = loc_entry_list 
    # logging.info("Found %d loc-like entries, %d trip-like entries, %d place-like entries = %d total entries" %
        # (len(loc_entry_list), len(trip_entry_list), len(place_entry_list), len(combined_list)))
    logging.info("Found %d loc-like entries = %d total entries" %
        (len(loc_entry_list), len(combined_list)))

    validate_truncation(loc_entry_list)
    # validate_truncation(loc_entry_list, trip_entry_list, place_entry_list)

    unique_key_list = set([e["metadata"]["key"] for e in combined_list])
    logging.info("timeline has unique keys = %s" % unique_key_list)
    if len(combined_list) == 0 or unique_key_list == set(['stats/pipeline_time']):
        logging.info("No entries found in range for user %s, skipping save" % user_id)
        print("No entries found in range for user %s, skipping save" % user_id)
        print("Combined list length = %d" % len(combined_list))
        print("Unique key list = %s" % unique_key_list)
        return None
    else:
        combined_filename = "%s.gz" % (file_name)
        logging.info("Combined list:")
        logging.info(len(combined_list))
        with gzip.open(combined_filename, "wt") as gcfd:
            json.dump(combined_list,
                gcfd, default=esj.wrapped_default, allow_nan=False, indent=4)
            
        # Returning these queries that were used to fetch the data entries that were exported.
        # Need these for use in the purge_user_timeseries.py script so that we only delete those entries that were exported
        return {
            # 'trip_time_query': trip_time_query,
            # 'place_time_query': place_time_query,
            'loc_time_query': loc_time_query
        }


# def validate_truncation(loc_entry_list, trip_entry_list, place_entry_list):
def validate_truncation(loc_entry_list):
    MAX_LIMIT = 25 * 10000
    if len(loc_entry_list) == MAX_LIMIT:
        logging.warning("loc_entry_list length = %d, probably truncated" % len(loc_entry_list))
    # if len(trip_entry_list) == MAX_LIMIT:
    #     logging.warning("trip_entry_list length = %d, probably truncated" % len(trip_entry_list))
    # if len(place_entry_list) == MAX_LIMIT:
    #     logging.warning("place_entry_list length = %d, probably truncated" % len(place_entry_list))
