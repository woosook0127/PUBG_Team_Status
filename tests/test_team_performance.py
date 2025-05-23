import pytest
from app.team_performance import calculate_team_performance_from_matches, calculate_overall_team_stats

# --- Sample Data for Team Performance Tests ---
MAIN_PLAYER_ID = "player_main"
TEAMMATE_A_ID = "teammate_A"
TEAMMATE_B_ID = "teammate_B"
TEAMMATE_C_ID = "teammate_C" # Part of team but no common matches in one scenario

IDENTIFIED_TEAM_WITH_MAIN = [MAIN_PLAYER_ID, TEAMMATE_A_ID, TEAMMATE_B_ID]
IDENTIFIED_TEAM_WITHOUT_MAIN_IN_LIST = [TEAMMATE_A_ID, TEAMMATE_B_ID] # Main player is implicit

REQUESTED_SEASON_ID = "season_current" # For now, this is mostly for passthrough, as filtering is limited

# --- Mock Match Details ---
# These represent the `processed_match_details_list` that `team_analyzer` would return.

# Match 1: Main player + Teammate A + Teammate B (Full Team A&B)
MATCH_1_DETAILS = {
    "data": {"id": "match1", "attributes": {"seasonState": "progress"}}, # Assume season matches for simplicity
    "included": [
        {"type": "participant", "id": "p_match1_main", "attributes": {"stats": {"playerId": MAIN_PLAYER_ID, "kills": 2, "damageDealt": 250.0, "timeSurvived": 1800.0, "assists": 1}}},
        {"type": "participant", "id": "p_match1_tmA", "attributes": {"stats": {"playerId": TEAMMATE_A_ID, "kills": 3, "damageDealt": 300.0, "timeSurvived": 1800.0, "assists": 0}}},
        {"type": "participant", "id": "p_match1_tmB", "attributes": {"stats": {"playerId": TEAMMATE_B_ID, "kills": 1, "damageDealt": 150.0, "timeSurvived": 1800.0, "assists": 2}}},
        {"type": "roster", "id": "roster1_match1", "attributes": {"stats": {"rank": 5}}, 
         "relationships": {"participants": {"data": [{"id": "p_match1_main"}, {"id": "p_match1_tmA"}, {"id": "p_match1_tmB"}]}}}
    ]
}
# Match 2: Main player + Teammate A only
MATCH_2_DETAILS = {
    "data": {"id": "match2", "attributes": {"seasonState": "progress"}},
    "included": [
        {"type": "participant", "id": "p_match2_main", "attributes": {"stats": {"playerId": MAIN_PLAYER_ID, "kills": 1, "damageDealt": 100.0, "timeSurvived": 1200.0, "assists": 0}}},
        {"type": "participant", "id": "p_match2_tmA", "attributes": {"stats": {"playerId": TEAMMATE_A_ID, "kills": 5, "damageDealt": 550.0, "timeSurvived": 1200.0, "assists": 1}}},
        {"type": "participant", "id": "p_match2_other", "attributes": {"stats": {"playerId": "random_player", "kills": 0, "damageDealt": 50.0, "timeSurvived": 1200.0, "assists": 0}}},
        {"type": "roster", "id": "roster1_match2", "attributes": {"stats": {"rank": 10}}, 
         "relationships": {"participants": {"data": [{"id": "p_match2_main"}, {"id": "p_match2_tmA"}, {"id": "p_match2_other"}]}}}
    ]
}
# Match 3: Main player + Teammate B only
MATCH_3_DETAILS = {
    "data": {"id": "match3", "attributes": {"seasonState": "progress"}},
    "included": [
        {"type": "participant", "id": "p_match3_main", "attributes": {"stats": {"playerId": MAIN_PLAYER_ID, "kills": 3, "damageDealt": 300.0, "timeSurvived": 1500.0, "assists": 1}}},
        {"type": "participant", "id": "p_match3_tmB", "attributes": {"stats": {"playerId": TEAMMATE_B_ID, "kills": 2, "damageDealt": 200.0, "timeSurvived": 1500.0, "assists": 1}}},
        {"type": "roster", "id": "roster1_match3", "attributes": {"stats": {"rank": 3}}, 
         "relationships": {"participants": {"data": [{"id": "p_match3_main"}, {"id": "p_match3_tmB"}]}}}
    ]
}
# Match 4: Main player + Teammate A + Teammate B (Full Team A&B) - different stats
MATCH_4_DETAILS = {
    "data": {"id": "match4", "attributes": {"seasonState": "progress"}},
    "included": [
        {"type": "participant", "id": "p_match4_main", "attributes": {"stats": {"playerId": MAIN_PLAYER_ID, "kills": 4, "damageDealt": 400.0, "timeSurvived": 2000.0, "assists": 0}}},
        {"type": "participant", "id": "p_match4_tmA", "attributes": {"stats": {"playerId": TEAMMATE_A_ID, "kills": 2, "damageDealt": 220.0, "timeSurvived": 2000.0, "assists": 2}}},
        {"type": "participant", "id": "p_match4_tmB", "attributes": {"stats": {"playerId": TEAMMATE_B_ID, "kills": 3, "damageDealt": 280.0, "timeSurvived": 2000.0, "assists": 1}}},
        {"type": "roster", "id": "roster1_match4", "attributes": {"stats": {"rank": 1}}, 
         "relationships": {"participants": {"data": [{"id": "p_match4_main"}, {"id": "p_match4_tmA"}, {"id": "p_match4_tmB"}]}}}
    ]
}
# Match 5: Main player solo (or with randoms not in identified team)
MATCH_5_SOLO_DETAILS = {
    "data": {"id": "match5", "attributes": {"seasonState": "progress"}},
    "included": [
        {"type": "participant", "id": "p_match5_main", "attributes": {"stats": {"playerId": MAIN_PLAYER_ID, "kills": 5, "damageDealt": 500.0, "timeSurvived": 2100.0, "assists": 0}}},
        {"type": "participant", "id": "p_match5_rand", "attributes": {"stats": {"playerId": "random_X", "kills": 1, "damageDealt": 100.0, "timeSurvived": 2100.0, "assists": 0}}},
        {"type": "roster", "id": "roster1_match5", "attributes": {"stats": {"rank": 2}},
         "relationships": {"participants": {"data": [{"id": "p_match5_main"}, {"id": "p_match5_rand"}]}}}
    ]
}

PROCESSED_MATCHES_SAMPLE = [MATCH_1_DETAILS, MATCH_2_DETAILS, MATCH_3_DETAILS, MATCH_4_DETAILS, MATCH_5_SOLO_DETAILS]

# --- Tests for calculate_team_performance_from_matches ---

def test_calculate_team_performance_basic():
    team_members = [MAIN_PLAYER_ID, TEAMMATE_A_ID, TEAMMATE_B_ID] # Main player included for context, but stats are for mates
    
    # Teammate A:
    # Match 1: Kills=3, Dmg=300, Surv=1800, Assists=0, Rank=5 (with main)
    # Match 2: Kills=5, Dmg=550, Surv=1200, Assists=1, Rank=10 (with main)
    # Match 4: Kills=2, Dmg=220, Surv=2000, Assists=2, Rank=1 (with main)
    # Total Matches with Main: 3
    # Total Kills = 3+5+2 = 10; Avg Kills = 10/3 = 3.33
    # Total Dmg = 300+550+220 = 1070; Avg Dmg = 1070/3 = 356.67
    # Total Surv = 1800+1200+2000 = 5000; Avg Surv = 5000/3 = 1666.67
    # Total Assists = 0+1+2 = 3; Avg Assists = 3/3 = 1.0
    # Total Rank Sum = 5+10+1 = 16; Avg Rank = 16/3 = 5.33

    # Teammate B:
    # Match 1: Kills=1, Dmg=150, Surv=1800, Assists=2, Rank=5 (with main)
    # Match 3: Kills=2, Dmg=200, Surv=1500, Assists=1, Rank=3 (with main)
    # Match 4: Kills=3, Dmg=280, Surv=2000, Assists=1, Rank=1 (with main)
    # Total Matches with Main: 3
    # Total Kills = 1+2+3 = 6; Avg Kills = 6/3 = 2.0
    # Total Dmg = 150+200+280 = 630; Avg Dmg = 630/3 = 210.0
    # Total Surv = 1800+1500+2000 = 5300; Avg Surv = 5300/3 = 1766.67
    # Total Assists = 2+1+1 = 4; Avg Assists = 4/3 = 1.33
    # Total Rank Sum = 5+3+1 = 9; Avg Rank = 9/3 = 3.0
    
    result = calculate_team_performance_from_matches(
        MAIN_PLAYER_ID, team_members, PROCESSED_MATCHES_SAMPLE, REQUESTED_SEASON_ID
    )
    
    assert len(result) == 2 # For Teammate A and Teammate B
    
    teammate_a_stats = next(s for s in result if s["teammate_account_id"] == TEAMMATE_A_ID)
    teammate_b_stats = next(s for s in result if s["teammate_account_id"] == TEAMMATE_B_ID)

    assert teammate_a_stats["matches_played_together"] == 3
    assert pytest.approx(teammate_a_stats["avg_kills"]) == 3.33
    assert pytest.approx(teammate_a_stats["avg_damage_dealt"]) == 356.67
    assert pytest.approx(teammate_a_stats["avg_survival_time_seconds"]) == 1666.67
    assert pytest.approx(teammate_a_stats["avg_assists"]) == 1.0
    assert pytest.approx(teammate_a_stats["avg_match_rank"]) == 5.33

    assert teammate_b_stats["matches_played_together"] == 3
    assert pytest.approx(teammate_b_stats["avg_kills"]) == 2.0
    assert pytest.approx(teammate_b_stats["avg_damage_dealt"]) == 210.0
    assert pytest.approx(teammate_b_stats["avg_survival_time_seconds"]) == 1766.67
    assert pytest.approx(teammate_b_stats["avg_assists"]) == 1.33
    assert pytest.approx(teammate_b_stats["avg_match_rank"]) == 3.0

def test_calculate_team_performance_no_common_matches_for_one_teammate():
    team_members = [MAIN_PLAYER_ID, TEAMMATE_A_ID, TEAMMATE_C_ID] # Teammate C has no common matches in PROCESSED_MATCHES_SAMPLE
    result = calculate_team_performance_from_matches(
        MAIN_PLAYER_ID, team_members, PROCESSED_MATCHES_SAMPLE, REQUESTED_SEASON_ID
    )
    assert len(result) == 2 # Teammate A and Teammate C
    teammate_c_stats = next(s for s in result if s["teammate_account_id"] == TEAMMATE_C_ID)
    assert teammate_c_stats["matches_played_together"] == 0
    assert teammate_c_stats["avg_kills"] == 0.0

def test_calculate_team_performance_empty_match_list():
    result = calculate_team_performance_from_matches(
        MAIN_PLAYER_ID, IDENTIFIED_TEAM_WITH_MAIN, [], REQUESTED_SEASON_ID
    )
    assert len(result) == 2 # For Teammate A and B
    for stats in result:
        assert stats["matches_played_together"] == 0

def test_calculate_team_performance_no_teammates():
    result = calculate_team_performance_from_matches(
        MAIN_PLAYER_ID, [MAIN_PLAYER_ID], PROCESSED_MATCHES_SAMPLE, REQUESTED_SEASON_ID
    )
    assert len(result) == 0


# --- Tests for calculate_overall_team_stats ---

def test_calculate_overall_team_stats_full_team_plays():
    # Full team: MAIN_PLAYER_ID, TEAMMATE_A_ID, TEAMMATE_B_ID
    # Matches 1 & 4 are full team.
    # Match 1: TeamKills=2+3+1=6, TeamDmg=250+300+150=700, AvgTeamSurv=(1800*3)/3=1800, Rank=5
    # Match 4: TeamKills=4+2+3=9, TeamDmg=400+220+280=900, AvgTeamSurv=(2000*3)/3=2000, Rank=1
    # Totals: Matches=2
    # AvgTeamKills = (6+9)/2 = 15/2 = 7.5
    # AvgTeamDmg = (700+900)/2 = 1600/2 = 800.0
    # AvgTeamSurv = (1800+2000)/2 = 3800/2 = 1900.0
    # AvgTeamRank = (5+1)/2 = 6/2 = 3.0
    
    result = calculate_overall_team_stats(
        IDENTIFIED_TEAM_WITH_MAIN, PROCESSED_MATCHES_SAMPLE, REQUESTED_SEASON_ID
    )
    
    assert result["matches_played_as_full_team"] == 2
    assert pytest.approx(result["avg_team_kills"]) == 7.5
    assert pytest.approx(result["avg_team_damage"]) == 800.0
    assert pytest.approx(result["avg_team_survival_time"]) == 1900.0
    assert pytest.approx(result["avg_team_match_rank"]) == 3.0
    assert "2 recent match(es)" in result["message"]

def test_calculate_overall_team_stats_no_full_team_matches():
    # Use only Match 2 (Main+A) and Match 3 (Main+B) - no full team matches for IDENTIFIED_TEAM_WITH_MAIN
    partial_matches = [MATCH_2_DETAILS, MATCH_3_DETAILS, MATCH_5_SOLO_DETAILS]
    result = calculate_overall_team_stats(
        IDENTIFIED_TEAM_WITH_MAIN, partial_matches, REQUESTED_SEASON_ID
    )
    assert result["matches_played_as_full_team"] == 0
    assert result["avg_team_kills"] == 0.0
    assert "no recent matches found" in result["message"].lower()

def test_calculate_overall_team_stats_empty_match_list():
    result = calculate_overall_team_stats(IDENTIFIED_TEAM_WITH_MAIN, [], REQUESTED_SEASON_ID)
    assert result["matches_played_as_full_team"] == 0
    assert "no recent matches found" in result["message"].lower()

def test_calculate_overall_team_stats_team_too_small():
    small_team = [MAIN_PLAYER_ID]
    result = calculate_overall_team_stats(small_team, PROCESSED_MATCHES_SAMPLE, REQUESTED_SEASON_ID)
    assert result["matches_played_as_full_team"] == 0
    assert "not enough team members" in result["message"].lower()

def test_calculate_overall_team_stats_team_members_not_in_any_roster_as_full_unit():
    # Team is Main, A, C. Match 1 has Main, A, B. No match has Main, A, C together.
    team_with_c = [MAIN_PLAYER_ID, TEAMMATE_A_ID, TEAMMATE_C_ID]
    result = calculate_overall_team_stats(team_with_c, PROCESSED_MATCHES_SAMPLE, REQUESTED_SEASON_ID)
    assert result["matches_played_as_full_team"] == 0
    assert "no recent matches found" in result["message"].lower()

# Example for season filtering (conceptual, as current implementation notes difficulty)
# To make this test meaningful, MATCH_1_DETAILS would need a reliable seasonId attribute.
# For now, this test will behave like test_calculate_overall_team_stats_full_team_plays
# because the season filtering logic in calculate_overall_team_stats is commented out.
def test_calculate_overall_team_stats_with_season_filtering_if_implemented():
    # Modify MATCH_1_DETAILS to have a specific season if the logic were to use it
    # MATCH_1_DETAILS_SEASONED = MATCH_1_DETAILS.copy()
    # MATCH_1_DETAILS_SEASONED["data"]["attributes"]["hypotheticalSeasonId"] = REQUESTED_SEASON_ID 
    # MATCH_4_DETAILS_OTHER_SEASON = MATCH_4_DETAILS.copy()
    # MATCH_4_DETAILS_OTHER_SEASON["data"]["attributes"]["hypotheticalSeasonId"] = "other_season"
    # seasoned_matches = [MATCH_1_DETAILS_SEASONED, MATCH_2_DETAILS, MATCH_3_DETAILS, MATCH_4_DETAILS_OTHER_SEASON]
    
    # This test currently doesn't test season filtering due to the commented out logic.
    # It's a placeholder for if that capability is robustly added.
    result = calculate_overall_team_stats(
        IDENTIFIED_TEAM_WITH_MAIN, PROCESSED_MATCHES_SAMPLE, "some_specific_season_id_to_filter_by"
    )
    # If filtering was active and effective, assertions here would change based on which matches meet the criteria.
    # For now, it will behave like test_calculate_overall_team_stats_full_team_plays
    assert result["matches_played_as_full_team"] == 2 # Because current logic doesn't filter by season string
    assert pytest.approx(result["avg_team_match_rank"]) == 3.0

# Test with a team definition that doesn't include the main player explicitly in the list
# (though main_player_id is passed to the function)
def test_calculate_team_performance_team_def_without_main_player():
    # Teammate A: (Stats from Match 1, 2, 4 as before)
    # Teammate B: (Stats from Match 1, 3, 4 as before)
    result = calculate_team_performance_from_matches(
        MAIN_PLAYER_ID, IDENTIFIED_TEAM_WITHOUT_MAIN_IN_LIST, PROCESSED_MATCHES_SAMPLE, REQUESTED_SEASON_ID
    )
    assert len(result) == 2 # For Teammate A and Teammate B
    # Stats should be identical to test_calculate_team_performance_basic
    teammate_a_stats = next(s for s in result if s["teammate_account_id"] == TEAMMATE_A_ID)
    assert teammate_a_stats["matches_played_together"] == 3
    assert pytest.approx(teammate_a_stats["avg_kills"]) == 3.33

    teammate_b_stats = next(s for s in result if s["teammate_account_id"] == TEAMMATE_B_ID)
    assert teammate_b_stats["matches_played_together"] == 3
    assert pytest.approx(teammate_b_stats["avg_kills"]) == 2.0
