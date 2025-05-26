WEAPON_CLASSIFICATION = {
    "Item_Weapon_AK47_C": {"name": "AKM", "category": "AR"},
    "Item_Weapon_M416_C": {"name": "M416", "category": "AR"},
    "Item_Weapon_Kar98k_C": {"name": "Kar98k", "category": "SR"},
    "Item_Weapon_AWM_C": {"name": "AWM", "category": "SR"},
    "Item_Weapon_Mini14_C": {"name": "Mini 14", "category": "DMR"},
    "Item_Weapon_SKS_C": {"name": "SKS", "category": "DMR"},
    "Item_Weapon_UMP_C": {"name": "UMP9", "category": "SMG"}, # Original name, changed to UMP45
    "Item_Weapon_Vector_C": {"name": "Vector", "category": "SMG"},
    "Item_Weapon_Saiga12_C": {"name": "S12K", "category": "Shotgun"},
    "Item_Weapon_Berreta686_C": {"name": "S686", "category": "Shotgun"},
    
    # Added ARs
    "Item_Weapon_ACE32_C": {"name": "ACE32", "category": "AR"},
    "Item_Weapon_AUG_C": {"name": "AUG A3", "category": "AR"},
    "Item_Weapon_BerylM762_C": {"name": "Beryl M762", "category": "AR"},
    "Item_Weapon_Groza_C": {"name": "Groza", "category": "AR"},
    # "Item_Weapon_HK416_C": {"name": "M416", "category": "AR"}, # This is typically the same as M416_C, avoid duplicate names if Item ID is primary key
    "Item_Weapon_K2_C": {"name": "K2", "category": "AR"},
    "Item_Weapon_M16A4_C": {"name": "M16A4", "category": "AR"},
    "Item_Weapon_Mk47Mutant_C": {"name": "Mk47 Mutant", "category": "AR"},
    "Item_Weapon_QBZ95_C": {"name": "QBZ", "category": "AR"}, # Often Item_Weapon_QBZ95_C
    "Item_Weapon_SCAR-L_C": {"name": "SCAR-L", "category": "AR"},
    "Item_Weapon_G36C_C": {"name": "G36C", "category": "AR"},
    "Item_Weapon_FAMASG2_C": {"name": "FAMAS", "category": "AR"},

    # Added SRs
    "Item_Weapon_M24_C": {"name": "M24", "category": "SR"},
    "Item_Weapon_Mosin_C": {"name": "Mosin Nagant", "category": "SR"},
    "Item_Weapon_Win1894_C": {"name": "Win94", "category": "SR"}, # Lever Action, often grouped with SRs
    "Item_Weapon_L6_C": {"name": "Lynx AMR", "category": "SR"}, # Anti-Materiel Rifle

    # Added DMRs
    "Item_Weapon_Dragunov_C": {"name": "Dragunov", "category": "DMR"}, # SVD
    "Item_Weapon_FNFal_C": {"name": "SLR", "category": "DMR"},
    "Item_Weapon_Mk12_C": {"name": "Mk12", "category": "DMR"},
    "Item_Weapon_Mk14_C": {"name": "Mk14 EBR", "category": "DMR"},
    "Item_Weapon_QBU88_C": {"name": "QBU", "category": "DMR"},
    "Item_Weapon_VSS_C": {"name": "VSS", "category": "DMR"}, # Vintorez

    # Added SMGs
    "Item_Weapon_BizonPP19_C": {"name": "PP-19 Bizon", "category": "SMG"},
    "Item_Weapon_JS9_C": {"name": "JS9", "category": "SMG"},
    "Item_Weapon_MP5K_C": {"name": "MP5K", "category": "SMG"},
    "Item_Weapon_MP9_C": {"name": "MP9", "category": "SMG"},
    "Item_Weapon_P90_C": {"name": "P90", "category": "SMG"},
    "Item_Weapon_Thompson_C": {"name": "Tommy Gun", "category": "SMG"},
    "Item_Weapon_UZI_C": {"name": "Micro UZI", "category": "SMG"},
    "Item_Weapon_UMP45_C": {"name": "UMP45", "category": "SMG"}, # Current UMP

    # Added Shotguns
    "Item_Weapon_DP12_C": {"name": "DBS", "category": "Shotgun"},
    "Item_Weapon_OriginS12_C": {"name": "O12", "category": "Shotgun"}, # Origin 12
    "Item_Weapon_S1897_C": {"name": "S1897", "category": "Shotgun"}, # Winchester Model 1897
    "Item_Weapon_Sawnoff_C": {"name": "Sawed-off", "category": "Pistol"}, # Often pistol slot, but shotgun type
    "Item_Weapon_NS2000_C": {"name": "NS2000", "category": "Shotgun"},

    # LMGs (Light Machine Guns) - can be a separate category or grouped
    "Item_Weapon_DP-28_C": {"name": "DP-28", "category": "LMG"},
    "Item_Weapon_M249_C": {"name": "M249", "category": "LMG"},
    "Item_Weapon_MG3_C": {"name": "MG3", "category": "LMG"},

    # Pistols - generally not primary, but for completeness if ever needed
    "Item_Weapon_Glock18_C": {"name": "P18C", "category": "Pistol"},
    "Item_Weapon_M1911_C": {"name": "P1911", "category": "Pistol"},
    "Item_Weapon_M9_C": {"name": "P92", "category": "Pistol"},
    "Item_Weapon_R1895_C": {"name": "R1895", "category": "Pistol"},
    "Item_Weapon_R45_C": {"name": "R45", "category": "Pistol"},
    "Item_Weapon_Skorpion_C": {"name": "Skorpion", "category": "Pistol"}, # Machine Pistol
    "Item_Weapon_DesertEagle_C": {"name": "Deagle", "category": "Pistol"},

    # Others
    "Item_Weapon_Pan_C": {"name": "Pan", "category": "Melee"},
    "Item_Weapon_Crossbow_C": {"name": "Crossbow", "category": "Misc"},
}

def get_top_damage_weapons_by_category(weapon_summaries):
    """
    Processes weaponSummaries to find the weapon with the highest total damage
    for each specified category (AR, SR, DMR, SMG, Shotgun).

    Args:
        weapon_summaries (dict): The 'weaponSummaries' object from the PUBG API.
                                 Example: {"Item_Weapon_AK47_C": {"StatsTotal": {"DamagePlayer": 100.0}}, ...}

    Returns:
        dict: A dictionary where keys are categories and values are dictionaries
              containing the name, damage, and item_id of the top weapon in that category.
              Example: {"AR": {"name": "AKM", "damage": 150.0, "item_id": "Item_Weapon_AK47_C"}, ...}
    """
    target_categories = {"AR", "SR", "DMR", "SMG", "Shotgun"}
    top_weapons = {category: None for category in target_categories}

    if not weapon_summaries: # Handles None or empty dict
        return top_weapons

    for item_id, stats_data in weapon_summaries.items():
        weapon_info = WEAPON_CLASSIFICATION.get(item_id)

        if weapon_info and weapon_info["category"] in target_categories:
            category = weapon_info["category"]
            # PUBG API seems to use "StatsTotal" in some docs, but actual JSON from fetch_pubg_data.py used "OfficialStatsTotal"
            # Also, weapon mastery data might have XPTotal, LevelCurrent etc. We need damage.
            # From player_weapon_mastery_chocoTaco_steam.json, structure is:
            # "weaponSummaries": { "Item_Weapon_ACE32_C": { "StatsTotal": { "DamagePlayer": 27158.982 } } }
            # The requirement is to change to 'OfficialStatsTotal'.
            
            # Check if 'OfficialStatsTotal' exists and then if 'DamagePlayer' exists within it
            official_stats = stats_data.get('OfficialStatsTotal', {}) # Default to empty dict if 'OfficialStatsTotal' is missing
            damage = official_stats.get('DamagePlayer', 0.0) # Default to 0.0 if 'DamagePlayer' is missing

            current_top_weapon = top_weapons.get(category)
            if current_top_weapon is None or damage > current_top_weapon["damage"]:
                top_weapons[category] = {
                    "name": weapon_info["name"],
                    "damage": damage,
                    "item_id": item_id
                }
    
    return top_weapons

# Example usage with a dummy weapon_summaries from a file (for testing this util in isolation)
# if __name__ == '__main__':
#     import json
#     try:
#         with open('player_weapon_mastery_chocoTaco_steam.json', 'r') as f:
#             sample_data = json.load(f)
#         weapon_summaries_sample = sample_data.get('data', {}).get('attributes', {}).get('weaponSummaries')
#         if weapon_summaries_sample:
#             top_weapons_results = get_top_damage_weapons_by_category(weapon_summaries_sample)
#             print("Top damage weapons by category:")
#             for category, weapon_data in top_weapons_results.items():
#                 if weapon_data:
#                     print(f"  {category}: {weapon_data['name']} (Damage: {weapon_data['damage']})")
#                 else:
#                     print(f"  {category}: No weapon found or no damage dealt.")
#         else:
#             print("Weapon summaries not found in the sample JSON.")
#     except FileNotFoundError:
#         print("Sample JSON file 'player_weapon_mastery_chocoTaco_steam.json' not found. Cannot run example.")
#     except json.JSONDecodeError:
#         print("Error decoding the sample JSON file.")
