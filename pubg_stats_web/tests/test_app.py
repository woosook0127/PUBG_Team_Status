import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

app_under_test = None

class TestAppRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.env_patcher = patch.dict(os.environ, {'PUBG_API_KEY': 'test_api_key_from_env_patch'})
        cls.env_patcher.start()

        global app_under_test
        from pubg_stats_web.app import app as flask_app
        app_under_test = flask_app
        
        app_under_test.config['TESTING'] = True
        app_under_test.config['WTF_CSRF_ENABLED'] = False 
        app_under_test.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        os.environ['WERKZEUG_RUN_MAIN'] = 'true'

    @classmethod
    def tearDownClass(cls):
        cls.env_patcher.stop()

    def setUp(self):
        self.client = app_under_test.test_client()
        self.mock_individual_stats = {"damageDealt": 100, "kills": 1, "assists": 0.5, "survivalTime": 1800, "avgRank": 30}
        self.mock_frequent_teammates = []
        self.mock_weapon_stats = {}
        self.mock_match_logs = [] 

    @patch('pubg_stats_web.app.calculate_individual_weapon_stats')
    @patch('pubg_stats_web.app.calculate_teammate_synergy_stats')
    @patch('pubg_stats_web.app.identify_frequent_teammates')
    @patch('pubg_stats_web.app.calculate_individual_player_stats')
    @patch('pubg_stats_web.app.PubgAPI') 
    def test_player_stats_default_game_mode(self, MockPubgAPI, mock_calc_individual_stats, mock_id_teammates, mock_calc_synergy, mock_calc_weapon):
        mock_api_instance = MockPubgAPI.return_value
        mock_api_instance.get_player_id.return_value = 'account_id_test'
        mock_api_instance.get_player_season_stats.return_value = {'attributes': {'gameModeStats': {'ranked-squad': {'kills': 10}}}}
        mock_api_instance.get_player_matches.return_value = [] 
        
        mock_calc_individual_stats.return_value = self.mock_individual_stats
        mock_id_teammates.return_value = self.mock_frequent_teammates
        mock_calc_weapon.return_value = self.mock_weapon_stats
        
        response = self.client.get('/api/player_stats?playerName=test_player&seasonId=test_season')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['accountId'], 'account_id_test')
        self.assertEqual(data['individualStats'], self.mock_individual_stats)
        mock_api_instance.get_player_season_stats.assert_called_once_with('account_id_test', 'test_season', game_mode_filter="ranked-squad")

    @patch('pubg_stats_web.app.calculate_individual_weapon_stats')
    @patch('pubg_stats_web.app.calculate_teammate_synergy_stats')
    @patch('pubg_stats_web.app.identify_frequent_teammates')
    @patch('pubg_stats_web.app.calculate_individual_player_stats')
    @patch('pubg_stats_web.app.PubgAPI')
    def test_player_stats_specific_game_mode_normal_fpp(self, MockPubgAPI, mock_calc_individual_stats, mock_id_teammates, mock_calc_synergy, mock_calc_weapon):
        mock_api_instance = MockPubgAPI.return_value
        mock_api_instance.get_player_id.return_value = 'account_id_test_normal_fpp'
        mock_api_instance.get_player_season_stats.return_value = {'attributes': {'gameModeStats': {'squad-fpp': {'kills': 5}}}}
        mock_api_instance.get_player_matches.return_value = []

        expected_individual_stats = {"damageDealt": 80, "kills": 0.8, "assists": 0.3, "survivalTime": 1500, "avgRank": 40}
        mock_calc_individual_stats.return_value = expected_individual_stats
        mock_id_teammates.return_value = []
        mock_calc_weapon.return_value = {}

        response = self.client.get('/api/player_stats?playerName=test_player&seasonId=test_season&gameType=normal&perspective=fpp')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['accountId'], 'account_id_test_normal_fpp')
        self.assertEqual(data['individualStats'], expected_individual_stats)
        mock_api_instance.get_player_season_stats.assert_called_once_with('account_id_test_normal_fpp', 'test_season', game_mode_filter="squad-fpp")

    @patch('pubg_stats_web.app.PubgAPI')
    def test_player_stats_player_not_found(self, MockPubgAPI):
        mock_api_instance = MockPubgAPI.return_value
        mock_api_instance.get_player_id.return_value = None 

        response = self.client.get('/api/player_stats?playerName=unknown_player&seasonId=test_season')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Player 'unknown_player' not found or an API error occurred.")

    # Patch PubgAPI for this test to prevent the "PubgAPI service not available" 500 error
    # if the import of PubgAPI in app.py fails.
    @patch('pubg_stats_web.app.PubgAPI') 
    def test_player_stats_missing_parameters(self, MockPubgAPI): # MockPubgAPI is not used but makes patch work
        # Ensure MockPubgAPI is not None, even if it's not strictly used in this test's logic flow,
        # to bypass the `if PubgAPI is None:` check in the route.
        # If app.PubgAPI was None due to import error, this patch replaces it with a MagicMock.
        
        response_no_player = self.client.get('/api/player_stats?seasonId=test_season')
        self.assertEqual(response_no_player.status_code, 400)
        data_no_player = json.loads(response_no_player.data)
        self.assertIn('error', data_no_player)
        self.assertEqual(data_no_player['error'], 'playerName parameter is required.')

        response_no_season = self.client.get('/api/player_stats?playerName=test_player')
        self.assertEqual(response_no_season.status_code, 400)
        data_no_season = json.loads(response_no_season.data)
        self.assertIn('error', data_no_season)
        self.assertEqual(data_no_season['error'], 'seasonId parameter is required.')

    @patch('pubg_stats_web.app.calculate_individual_player_stats') 
    @patch('pubg_stats_web.app.PubgAPI')
    def test_player_stats_season_data_not_found(self, MockPubgAPI, mock_calc_individual_stats):
        mock_api_instance = MockPubgAPI.return_value
        mock_api_instance.get_player_id.return_value = 'account_id_test'
        mock_api_instance.get_player_season_stats.return_value = None 
        mock_api_instance.get_player_matches.return_value = []

        response = self.client.get('/api/player_stats?playerName=test_player&seasonId=non_existent_season')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Could not fetch season stats for this player. The account may be invalid or there's no data for the selected season/game mode.")
        mock_calc_individual_stats.assert_not_called() 

if __name__ == '__main__':
    unittest.main()
