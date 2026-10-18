"""
Quick profile builder: turns simple preferences (content, quality, language order, accepted criteria)
into a Recyclarr v8 instance setup. Everything is detected from the TRaSH Guides data downloaded at
startup (profiles, quality tiers, score sets, language CFs, CF groups, scores), so new or re-scored
TRaSH entries show up without code changes.

Language logic (checked against Radarr/Sonarr LanguageParser): "VOSTFR" is NOT parsed as French,
so a VOSTFR release looks like plain VO (original audio) and only the VOSTFR title CF tells them apart.
Each language "bucket" ends up with this net score:
    MULTi  (original + French audio) = Language: Original + French
    VF     (French audio only)       = Language: Not Original
    VOSTFR (original audio + FR subs)= Language: Not French + VOSTFR
    VO     (original audio only)     = Language: Not French
"""
import re

from core.resolver import auto_groups, group_includes, resolve

LANGUAGES = {
    "multi": "MULTi (VO + VF)",
    "vf": "VF seule",
    "vostfr": "VOSTFR",
    "vo": "VO sans sous-titres FR",
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


def _pick_set(sets, ranking: list):
    """Score set matching the preferred language: VOSTFR-first, else MULTi (VF fallback or VO fallback)."""
    top = ranking[0] if ranking else None
    wanted = ["vostfr"] if top in ("vostfr", "vo") else (["multi-vf", "multi"] if "vf" in ranking else ["multi-vo", "multi"])
    for key in wanted:
        match = [s for s in sets if key in s]
        if match:
            return match[0]
    return sorted(sets)[0] if sets else None


def _language_cfs(dm, app: str) -> dict:
    by_name = {cf["name"]: cf for cf in dm.get_custom_formats_for_app(app)}
    missing = [n for n in LANGUAGE_CF_NAMES.values() if n not in by_name]
    if missing:
        raise ValueError(f"CF TRaSH introuvables ({', '.join(missing)}) : mettez les données à jour")
    return {role: by_name[name] for role, name in LANGUAGE_CF_NAMES.items()}


def guide_steps(dm, app: str, score_set: str):
    """(step, reject) read from the guide: MULTi bonus of the score set and the language rejection score."""
    cfs = _language_cfs(dm, app)
    multi = cfs["orig_french"].get("trash_scores") or {}
    step = multi.get(score_set) or 0
    if step <= 0:  # VOSTFR-first sets don't reward MULTi: reuse the guide's MULTi bonus from the other sets
        step = max([v for v in multi.values() if v > 0], default=500)
    # Rejection score the French guide uses for these CFs (other languages' sets, e.g. German -35000, ignored)
    reject = min((v for cf in cfs.values() for k, v in (cf.get("trash_scores") or {}).items()
                  if k == score_set or k.startswith("french")), default=0)
    return step, (reject if reject < 0 else -10000)


def language_cf_scores(ranking: list, step: int = 500, reject: int = -10000) -> dict:
    """ranking: accepted languages, best first. Returns the score of each language CF role."""
    if not ranking:
        raise ValueError("Au moins une langue doit être acceptée")
    net = {lang: reject for lang in LANGUAGES}
    for i, lang in enumerate(ranking):
        net[lang] = (len(ranking) - 1 - i) * step
    return {
        "orig_french": net["multi"],
        "not_original": net["vf"],
        "not_french": net["vo"],
        "vostfr": net["vostfr"] - net["vo"],
    }


def _base(dm, app: str, anime: bool, tier: str, ranking: list) -> dict:
    """Guide profile + score set + extra CF groups for these preferences (before user overrides)."""
    variants = profile_tiers(dm, app, anime).get(tier)
    if not variants:
        raise ValueError(f"Palier « {tier} » introuvable dans les profils TRaSH : mettez les données à jour")
    if anime:
        profile_id = next(iter(variants.values()))
        score_set = _pick_set(_score_sets(dm, app, "french-anime"), ranking)
    else:
        score_set = _pick_set(list(variants), ranking)
        profile_id = variants[score_set]
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


def rejected_criteria(dm, app: str, anime: bool, tier: str, ranking: list) -> list:
    """[(trash_id, name, score)] the guide rejects (negative score) in this profile, language CFs excluded."""
    base = _base(dm, app, anime, tier, ranking)
    (_, profile), = resolve(_instance(base, app, dm), app, dm).items()
    language = {cf["trash_id"] for cf in _language_cfs(dm, app).values()}
    rows = [(tid, (dm.get_cf_by_id(tid) or {}).get("name", tid), score)
            for tid, score in profile["cfs"].items() if score < 0 and tid not in language]
    return sorted(rows, key=lambda r: r[1].lower())


def build_quick_profile(dm, app: str, anime: bool, tier: str, ranking: list, accepted=()) -> dict:
    """Returns {qdef, profile_trash_id, profile_name, score_set, cf_groups [ids], custom_formats (YAML-shaped)}.
    accepted: trash_ids of guide-rejected criteria to accept (score 0), e.g. x265 or AV1."""
    if not ranking:
        raise ValueError("Au moins une langue doit être acceptée")
    plan = _base(dm, app, anime, tier, ranking)
    effective_set = plan["score_set"] or dm.get_quality_profile_by_id(plan["profile_trash_id"]).get("score_set") or "default"
    step, reject = guide_steps(dm, app, effective_set)
    cfs = _language_cfs(dm, app)
    scores = {cfs[role]["trash_id"]: s for role, s in language_cf_scores(ranking, step, reject).items()}
    scores.update({tid: 0 for tid in accepted})
    plan["custom_formats"] = [
        {"trash_ids": [tid], "assign_scores_to": [{"name": plan["profile_name"], "score": score}]}
        for tid, score in scores.items()
    ]
    return plan


def describe(ranking: list) -> str:
    """Human summary, e.g. 'MULTi (VO + VF) > VF seule > VOSTFR — refusé : VO sans sous-titres FR'."""
    refused = [LANGUAGES[l] for l in LANGUAGES if l not in ranking]
    text = " > ".join(LANGUAGES[l] for l in ranking) or "aucune langue"
    return text + (f"  —  refusé : {', '.join(refused)}" if refused else "")
