WEAPON_CATEGORIES = {
    # Assault Rifles (AR)
    "Item_Weapon_ACE32_C": "AR",
    "Item_Weapon_AKM_C": "AR",
    "Item_Weapon_AUG_C": "AR",
    "Item_Weapon_BerylM762_C": "AR",
    "Item_Weapon_G36C_C": "AR",
    "Item_Weapon_Groza_C": "AR",
    "Item_Weapon_K2_C": "AR",
    "Item_Weapon_M16A4_C": "AR",
    "Item_Weapon_M416_C": "AR",
    "Item_Weapon_Mk47Mutant_C": "AR",
    "Item_Weapon_QBZ95_C": "AR",
    "Item_Weapon_SCAR-L_C": "AR",
    "Item_Weapon_FAMASG2_C": "AR", # FAMAS

    # Designated Marksman Rifles (DMR)
    "Item_Weapon_Mini14_C": "DMR",
    "Item_Weapon_Mk12_C": "DMR",
    "Item_Weapon_Mk14_C": "DMR", # EBR
    "Item_Weapon_QBU88_C": "DMR",
    "Item_Weapon_SKS_C": "DMR",
    "Item_Weapon_SLR_C": "DMR",
    "Item_Weapon_VSS_C": "DMR",
    "Item_Weapon_Dragunov_C": "DMR", # SVD

    # Sniper Rifles (SR)
    "Item_Weapon_AWM_C": "SR",
    "Item_Weapon_Kar98k_C": "SR",
    "Item_Weapon_M24_C": "SR",
    "Item_Weapon_MosinNagant_C": "SR",
    "Item_Weapon_Win94_C": "SR",
    "Item_Weapon_Lynx_AMR_C": "SR", # AMR_Lynx

    # Submachine Guns (SMG)
    "Item_Weapon_BizonPP19_C": "SMG",
    "Item_Weapon_DP28_C": "SMG", # LMG, but often grouped with SMGs in usage type for stats
    "Item_Weapon_JS9_C": "SMG",
    "Item_Weapon_MicroUzi_C": "SMG",
    "Item_Weapon_MP5K_C": "SMG",
    "Item_Weapon_MP9_C": "SMG",
    "Item_Weapon_P90_C": "SMG",
    "Item_Weapon_ThompsonSubmachineGun_C": "SMG",
    "Item_Weapon_UMP45_C": "SMG",
    "Item_Weapon_Vector_C": "SMG",

    # Shotguns
    "Item_Weapon_BenelliM4_C": "Shotgun", # M1014
    "Item_Weapon_DP12_C": "Shotgun",
    "Item_Weapon_Saiga12K_C": "Shotgun",
    "Item_Weapon_Winchester_C": "Shotgun", # S1897
    "Item_Weapon_Berreta686_C": "Shotgun", # S686
    "Item_Weapon_Sawnoff_C": "Shotgun",

    # Light Machine Guns (LMG) - can be its own category or grouped. For now, I'll keep it separate for detail.
    "Item_Weapon_M249_C": "LMG",
    "Item_Weapon_MG3_C": "LMG",

    # Pistols (often excluded from primary weapon stats, but good to have)
    "Item_Weapon_DesertEagle_C": "Pistol",
    "Item_Weapon_Glock18_C": "Pistol",
    "Item_Weapon_M1911_C": "Pistol",
    "Item_Weapon_M9_C": "Pistol", # P92
    "Item_Weapon_P18C_C": "Pistol",
    "Item_Weapon_P1911_C": "Pistol",
    "Item_Weapon_R1895_C": "Pistol",
    "Item_Weapon_R45_C": "Pistol",
    "Item_Weapon_Skorpion_C": "Pistol", # Vz61

    # Other/Melee/Crossbow - generally ignored for DPM of primary weapons
    "Item_Weapon_Crossbow_C": "Other",
    "Item_Weapon_Pan_C": "Melee",
    # ... other melee weapons
}

def get_weapon_category(weapon_id: str) -> str:
    """Returns the category for a given weapon ID, or 'Other' if not found."""
    return WEAPON_CATEGORIES.get(weapon_id, "Other")

# Mapping for frontend platform display names to API platform shards
PLATFORM_SHARD_MAP = {
    "KAKAO": "kakao",
    "STEAM": "steam",
    "PSN": "psn",
    "XBOX": "xbox",
    # Add other platforms as needed
    # "STADIA": "stadia" # Stadia is deprecated
}

def get_platform_shard(platform_display_name: str) -> str | None:
    """Converts a user-friendly platform name to its API shard equivalent."""
    return PLATFORM_SHARD_MAP.get(platform_display_name.upper())
