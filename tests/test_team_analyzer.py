import pytest
from unittest.mock import AsyncMock, MagicMock # For mocking the pubg_api_module

from app.team_analyzer import identify_player_team, NUM_MATCHES_TO_ANALYZE, MIN_GAMES_FOR_FREQUENT_TEAM, MIN_CLAN_GAMES_THRESHOLD
from app.exceptions import APIError # For simulating API errors

# --- Mock PUBG API Module ---
class MockPubgApiModule:
    def __init__(self):
        self.get_player_clan_details = AsyncMock()
        self.get_player_match_history_ids = AsyncMock()
        self.get_match_details = AsyncMock()

    def reset_mocks(self):
        self.get_player_clan_details.reset_mock()
        self.get_player_match_history_ids.reset_mock()
        self.get_match_details.reset_mock()

    # Helper to set up default successful responses (can be overridden per test)
    def setup_default_responses(self, player_id="player1", clan_id=None, clan_members=None, match_ids=None, match_details_map=None):
        if clan_id and clan_members:
            self.get_player_clan_details.return_value = {
                "data": {"id": clan_id, "type": "clan", "attributes": {"name": "Test Clan"},
                         "relationships": {"members": {"data": [{"id": member_id} for member_id in clan_members]}}}
            }
        else:
            # Simulate "not in clan" by raising the specific exception pubg_api.py would raise
            from app.exceptions import ClanNotFoundAPIError
            self.get_player_clan_details.side_effect = ClanNotFoundAPIError(player_id, "steam", by_player=True)
            
        self.get_player_match_history_ids.return_value = match_ids if match_ids is not None else [f"match{i}" for i in range(NUM_MATCHES_TO_ANALYZE)]
        
        if match_details_map:
            # Make get_match_details return specific details based on match_id
            async def side_effect_get_match_details(match_id, platform_shard):
                return match_details_map.get(match_id, {}) # Default to empty if not in map
            self.get_match_details.side_effect = side_effect_get_match_details
        else: # Default simple match detail
            self.get_match_details.return_value = {"data": {"id": "match_default"}, "included": []}


@pytest.fixture
def mock_pubg_api():
    return MockPubgApiModule()

# --- Test Scenarios ---

@pytest.mark.asyncio
async def test_player_in_clan_clan_plays_frequently(mock_pubg_api):
    player_id = "player_clan_freq"
    clan_id = "clan1"
    clan_members = [player_id, "clan_mate1", "clan_mate2"]
    num_matches = NUM_MATCHES_TO_ANALYZE # e.g., 20
    
    match_ids = [f"match_clan_game_{i}" for i in range(num_matches)]
    match_details_map = {}
    for i, match_id in enumerate(match_ids):
        # All matches are with the full clan
        participants = [
            {"type": "participant", "id": f"p_main_{i}", "attributes": {"stats": {"playerId": player_id}}},
            {"type": "participant", "id": f"p_cm1_{i}", "attributes": {"stats": {"playerId": "clan_mate1"}}},
            {"type": "participant", "id": f"p_cm2_{i}", "attributes": {"stats": {"playerId": "clan_mate2"}}},
        ]
        roster = {"type": "roster", "id": f"r_{i}", "relationships": {"participants": {"data": [
            {"id": f"p_main_{i}"}, {"id": f"p_cm1_{i}"}, {"id": f"p_cm2_{i}"}
        ]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}

    mock_pubg_api.setup_default_responses(
        player_id=player_id, clan_id=clan_id, clan_members=clan_members, 
        match_ids=match_ids, match_details_map=match_details_map
    )

    team, msg, processed_matches = await identify_player_team(player_id, "steam", mock_pubg_api)
    
    assert team is not None
    assert sorted(team) == sorted(clan_members)
    assert "identified by clan membership" in msg.lower()
    assert len(processed_matches) == num_matches
    # clan_team_play_frequency should be num_matches, which is >= MIN_CLAN_GAMES_THRESHOLD (3)
    # most_frequent_squad_play_frequency will also be num_matches, for the clan squad.
    # Clan wins on tie.

@pytest.mark.asyncio
async def test_player_not_in_clan_frequent_squad(mock_pubg_api):
    player_id = "player_squad_freq"
    squad_mates = ["friend1", "friend2"]
    full_squad = [player_id] + squad_mates
    num_matches = NUM_MATCHES_TO_ANALYZE # 20
    
    match_ids = [f"match_squad_game_{i}" for i in range(num_matches)]
    match_details_map = {}
    for i, match_id in enumerate(match_ids):
        # All matches are with the frequent squad
        participants = [
            {"type": "participant", "id": f"p_main_{i}", "attributes": {"stats": {"playerId": player_id}}},
            {"type": "participant", "id": f"p_f1_{i}", "attributes": {"stats": {"playerId": "friend1"}}},
            {"type": "participant", "id": f"p_f2_{i}", "attributes": {"stats": {"playerId": "friend2"}}},
        ]
        roster = {"type": "roster", "id": f"r_{i}", "relationships": {"participants": {"data": [
            {"id": f"p_main_{i}"}, {"id": f"p_f1_{i}"}, {"id": f"p_f2_{i}"}
        ]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}

    mock_pubg_api.setup_default_responses( # Player not in clan (clan_id=None)
        player_id=player_id, match_ids=match_ids, match_details_map=match_details_map
    )

    team, msg, processed_matches = await identify_player_team(player_id, "steam", mock_pubg_api)
    
    assert team is not None
    assert sorted(team) == sorted(full_squad)
    assert "identified by frequent squad" in msg.lower()
    assert len(processed_matches) == num_matches
    # most_frequent_squad_play_frequency = num_matches >= MIN_GAMES_FOR_FREQUENT_TEAM (3)
    # clan_team_play_frequency = 0

@pytest.mark.asyncio
async def test_player_in_clan_but_squad_plays_more(mock_pubg_api):
    player_id = "player_mixed_teams"
    clan_id = "clan_less_freq"
    clan_members = [player_id, "clan_mate_ infrequent"]
    squad_mates = ["friend_super_freq1", "friend_super_freq2"]
    frequent_squad_full = [player_id] + squad_mates

    # Total 20 matches (NUM_MATCHES_TO_ANALYZE)
    # 5 games with clan, 15 games with frequent squad
    clan_game_count = MIN_CLAN_GAMES_THRESHOLD + 2 # e.g. 5, meets threshold
    squad_game_count = NUM_MATCHES_TO_ANALYZE - clan_game_count # e.g. 15, also meets threshold and is higher

    match_ids = []
    match_details_map = {}

    # Clan games
    for i in range(clan_game_count):
        match_id = f"match_clan_{i}"
        match_ids.append(match_id)
        participants = [
            {"type": "participant", "id": f"p_main_c{i}", "attributes": {"stats": {"playerId": player_id}}},
            {"type": "participant", "id": f"p_cm_c{i}", "attributes": {"stats": {"playerId": clan_members[1]}}},
        ]
        roster = {"type": "roster", "id": f"rc_{i}", "relationships": {"participants": {"data": [
            {"id": f"p_main_c{i}"}, {"id": f"p_cm_c{i}"}
        ]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}

    # Frequent squad games
    for i in range(squad_game_count):
        match_id = f"match_squad_{i}"
        match_ids.append(match_id)
        participants = [
            {"type": "participant", "id": f"p_main_s{i}", "attributes": {"stats": {"playerId": player_id}}},
            {"type": "participant", "id": f"p_f1_s{i}", "attributes": {"stats": {"playerId": squad_mates[0]}}},
            {"type": "participant", "id": f"p_f2_s{i}", "attributes": {"stats": {"playerId": squad_mates[1]}}},
        ]
        roster = {"type": "roster", "id": f"rs_{i}", "relationships": {"participants": {"data": [
            {"id": f"p_main_s{i}"}, {"id": f"p_f1_s{i}"}, {"id": f"p_f2_s{i}"}
        ]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}
    
    mock_pubg_api.setup_default_responses(
        player_id=player_id, clan_id=clan_id, clan_members=clan_members,
        match_ids=match_ids, match_details_map=match_details_map
    )

    team, msg, processed_matches = await identify_player_team(player_id, "steam", mock_pubg_api)

    assert team is not None
    assert sorted(team) == sorted(frequent_squad_full) # Frequent squad should win
    assert "identified by frequent squad" in msg.lower()
    assert f"({squad_game_count}/{NUM_MATCHES_TO_ANALYZE}" in msg # Check frequency in message
    assert len(processed_matches) == NUM_MATCHES_TO_ANALYZE


@pytest.mark.asyncio
async def test_no_consistent_team_found(mock_pubg_api):
    player_id = "player_solo_random"
    num_matches = NUM_MATCHES_TO_ANALYZE
    
    match_ids = [f"match_random_{i}" for i in range(num_matches)]
    match_details_map = {}
    for i, match_id in enumerate(match_ids):
        # Each match with a different random player, so no squad meets MIN_GAMES_FOR_FREQUENT_TEAM (3)
        participants = [
            {"type": "participant", "id": f"p_main_{i}", "attributes": {"stats": {"playerId": player_id}}},
            {"type": "participant", "id": f"p_rand_{i}", "attributes": {"stats": {"playerId": f"random_player_{i}"}}},
        ]
        roster = {"type": "roster", "id": f"r_{i}", "relationships": {"participants": {"data": [
            {"id": f"p_main_{i}"}, {"id": f"p_rand_{i}"}
        ]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}

    mock_pubg_api.setup_default_responses( # Player not in clan
        player_id=player_id, match_ids=match_ids, match_details_map=match_details_map
    )

    team, msg, processed_matches = await identify_player_team(player_id, "steam", mock_pubg_api)
    
    assert team is None
    assert "no consistent team identified" in msg.lower()
    assert len(processed_matches) == num_matches

@pytest.mark.asyncio
async def test_no_match_history(mock_pubg_api):
    player_id = "player_no_matches"
    mock_pubg_api.setup_default_responses(player_id=player_id, match_ids=[]) # No matches
    
    team, msg, processed_matches = await identify_player_team(player_id, "steam", mock_pubg_api)
    
    assert team is None
    assert "no match history found" in msg.lower()
    assert len(processed_matches) == 0

@pytest.mark.asyncio
async def test_match_history_fetch_error(mock_pubg_api):
    player_id = "player_match_fetch_error"
    mock_pubg_api.get_player_match_history_ids.side_effect = APIError("Failed to fetch history", 500)
    # Clan details will still be fetched first
    mock_pubg_api.setup_default_responses(player_id=player_id) # Not in clan by default setup

    team, msg, processed_matches = await identify_player_team(player_id, "steam", mock_pubg_api)

    assert team is None
    assert "error fetching match history" in msg.lower()
    assert len(processed_matches) == 0

@pytest.mark.asyncio
async def test_match_detail_fetch_error_some_matches(mock_pubg_api):
    player_id = "player_partial_match_data"
    num_ok_matches = MIN_GAMES_FOR_FREQUENT_TEAM # e.g. 3
    num_err_matches = 2
    total_matches_in_history = num_ok_matches + num_err_matches

    squad_mates = ["friendA", "friendB"]
    full_squad = [player_id] + squad_mates
    
    match_ids = []
    match_details_map = {}

    # OK Matches with frequent squad
    for i in range(num_ok_matches):
        match_id = f"match_ok_{i}"
        match_ids.append(match_id)
        participants = [
            {"type": "participant", "id": f"p_main_ok{i}", "attributes": {"stats": {"playerId": player_id}}},
            {"type": "participant", "id": f"p_fA_ok{i}", "attributes": {"stats": {"playerId": squad_mates[0]}}},
            {"type": "participant", "id": f"p_fB_ok{i}", "attributes": {"stats": {"playerId": squad_mates[1]}}},
        ]
        roster = {"type": "roster", "id": f"r_ok{i}", "relationships": {"participants": {"data": [
            {"id": f"p_main_ok{i}"}, {"id": f"p_fA_ok{i}"}, {"id": f"p_fB_ok{i}"}
        ]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}

    # Error Matches
    for i in range(num_err_matches):
        match_id = f"match_err_{i}"
        match_ids.append(match_id)
        # This match_id will cause get_match_details to raise an error
        # match_details_map[match_id] = APIError("Simulated error for this match", 500) # This was for direct side_effect
    
    async def custom_get_match_details(match_id_arg, platform_shard_arg):
        if "match_err_" in match_id_arg:
            raise APIError(f"Simulated error for {match_id_arg}", 500)
        return match_details_map.get(match_id_arg, {})
    
    mock_pubg_api.get_match_details.side_effect = custom_get_match_details
    mock_pubg_api.setup_default_responses(player_id=player_id, match_ids=match_ids) # Not in clan

    team, msg, processed_matches = await identify_player_team(player_id, "steam", mock_pubg_api)

    assert team is not None
    assert sorted(team) == sorted(full_squad) # Frequent squad identified from OK matches
    assert "identified by frequent squad" in msg.lower()
    assert f"({num_ok_matches}/{num_ok_matches} analyzed matches)" in msg # Message reflects only successfully analyzed matches
    assert len(processed_matches) == num_ok_matches # Only OK matches are in processed_matches

@pytest.mark.asyncio
async def test_player_in_solo_clan(mock_pubg_api):
    player_id = "player_solo_clan"
    clan_id = "solo_clan_id"
    clan_members = [player_id] # Only the player themself

    # Play some random matches, not enough to form a frequent squad
    num_matches = MIN_GAMES_FOR_FREQUENT_TEAM -1 # e.g. 2
    match_ids = [f"match_solo_random_{i}" for i in range(num_matches)]
    match_details_map = {}
    for i, match_id in enumerate(match_ids):
        participants = [
            {"type": "participant", "id": f"p_main_{i}", "attributes": {"stats": {"playerId": player_id}}},
            {"type": "participant", "id": f"p_rand_{i}", "attributes": {"stats": {"playerId": f"random_player_{i}"}}},
        ]
        roster = {"type": "roster", "id": f"r_{i}", "relationships": {"participants": {"data": [
            {"id": f"p_main_{i}"}, {"id": f"p_rand_{i}"}
        ]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}
    
    mock_pubg_api.setup_default_responses(
        player_id=player_id, clan_id=clan_id, clan_members=clan_members,
        match_ids=match_ids, match_details_map=match_details_map
    )

    team, msg, processed_matches = await identify_player_team(player_id, "steam", mock_pubg_api)
    
    assert team is None # No team identified as clan has only 1 member and no frequent squad
    assert "player is in a solo clan" in msg.lower()
    assert len(processed_matches) == num_matches

@pytest.mark.asyncio
async def test_clan_identified_but_no_recent_clan_games(mock_pubg_api):
    player_id = "player_inactive_clan_ties"
    clan_id = "clan_inactive"
    clan_members = [player_id, "clan_mate_A", "clan_mate_B"] # Clan exists
    
    # Player plays MIN_GAMES_FOR_FREQUENT_TEAM with a non-clan squad.
    # Player plays 0 games with clan members.
    num_squad_games = MIN_GAMES_FOR_FREQUENT_TEAM # e.g. 3
    squad_mates = ["friend1", "friend2"]
    frequent_squad = [player_id] + squad_mates

    match_ids = [f"match_squad_{i}" for i in range(num_squad_games)]
    match_details_map = {}
    for i, match_id in enumerate(match_ids):
        participants = [
            {"type": "participant", "id": f"p_main_s{i}", "attributes": {"stats": {"playerId": player_id}}},
            {"type": "participant", "id": f"p_f1_s{i}", "attributes": {"stats": {"playerId": squad_mates[0]}}},
            {"type": "participant", "id": f"p_f2_s{i}", "attributes": {"stats": {"playerId": squad_mates[1]}}},
        ]
        roster = {"type": "roster", "id": f"rs_{i}", "relationships": {"participants": {"data": [
            {"id": f"p_main_s{i}"}, {"id": f"p_f1_s{i}"}, {"id": f"p_f2_s{i}"} ]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}

    # Add some other random games to fill up NUM_MATCHES_TO_ANALYZE if needed
    num_random_games = NUM_MATCHES_TO_ANALYZE - num_squad_games
    for i in range(num_random_games):
        match_id = f"match_random_{i}"
        match_ids.append(match_id)
        participants = [
            {"type": "participant", "id": f"p_main_r{i}", "attributes": {"stats": {"playerId": player_id}}},
            {"type": "participant", "id": f"p_rand_r{i}", "attributes": {"stats": {"playerId": f"random_player_{i}"}}},
        ]
        roster = {"type": "roster", "id": f"rr_{i}", "relationships": {"participants": {"data": [
            {"id": f"p_main_r{i}"}, {"id": f"p_rand_r{i}"} ]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}


    mock_pubg_api.setup_default_responses(
        player_id=player_id, clan_id=clan_id, clan_members=clan_members,
        match_ids=match_ids, match_details_map=match_details_map
    )

    team, msg, processed_matches = await identify_player_team(player_id, "steam", mock_pubg_api)

    # Clan team play frequency is 0 (less than MIN_CLAN_GAMES_THRESHOLD)
    # Frequent squad play frequency is num_squad_games (meets MIN_GAMES_FOR_FREQUENT_TEAM)
    # So, frequent squad should be chosen.
    assert team is not None
    assert sorted(team) == sorted(frequent_squad)
    assert "identified by frequent squad" in msg.lower()
    assert f"({num_squad_games}/{NUM_MATCHES_TO_ANALYZE}" in msg
    assert len(processed_matches) == NUM_MATCHES_TO_ANALYZE

@pytest.mark.asyncio
async def test_tie_between_clan_and_squad_frequency_clan_wins(mock_pubg_api):
    player_id = "player_tie_clan_wins"
    clan_id = "clan_tie"
    clan_members = [player_id, "clan_mateX"]
    squad_mates = ["friendX", "friendY"]
    frequent_squad_full = [player_id] + squad_mates
    
    # Both clan and squad play exactly MIN_GAMES_FOR_FREQUENT_TEAM (which is also MIN_CLAN_GAMES_THRESHOLD)
    # For this test, let's assume MIN_GAMES_FOR_FREQUENT_TEAM = MIN_CLAN_GAMES_THRESHOLD = 3
    # If they are different, the logic might need adjustment or this test needs specific values.
    # The current logic prioritizes clan on ties.
    
    # For this test to be robust, ensure MIN_GAMES_FOR_FREQUENT_TEAM and MIN_CLAN_GAMES_THRESHOLD are equal.
    # If not, this test demonstrates behavior for the specific default values (3 and 3).
    assert MIN_GAMES_FOR_FREQUENT_TEAM == MIN_CLAN_GAMES_THRESHOLD, "This test assumes thresholds are equal for a true tie."

    game_count_for_tie = MIN_GAMES_FOR_FREQUENT_TEAM 
    
    match_ids = []
    match_details_map = {}

    # Clan games
    for i in range(game_count_for_tie):
        match_id = f"match_clan_tie_{i}"
        match_ids.append(match_id)
        participants = [{"type": "participant", "id": f"pc_main{i}", "attributes": {"stats": {"playerId": player_id}}},
                        {"type": "participant", "id": f"pc_cmX{i}", "attributes": {"stats": {"playerId": "clan_mateX"}}}]
        roster = {"type": "roster", "id": f"rc_tie{i}", "relationships": {"participants": {"data": [{"id": f"pc_main{i}"}, {"id": f"pc_cmX{i}"}]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}

    # Frequent squad games
    for i in range(game_count_for_tie):
        match_id = f"match_squad_tie_{i}"
        match_ids.append(match_id)
        participants = [{"type": "participant", "id": f"ps_main{i}", "attributes": {"stats": {"playerId": player_id}}},
                        {"type": "participant", "id": f"ps_fX{i}", "attributes": {"stats": {"playerId": "friendX"}}},
                        {"type": "participant", "id": f"ps_fY{i}", "attributes": {"stats": {"playerId": "friendY"}}}]
        roster = {"type": "roster", "id": f"rs_tie{i}", "relationships": {"participants": {"data": [{"id": f"ps_main{i}"}, {"id": f"ps_fX{i}"}, {"id": f"ps_fY{i}"}]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}
    
    # Fill remaining matches if NUM_MATCHES_TO_ANALYZE is larger
    remaining_matches = NUM_MATCHES_TO_ANALYZE - (2 * game_count_for_tie)
    for i in range(remaining_matches):
        match_id = f"match_random_tie_{i}"
        match_ids.append(match_id)
        participants = [{"type": "participant", "id": f"pr_main{i}", "attributes": {"stats": {"playerId": player_id}}},
                        {"type": "participant", "id": f"pr_rand{i}", "attributes": {"stats": {"playerId": f"rand_player_tie_{i}"}}}]
        roster = {"type": "roster", "id": f"rr_tie{i}", "relationships": {"participants": {"data": [{"id": f"pr_main{i}"}, {"id": f"pr_rand{i}"}]}}}
        match_details_map[match_id] = {"data": {"id": match_id}, "included": participants + [roster]}


    mock_pubg_api.setup_default_responses(
        player_id=player_id, clan_id=clan_id, clan_members=clan_members,
        match_ids=match_ids, match_details_map=match_details_map
    )

    team, msg, processed_matches = await identify_player_team(player_id, "steam", mock_pubg_api)

    assert team is not None
    assert sorted(team) == sorted(clan_members) # Clan should win on tie
    assert "identified by clan membership" in msg.lower()
    # Clan played `game_count_for_tie` games. Total analyzed games is NUM_MATCHES_TO_ANALYZE.
    assert f"({game_count_for_tie}/{NUM_MATCHES_TO_ANALYZE}" in msg 
    assert len(processed_matches) == NUM_MATCHES_TO_ANALYZE
