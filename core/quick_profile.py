"""
Quick profile builder: turns simple choices (content, quality, TRaSH language variant, accepted criteria)
into a Recyclarr v8 instance setup. Profiles, variants (score sets), CF groups and scores all come from the
TRaSH Guides data downloaded at startup: nothing is computed here, so new or re-scored entries just show up.

Language logic (checked against Radarr/Sonarr LanguageParser): "VOSTFR" is NOT parsed as French,
so a VOSTFR release looks like plain VO (original audio) and only the VOSTFR title CF tells them apart.
Each language's net score in a variant, read from the guide:
    MULTi  (original + French audio) = Language: Original + French
    VF     (French audio only)       = Language: Not Original
    VOSTFR (original audio + FR subs)= Language: Not French + VOSTFR
    VO     (original audio only)     = Language: Not French
"""
import re

from core.resolver import auto_groups, group_includes, resolve

LANGUAGES = {"multi": "MULTi", "vf": "VF", "vo": "VO", "vostfr": "VOSTFR"}

# Display names of the TRaSH score sets; a new TRaSH variant shows under its own name
VARIANT_LABELS = {
    "french-multi-vf": "MULTi, sinon VF",
    "french-multi-vo": "MULTi, sinon VO",
    "french-vostfr": "VOSTFR, sinon VO",
    "french-anime-multi": "MULTi",
    "french-anime-vostfr": "VOSTFR",
}

# TRaSH custom format names carrying the language logic above
LANGUAGE_CF_NAMES = {
    "orig_french": "Language: Original + French",
    "not_original": "Language: Not Original",
    "not_french": "Language: Not French",
    "vostfr": "VOSTFR",
}

# Recyclarr quality_definition types (Recyclarr schema values, not guide data)
QDEF = {"radarr": "movie", "sonarr": "series"}


def split_name(name: str):
    """'[French MULTi.VF] HD Bluray + WEB' -> ('French MULTi.VF', 'HD Bluray + WEB')."""
    m = re.match(r"\[(.+?)\]\s*(.*)", name)
    return (m.group(1), m.group(2)) if m else ("", name)


def profile_tiers(dm, app: str, anime: bool) -> dict:
    """{tier label: {score_set: profile trash_id}} for TRaSH French profiles, or [Anime] profiles."""
    tiers = {}
    for p in dm.get_quality_profiles_for_app(app):
        tag, rest = split_name(p["name"])
        score_set = p.get("score_set") or "default"
        if (anime and tag == "Anime") or (not anime and score_set.startswith("french-")):
            tiers.setdefault(rest, {})[score_set] = p["trash_id"]
    return tiers


def _score_sets(dm, app: str, prefix: str) -> list:
    return sorted({k for cf in dm.get_custom_formats_for_app(app) for k in (cf.get("trash_scores") or {}) if k.startswith(prefix)})


def _language_cfs(dm, app: str) -> dict:
    by_name = {cf["name"]: cf for cf in dm.get_custom_formats_for_app(app)}
    missing = [n for n in LANGUAGE_CF_NAMES.values() if n not in by_name]
    if missing:
        raise ValueError(f"CF TRaSH introuvables ({', '.join(missing)}) : mettez les données à jour")
    return {role: by_name[name] for role, name in LANGUAGE_CF_NAMES.items()}


def variants(dm, app: str, anime: bool, tier: str) -> list:
    """TRaSH language variants (score sets) of a quality tier."""
    if anime:
        return _score_sets(dm, app, "french-anime")
    return sorted(profile_tiers(dm, app, False).get(tier, {}))


def _base(dm, app: str, anime: bool, tier: str, variant: str) -> dict:
    """Guide profile + score set + extra CF groups for these choices (before user overrides)."""
    tiers = profile_tiers(dm, app, anime).get(tier)
    if not tiers:
        raise ValueError(f"Palier « {tier} » introuvable dans les profils TRaSH : mettez les données à jour")
    if variant not in variants(dm, app, anime, tier):
        raise ValueError(f"Variante « {variant} » introuvable dans les données TRaSH : mettez les données à jour")
    profile_id = next(iter(tiers.values())) if anime else tiers[variant]
    score_set = variant
    guide_qp = dm.get_quality_profile_by_id(profile_id)

    groups = []
    if anime and score_set:
        # Groups the guide scores for this score set but does not auto-sync for the [Anime] profile
        scores = {cf["trash_id"]: cf.get("trash_scores") or {} for cf in dm.get_custom_formats_for_app(app)}
        auto = set(auto_groups(dm, app, [profile_id]))
        groups = [g["trash_id"] for g in dm.get_includes_by_type(app, "custom-formats")
                  if g["trash_id"] not in auto
                  and any(score_set in scores.get(cf["trash_id"], {}) for cf in g["content"]["custom_formats"])]
    return {
        "qdef": "anime" if anime else QDEF[app],
        "profile_trash_id": profile_id,
        "profile_name": guide_qp["name"],
        # Guide profiles already carry their French set; anime ones need the French anime set
        "score_set": score_set if anime else None,
        "cf_groups": groups,
    }


def group_add_options(dm, app: str, group_id: str, profiles: list) -> dict:
    """
    Options Recyclarr needs for an added CF group to actually apply to these profiles.
    profiles: [(name, trash_id or "", score_set)]. A group only scores the profiles in its include list
    unless assign_scores_to is given, and syncs nothing when it has no required/default CF unless selected.
    """
    group = dm.get_include_data(app, group_id)
    if not group or "content" not in group:
        return {}
    options = {}
    if not any(t and group_includes(group, t) for _, t, _ in profiles):
        options["assign_scores_to"] = [{"name": name} for name, _, _ in profiles]
    cfs = group["content"]["custom_formats"]
    if not any(cf.get("required") or cf.get("default") for cf in cfs):
        sets = {s for _, _, s in profiles if s and s != "default"}
        relevant = set()
        for score_set in sets:
            relevant |= family_cfs(dm, app, score_set.split("-")[0])
        relevant |= {cf["trash_id"] for cf in cfs
                     if sets & set((dm.get_cf_by_id(cf["trash_id"]) or {}).get("trash_scores") or {})}
        chosen = [cf["trash_id"] for cf in cfs if cf["trash_id"] in relevant]
        # Only what the guide uses for these profiles' language family, else the whole group
        if chosen and len(chosen) < len(cfs):
            options["select"] = chosen
        else:
            options["select_all"] = True
    return options


def family_cfs(dm, app: str, family: str) -> set:
    """CFs TRaSH uses in the guide profiles of a score-set family (e.g. 'french' -> French profiles + their groups)."""
    cache = dm.__dict__.setdefault("_family_cfs", {})
    if (app, family) not in cache:
        found = set()
        for p in dm.get_quality_profiles_for_app(app):
            if (p.get("score_set") or "").startswith(family):
                (_, resolved), = resolve({"quality_profiles": [{"trash_id": p["trash_id"]}]}, app, dm).items()
                found |= set(resolved["cfs"])
        cache[(app, family)] = found
    return cache[(app, family)]


def _instance(base: dict, app: str, dm, custom_formats=None) -> dict:
    profiles = [(base["profile_name"], base["profile_trash_id"], base["score_set"] or
                 dm.get_quality_profile_by_id(base["profile_trash_id"]).get("score_set"))]
    qp = {"trash_id": base["profile_trash_id"]}
    if base["score_set"]:
        qp["score_set"] = base["score_set"]
    inst = {"quality_profiles": [qp], "custom_formats": custom_formats or []}
    if base["cf_groups"]:
        inst["custom_format_groups"] = {"add": [{"trash_id": g, **group_add_options(dm, app, g, profiles)}
                                                for g in base["cf_groups"]]}
    return inst


def rejected_criteria(dm, app: str, anime: bool, tier: str, variant: str) -> list:
    """[(trash_id, name, score)] the guide rejects (negative score) in this profile, language CFs excluded."""
    base = _base(dm, app, anime, tier, variant)
    (_, profile), = resolve(_instance(base, app, dm), app, dm).items()
    language = {cf["trash_id"] for cf in _language_cfs(dm, app).values()}
    rows = [(tid, (dm.get_cf_by_id(tid) or {}).get("name", tid), score)
            for tid, score in profile["cfs"].items() if score < 0 and tid not in language]
    return sorted(rows, key=lambda r: r[1].lower())


def build_quick_profile(dm, app: str, anime: bool, tier: str, variant: str, accepted=()) -> dict:
    """Returns {qdef, profile_trash_id, profile_name, score_set, cf_groups [ids], custom_formats (YAML-shaped)}.
    Scores are the guide's. accepted: trash_ids of guide-rejected criteria the user accepts (score 0), e.g. x265 or AV1."""
    plan = _base(dm, app, anime, tier, variant)
    plan["custom_formats"] = [
        {"trash_ids": [tid], "assign_scores_to": [{"name": plan["profile_name"], "score": 0}]}
        for tid in accepted
    ]
    return plan


def describe(dm, app: str, anime: bool, tier: str, variant: str) -> str:
    """What this variant does with each language, read from the guide's scores."""
    (_, profile), = resolve(_instance(_base(dm, app, anime, tier, variant), app, dm), app, dm).items()
    cfs = _language_cfs(dm, app)
    score = {role: (cf.get("trash_scores") or {}).get(variant, 0) for role, cf in cfs.items()}
    net = {"multi": score["orig_french"], "vf": score["not_original"], "vo": score["not_french"],
           "vostfr": score["not_french"] + score["vostfr"]}
    top = max(net.values())
    parts = {"Préférée": [], "Acceptée": [], "Acceptée si le groupe est reconnu": [], "Refusée": []}
    for lang, value in net.items():
        if value < 0:
            parts["Refusée"].append(LANGUAGES[lang])
        elif value == top:
            parts["Préférée"].append(LANGUAGES[lang])
        elif value < profile["min_score"]:
            parts["Acceptée si le groupe est reconnu"].append(LANGUAGES[lang])
        else:
            parts["Acceptée"].append(LANGUAGES[lang])
    return " — ".join(f"{label} : {', '.join(langs)}" for label, langs in parts.items() if langs)
