# Standard imports
import unittest
import sys
import os
from datetime import datetime, timedelta
import logging

# Our imports
from emission.core.get_database import get_db, get_client_db, get_profile_db, get_uuid_db, get_pending_signup_db, get_section_db
from emission.core.wrapper.client import Client
from emission.tests import common
from emission.core.wrapper.user import User

import emission.tests.common as etc

class TestClient(unittest.TestCase):
  def setUp(self):
    # Make sure we start with a clean slate every time
    self.serverName = 'localhost'
    common.dropAllCollections(get_db())
    logging.info("After setup, client count = %d, profile count = %d, uuid count = %d" % 
      (get_client_db().find().count(), get_profile_db().count(), get_uuid_db().count()))
    common.loadTable(self.serverName, "Stage_Modes", "emission/tests/data/modes.json")
    
  def testInitClient(self):
    emptyClient = Client("testclient")
    self.assertEqual(emptyClient.clientName, "testclient")
    self.assertEqual(emptyClient.settings_filename, "conf/clients/testclient.settings.json")
    self.assertEqual(emptyClient.clientJSON, None)

  def updateWithTestSettings(self, client, fileName):
    client.settings_filename = fileName
    client.update(createKey = True)

  def testCreateClient(self):
    client = Client("testclient")
    client.update(createKey = False)

    # Reset the times in the client so that it will show as active and we will
    # get a valid set of settings    
    common.makeValid(client)
    self.assertNotEqual(client.getSettings(), None)
    self.assertNotEqual(client.getSettings(), {})

    print client.getSettings()
    self.assertNotEqual(client.getSettings()['result_url'], None)

  def testUpdateClient(self):
    client = Client("testclient")
    self.updateWithTestSettings(client, "emission/tests/coreTests/wrapperTests/testclient/testclient_settings_update.json")

if __name__ == '__main__':
    etc.configLogging()
    unittest.main()
