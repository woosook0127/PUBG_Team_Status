import pytest
from app.weapon_utils import get_weapon_category, get_platform_shard, WEAPON_CATEGORIES, PLATFORM_SHARD_MAP

def test_get_weapon_category_known_weapons():
    """Test that known weapon IDs return their correct categories."""
    assert get_weapon_category("Item_Weapon_M416_C") == "AR"
    assert get_weapon_category("Item_Weapon_Kar98k_C") == "SR"
    assert get_weapon_category("Item_Weapon_UMP45_C") == "SMG"
    assert get_weapon_category("Item_Weapon_Saiga12K_C") == "Shotgun"
    assert get_weapon_category("Item_Weapon_M249_C") == "LMG"
    assert get_weapon_category("Item_Weapon_DesertEagle_C") == "Pistol"
    assert get_weapon_category("Item_Weapon_Pan_C") == "Melee"
    assert get_weapon_category("Item_Weapon_Crossbow_C") == "Other"

def test_get_weapon_category_unknown_weapon():
    """Test that an unknown weapon ID returns 'Other'."""
    assert get_weapon_category("Item_Weapon_UnknownGun_C") == "Other"

def test_get_weapon_category_empty_id():
    """Test that an empty weapon ID returns 'Other'."""
    assert get_weapon_category("") == "Other"

def test_get_weapon_category_case_insensitivity_if_applicable():
    """
    Test if weapon ID matching should be case insensitive.
    Based on current WEAPON_CATEGORIES, it's case-sensitive.
    This test confirms the current behavior. If requirements change, this test would need to change.
    """
    assert get_weapon_category("item_weapon_m416_c") == "Other" # Current behavior is case-sensitive
    # If it were meant to be case-insensitive, the expected would be "AR"
    # and the get_weapon_category function or WEAPON_CATEGORIES keys would need adjustment.

def test_all_weapon_categories_covered():
    """Test to ensure all explicitly defined weapons in WEAPON_CATEGORIES are checked."""
    for weapon_id, category in WEAPON_CATEGORIES.items():
        assert get_weapon_category(weapon_id) == category

def test_get_platform_shard_known_platforms():
    """Test that known platform display names return correct shard values."""
    assert get_platform_shard("STEAM") == "steam"
    assert get_platform_shard("Steam") == "steam" # Test case-insensitivity of input
    assert get_platform_shard("steam") == "steam"
    assert get_platform_shard("KAKAO") == "kakao"
    assert get_platform_shard("kakao") == "kakao"
    assert get_platform_shard("PSN") == "psn"
    assert get_platform_shard("psn") == "psn"
    assert get_platform_shard("XBOX") == "xbox"
    assert get_platform_shard("xbox") == "xbox"

def test_get_platform_shard_unknown_platform():
    """Test that an unknown platform display name returns None."""
    assert get_platform_shard("NINTENDO_SWITCH") is None

def test_get_platform_shard_empty_string():
    """Test that an empty string for platform display name returns None."""
    assert get_platform_shard("") is None

def test_all_platform_shards_covered():
    """Test to ensure all explicitly defined platforms in PLATFORM_SHARD_MAP are checked."""
    for display_name, shard_value in PLATFORM_SHARD_MAP.items():
        assert get_platform_shard(display_name) == shard_value
        assert get_platform_shard(display_name.lower()) == shard_value # Check lowercase version too
        assert get_platform_shard(display_name.upper()) == shard_value # Check uppercase version

def test_get_platform_shard_mixed_case():
    """Test mixed case platform display names."""
    assert get_platform_shard("sTeAm") == "steam"
    assert get_platform_shard("kAkAo") == "kakao"
