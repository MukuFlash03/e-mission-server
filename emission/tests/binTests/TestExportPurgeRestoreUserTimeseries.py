from future import standard_library
standard_library.install_aliases()
from builtins import *
import os
import json
import logging
import tempfile
import unittest
from pymongo import errors

import emission.tests.common as etc
import emission.core.get_database as edb
import emission.storage.pipeline_queries as esp
import emission.core.wrapper.pipelinestate as ecwp
import bin.purge_user_timeseries as bput
import bin.restore_user_timeseries as brut
import bin.debug.load_multi_timeline_for_range as lmtfr

class TestPurgeRestoreUserTimeseries(unittest.TestCase):
    def setUp(self):
        etc.setupRealExample(self, "emission/tests/data/real_examples/shankari_2015-07-22")
        etc.runIntakePipeline(self.testUUID)

    def tearDown(self):
        etc.dropAllCollections(edb._get_current_db())

    def testExportPurgeRestoreUserTimeseries(self):
        # with tempfile.TemporaryDirectory() as tmpdirname:
        #     logging.info(f"Default temporary directory: {tempfile.gettempdir()}")
        #     # cstate = esp.get_current_state(self.testUUID, ecwp.PipelineStages.CREATE_CONFIRMED_OBJECTS)
        #     # last_ts_run = cstate['last_ts_run']
        #     # self.assertTrue(last_ts_run > 0)
            
        # Run the purge function
        tmpdirname = "/Users/mmahadik/Documents/Work/OpenPATH/Code/GitHub/logs/data/export_purge_restore/purge/tests"
        
        # Without running intake pipeline, for both usercache and analysis, no entries exported, export file not created since no data in usercache
        # With intake pipeline, can see same 3 analysis key entries: 'analysis/cleaned_place', 'segmentation/raw_place', 'analysis/confirmed_place'
        # export_databases = ['usercache_db'] 
        # export_databases = ['analysis_timeseries_db'] 
        export_databases = ['timeseries_db'] 
        export_file_name = bput.purgeUserTimeseries(str(self.testUUID), databases=export_databases, dir_name=tmpdirname)
        export_file_name += ".gz"

        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("file_prefix", help="the name of the file or file prefix that contains the json representation of the timeline")
        args = parser.parse_args(["--file_prefix", export_file_name])
        print("In TestExportPurgeRestoreUserTimeseries: export_file_name: ", export_file_name)
        lmtfr.load_multi_timeline_for_range(args)


           
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    etc.configLogging()
    unittest.main()