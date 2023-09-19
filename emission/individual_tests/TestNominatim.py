from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
import unittest
import unittest.mock as mock
# import overpy
import os
from emission.core.wrapper.trip_old import Coordinate
import requests
import emission.core.wrapper.entry as ecwe
import emission.core.wrapper.wrapperbase as ecww
import emission.net.ext_service.geocoder.nominatim as eco
import emission.analysis.intake.cleaning.clean_and_resample as clean

print("Starting to test Nominatim")
print("keys", os.environ.keys())
#temporarily sets NOMINATIM_QUERY_URL to the environment variable for testing.
NOMINATIM_QUERY_URL_env = os.environ.get("NOMINATIM_QUERY_URL", "")
NOMINATIM_QUERY_URL = NOMINATIM_QUERY_URL_env if NOMINATIM_QUERY_URL_env != "" else eco.NOMINATIM_QUERY_URL
GEOFABRIK_QUERY_URL = os.environ.get("GEOFABRIK_QUERY_URL")
TEST_ENVVAR = os.environ.get("TEST_ENVVAR")
TEST_KEY = os.environ.get("TEST_KEY")
TEST_STR = os.environ.get("TEST_STR")
print("Test str w envvar", TEST_ENVVAR)
print("Test key", TEST_KEY)
print("TESTSTRING", TEST_STR)
#Creates a fake place in Rhode Island to use for testing.
fake_id = "rhodeislander"
key = "segmentation/raw_place"
write_ts = 1694344333
data = {'source': 'FakeTripGenerator','location': {'type': 'Point', 'coordinates': [-71.4128343, 41.8239891]}}
fake_place = ecwe.Entry.create_fake_entry(fake_id, key, data, write_ts)

class NominatimTest(unittest.TestCase):
    maxDiff = None

    #basic query to check that both nominatim and geofabrik are acting as drop-ins for eachother.
    def test_geofabrik_and_nominatim(self):
        nominatim_result =  requests.get(NOMINATIM_QUERY_URL + "/reverse?lat=41.8239891&lon=-71.4128343&format=json")
        geofabrik_result =  requests.get(GEOFABRIK_QUERY_URL + "/reverse?lat=41.8239891&lon=-71.4128343&format=json")
        self.assertEqual(nominatim_result, geofabrik_result)

#checks the display name generated by get_filtered place in clean_and_resample.py, which creates a cleaned place from the fake place
# and reverse geocodes with the coordinates.
    def test_get_filtered_place(self):
        raw_result = ecww.WrapperBase.__getattr__(clean.get_filtered_place(fake_place), "data")
        print(NOMINATIM_QUERY_URL)
        actual_result = ecww.WrapperBase.__getattr__(raw_result, "display_name")
        expected_result = "Dorrance Street, Providence"
        self.assertEqual(expected_result, actual_result)

    def test_make_url_geo(self):
        expected_result = NOMINATIM_QUERY_URL + "/search?q=Providence%2C+Rhode+Island&format=json"
        actual_result = eco.Geocoder.make_url_geo("Providence, Rhode Island")
        self.assertEqual(expected_result, actual_result)

    #we ignore the place_id because it is an internal Nominatim identifier 
    def test_get_json_geo(self):
        expected_result = "Hartford Pike"
        actual_result = eco.Geocoder.get_json_geo("Old Hartford Pike, Scituate, RI 02857")[0]["name"]
        self.assertEqual(expected_result, actual_result)

    def test_geocode(self):
        expected_result_lon = Coordinate(41.8239891, -71.4128343).get_lon()
        expected_result_lat = Coordinate(41.8239891, -71.4128343).get_lat()
        actual_result = eco.Geocoder.geocode("Providence, Rhode Island")
        actual_result_lon = actual_result.get_lon()
        actual_result_lat = actual_result.get_lat()
        self.assertEqual(expected_result_lon, actual_result_lon)
        self.assertEqual(expected_result_lat, actual_result_lat)


    def test_make_url_reverse(self):
        expected_result = NOMINATIM_QUERY_URL + "/reverse?lat=41.8239891&lon=-71.4128343&format=json"
        actual_result = (eco.Geocoder.make_url_reverse(41.8239891, -71.4128343))
        self.assertEqual(expected_result, actual_result)
 
        #tested result was modified to only look at the name returned with the coordinates, rather than the entire dictionary.
    def test_get_json_reverse(self):
        expected_result = "Providence City Hall"
        actual_result = eco.Geocoder.get_json_reverse(41.8239891, -71.4128343)["display_name"].split(",")[0]
        self.assertEqual(expected_result, actual_result)

    def test_reverse_geocode(self):
        expected_result = "Portugal Parkway, Fox Point, Providence, Providence County, 02906, United States"
        actual_result = eco.Geocoder.reverse_geocode(41.8174476, -71.3903767)
        self.assertEqual(expected_result, actual_result)

    #a hard-coded nominatim call to compare with our container. 
    def test_nominatim_api(self):
        nominatim_url = "http://nominatim.openstreetmap.org/reverse?lat=41.832942092439694&lon=-71.41558148857203&format=json"
        nominatim_result_raw = requests.get(nominatim_url)
        nominatim_result = nominatim_result_raw.json()['display_name']
        # NOMINATIM_QUERY_URL = eco.NOMINATIM_QUERY_URL
        docker_result = eco.Geocoder.reverse_geocode(41.832942092439694, -71.41558148857203)
        print(docker_result)
        print(nominatim_result)
        self.assertEqual(nominatim_result, docker_result)

    # def test_overpass_api(self):
    #     api = overpy.Overpass()
    #     result = api.query("""way["name"="Gielgenstraße"](50.7,7.1,50.8,7.25);out;""")
        

if __name__ == '__main__':
    unittest.main()