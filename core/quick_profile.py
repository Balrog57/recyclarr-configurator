"""
Quick profile builder: turns simple preferences (content, quality, language order, codecs)
into a Recyclarr v8 instance setup based on TRaSH Guides profiles.

Language logic (checked against Radarr/Sonarr LanguageParser): "VOSTFR" is NOT parsed as French,
so a VOSTFR release looks like plain VO (original audio) and only the VOSTFR title CF tells them apart.
Each language "bucket" ends up with this net score:
    MULTi  (original + French audio) = Language: Original + French
    VF     (French audio only)       = Language: Not Original
    VOSTFR (original audio + FR subs)= Language: Not French + VOSTFR
    VO     (original audio only)     = Language: Not French
"""

LANGUAGES = {
    "multi": "MULTi (VO + VF)",
    "vf": "VF seule",
    "vostfr": "VOSTFR",
    "vo": "VO sans sous-titres FR",
}

STEP = 500        # gap between two accepted languages (TRaSH uses 500 for MULTi vs VF)
REJECT = -10000   # TRaSH "unwanted" score

# TRaSH Guides quality profile trash_ids (immutable). Base variant -> profile per quality tier.
FRENCH_PROFILES = {
    "radarr": {
        "hd-bluray-web": {"multi-vf": "500ecc23572575511fd81893777d1e06", "multi-vo": "2572ce3ea4eef1c19d59e0e20ed1cea7", "vostfr": "1addc08c4232bc2617684d517df15f75"},
        "hd-remux": {"multi-vf": "6b93fe45f357e9a94228e5d4658e9bb5", "multi-vo": "c6460a102b312200c095a2d0982e0461", "vostfr": "d98f20924b001e9f6b9595d5440abc87"},
        "uhd-bluray-web": {"multi-vf": "e64b266178c7f70e208f493f00e0e50a", "multi-vo": "92ead7022d13a7858d54e328e6a2f8f9", "vostfr": "525bf0513e2ac22fe116e8d7bec0a6b5"},
        "uhd-remux": {"multi-vf": "595bb95c6b6970468880069dce23e1d2", "multi-vo": "1fef28c8c919f31cd86283b1baf527d4", "vostfr": "9b32fc61d8ec83ed131f50f1db80505a"},
    },
    "sonarr": {
        "hd-bluray-web": {"multi-vf": "58e8dc75731040612dd6f4ac0676bfd7", "multi-vo": "4c48f506c1116a3a57ae33f12346bd15", "vostfr": "b34c968f58433a38e0e690d42a1dc37e"},
        "uhd-bluray-web": {"multi-vf": "68c8b82ad2b7ea1941fce71eb56421c3", "multi-vo": "6fa7364373e8f06206871d9c20a4fb3e", "vostfr": "d6252dce6af535107ed4b03e68052ae8"},
    },
}

TIERS = {
    "hd-bluray-web": "1080p - Bluray + WEB",
    "hd-remux": "1080p - Remux + WEB",
    "uhd-bluray-web": "2160p - Bluray + WEB",
    "uhd-remux": "2160p - Remux + WEB",
}

# TRaSH French anime recipe: [Anime] profile + french-anime score set + French anime release groups
ANIME_PROFILE = {"radarr": "722b624f9af1e492284c4bc842153a38", "sonarr": "20e0fc959f1f1704bed501f23bdae76f"}
# Their CFs have no required/default flag and the groups only include TRaSH's "Base Profile":
# they need select_all + an explicit assign_scores_to, or Recyclarr silently skips them.
ANIME_GROUPS = {
    "radarr": ["24c8342b620f7a229448ac2f51720e69", "12a919c8a5e2342db6e9c0b4e3c0756e"],  # French Anime, French release groups
    "sonarr": ["cb745c70bc9ea2ae49b72cfeed17cfd2", "9fa0bf3c8f8f00154431c3323a29eef2"],
}
# Kept from the former (v7) French anime template: MULTi (renaming), BR-DISK, FastSUB
ANIME_EXTRA_CFS = {
    "radarr": ["4b900e171accbfb172729b63323ea8ca", "ed38b889b31be83fda192888e2286d83", "7f9b93f82b7e996391525f2be1d891e0"],
    "sonarr": ["7ba05c6e0e14e793538174c679126996", "85c61753df5da1fb2aab6f2a47426b09", "ea0bb4b6ba388992fad1092703b5ff7b"],
}

LANGUAGE_CFS = {
    "radarr": {"orig_french": "0542a48746585dc4444bbbb8a6bdf6ea", "not_original": "d6e9318c875905d6cfb5bee961afcea9",
               "not_french": "533f782474f0819643c2ec0c1eeeb0ac", "vostfr": "9172b2f683f6223e3a1846427b417a3d"},
    "sonarr": {"orig_french": "10e77b96ae4770a7de645a91a53ce29a", "not_original": "ae575f95ab639ba5d15f663bf019e3e8",
               "not_french": "322fca6f8f3694acc1401ddb530fd33d", "vostfr": "07a32f77690263bb9fda1842db7e273f"},
}
CODEC_CFS = {
    "radarr": {"x265": ["dc98083864ea246d05a42df0d05f81cc", "839bea857ed2c0a8e084f3cbdbd65ecb"], "av1": ["cae4ca30163749b891686f95532519bd"]},
    "sonarr": {"x265": ["47435ece6b99a0b477caf360e79ba0bb", "9b64dff695c2115facf1b6ea59c9bd07"], "av1": ["15a05bc7c1a36e2b57fd628f8977e2fc"]},
}


def tiers_for(app: str, anime: bool) -> dict:
    if anime:
        return {"anime": "1080p - Remux + Bluray + WEB (TRaSH Anime)"}
    return {k: TIERS[k] for k in FRENCH_PROFILES[app]}


def language_cf_scores(ranking: list) -> dict:
    """ranking: accepted languages, best first. Returns the score of each language CF."""
    if not ranking:
        raise ValueError("Au moins une langue doit être acceptée")
    net = {lang: REJECT for lang in LANGUAGES}
    for i, lang in enumerate(ranking):
        net[lang] = (len(ranking) - 1 - i) * STEP
    return {
        "orig_french": net["multi"],
        "not_original": net["vf"],
        "not_french": net["vo"],
        "vostfr": net["vostfr"] - net["vo"],
    }


def build_quick_profile(data_manager, app: str, anime: bool, tier: str, ranking: list,
                        accept_x265: bool = False, accept_av1: bool = False) -> dict:
    """Returns {qdef, profile_trash_id, profile_name, score_set, cf_groups {id: options}, custom_formats (YAML-shaped)}."""
    top = ranking[0] if ranking else None
    if anime:
        profile_id = ANIME_PROFILE[app]
        score_set = "french-anime-vostfr" if top in ("vostfr", "vo") else "french-anime-multi"
        qdef = "anime"
    else:
        variant = "vostfr" if top in ("vostfr", "vo") else ("multi-vf" if "vf" in ranking else "multi-vo")
        profile_id = FRENCH_PROFILES[app][tier][variant]
        score_set = None  # the guide profile already carries the right French score set
        qdef = "movie" if app == "radarr" else "series"

    guide_qp = data_manager.get_quality_profile_by_id(profile_id)
    if not guide_qp:
        raise ValueError(f"Profil TRaSH introuvable ({profile_id}) : mettez les données à jour")
    profile_name = guide_qp["name"]
    groups = {gid: {"select_all": True, "assign_scores_to": [{"name": profile_name}]} for gid in ANIME_GROUPS[app]} if anime else {}
    effective_set = score_set or guide_qp.get("score_set") or "default"

    scores = {LANGUAGE_CFS[app][key]: s for key, s in language_cf_scores(ranking).items()}
    if anime:
        for tid in ANIME_EXTRA_CFS[app]:
            trash_scores = (data_manager.get_cf_by_id(tid) or {}).get("trash_scores") or {}
            scores[tid] = trash_scores.get(effective_set, trash_scores.get("default", 0))
    for codec, accepted in (("x265", accept_x265), ("av1", accept_av1)):
        if accepted:
            scores.update({tid: 0 for tid in CODEC_CFS[app][codec]})

    custom_formats = [
        {"trash_ids": [tid], "assign_scores_to": [{"name": profile_name, "score": score}]}
        for tid, score in scores.items()
    ]
    return {
        "qdef": qdef,
        "profile_trash_id": profile_id,
        "profile_name": profile_name,
        "score_set": score_set,
        "cf_groups": groups,
        "custom_formats": custom_formats,
    }


def describe(ranking: list) -> str:
    """Human summary, e.g. 'MULTi (VO + VF) > VF seule > VOSTFR — refusé : VO sans sous-titres FR'."""
    refused = [LANGUAGES[l] for l in LANGUAGES if l not in ranking]
    text = " > ".join(LANGUAGES[l] for l in ranking) or "aucune langue"
    return text + (f"  —  refusé : {', '.join(refused)}" if refused else "")
