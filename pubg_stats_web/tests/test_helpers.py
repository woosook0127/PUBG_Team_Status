import unittest
import sys
import os

# Adjust the Python path to include the project root directory
# This allows us to import modules from pubg_stats_web
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pubg_stats_web.utils.helpers import calculate_individual_player_stats

class TestCalculateIndividualPlayerStats(unittest.TestCase):

    def test_single_game_mode(self):
        mock_season_data_single_mode = {
            "attributes": {
                "gameModeStats": {
                    "ranked-squad": {
                        "damageDealt": 1000.0, "kills": 10, "assists": 5,
                        "timeSurvived": 18000.0, # 300 mins / 10 rounds = 30 min/round = 1800s/round
                        "wins": 1, "top10s": 5, "roundsPlayed": 10
                    }
                }
            }
        }
        expected_stats = {
            "damageDealt": 100.0, # 1000 / 10
            "kills": 1.0,       # 10 / 10
            "assists": 0.5,     # 5 / 10
            "survivalTime": 1800.0, # 18000 / 10
            # avgRank: ((wins/rounds)*50 + (top10s/rounds)*50)
            # ( (1/10)*50 + (5/10)*50 ) = (0.1*50 + 0.5*50) = 5 + 25 = 30
            "avgRank": 30.0
        }
        result = calculate_individual_player_stats(mock_season_data_single_mode)
        self.assertIsNotNone(result)
        for key, value in expected_stats.items():
            self.assertAlmostEqual(result[key], value, places=2, msg=f"Stat {key} did not match")

    def test_multiple_game_modes(self):
        mock_season_data_multi_mode = {
            "attributes": {
                "gameModeStats": {
                    "squad": { # Rounds: 10
                        "damageDealt": 1000.0, "kills": 10, "assists": 5,
                        "timeSurvived": 18000.0, "wins": 1, "top10s": 5, "roundsPlayed": 10
                    },
                    "squad-fpp": { # Rounds: 5
                        "damageDealt": 500.0, "kills": 5, "assists": 2,
                        "timeSurvived": 9000.0, "wins": 0, "top10s": 2, "roundsPlayed": 5
                    }
                }
            }
        }
        # Total rounds = 15
        # Total damage = 1500.0 -> avg = 100.0
        # Total kills = 15 -> avg = 1.0
        # Total assists = 7 -> avg = 0.4666...
        # Total time survived = 27000.0 -> avg = 1800.0
        # Rank score squad: ((1/10)*50 + (5/10)*50) = 5 + 25 = 30
        # Rank score squad-fpp: ((0/5)*50 + (2/5)*50) = 0 + 20 = 20
        # total_rank_points_equivalent = (30 * 10) + (20 * 5) = 300 + 100 = 400
        # avgRank = 400 / 15 = 26.666...
        expected_stats = {
            "damageDealt": 100.0,
            "kills": 1.0,
            "assists": 7 / 15,
            "survivalTime": 1800.0,
            "avgRank": 400 / 15
        }
        result = calculate_individual_player_stats(mock_season_data_multi_mode)
        self.assertIsNotNone(result)
        for key, value in expected_stats.items():
            self.assertAlmostEqual(result[key], value, places=2, msg=f"Stat {key} did not match")

    def test_empty_or_invalid_data(self):
        self.assertIsNone(calculate_individual_player_stats(None), "Test with None failed")
        self.assertIsNone(calculate_individual_player_stats({}), "Test with empty dict failed")
        self.assertIsNone(calculate_individual_player_stats({"attributes": {}}), "Test with missing gameModeStats failed")
        self.assertIsNone(calculate_individual_player_stats({"attributes": {"gameModeStats": {}}}), "Test with empty gameModeStats failed")

    def test_mode_with_zero_rounds_played(self):
        mock_data = {
            "attributes": {
                "gameModeStats": {
                    "ranked-squad": { # This mode should be counted
                        "damageDealt": 1000.0, "kills": 10, "assists": 5,
                        "timeSurvived": 18000.0, "wins": 1, "top10s": 5, "roundsPlayed": 10
                    },
                    "solo": { # This mode should be skipped
                        "damageDealt": 200.0, "kills": 2, "assists": 1,
                        "timeSurvived": 3600.0, "wins": 0, "top10s": 0, "roundsPlayed": 0
                    }
                }
            }
        }
        # Expected stats should be the same as test_single_game_mode
        expected_stats = {
            "damageDealt": 100.0,
            "kills": 1.0,
            "assists": 0.5,
            "survivalTime": 1800.0,
            "avgRank": 30.0
        }
        result = calculate_individual_player_stats(mock_data)
        self.assertIsNotNone(result)
        for key, value in expected_stats.items():
            self.assertAlmostEqual(result[key], value, places=2, msg=f"Stat {key} did not match")

    def test_all_modes_zero_rounds_played(self):
        mock_data = {
            "attributes": {
                "gameModeStats": {
                    "ranked-squad": {
                        "damageDealt": 1000.0, "kills": 10, "assists": 5,
                        "timeSurvived": 18000.0, "wins": 1, "top10s": 5, "roundsPlayed": 0
                    },
                    "solo": {
                        "damageDealt": 200.0, "kills": 2, "assists": 1,
                        "timeSurvived": 3600.0, "wins": 0, "top10s": 0, "roundsPlayed": 0
                    }
                }
            }
        }
        self.assertIsNone(calculate_individual_player_stats(mock_data), "Test with all modes zero rounds failed")


if __name__ == '__main__':
    unittest.main()
