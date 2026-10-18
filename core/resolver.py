"""
Offline resolution of how Recyclarr resolves an instance config into the quality profiles
Radarr/Sonarr end up with (qualities, cutoff, scores). Follows recyclarr.dev semantics:
- guide-backed profile (trash_id): TRaSH profile JSON + YAML overrides, CF scores from its score_set
- CF groups: default groups auto-sync to profiles in their `include` list; `add` groups target
  `assign_scores_to` or, when omitted, only the profiles the group includes
- group CFs: required + default (- exclude) + select (or select_all)
- explicit `custom_formats` scores win over guide scores
- v7 configs: `include: - template:` fragments are merged in (pass them via `includes`)
"""


def _guide_score(cf: dict, score_set: str) -> int:
    scores = (cf or {}).get("trash_scores") or {}
    return scores.get(score_set or "default", scores.get("default", 0))


def _leaves(qualities: list) -> list:
    out = []
    for q in qualities:
        out += q.get("qualities") or [q["name"]]
    return out


def group_cfs(group: dict, select=None, exclude=None, select_all=False) -> list:
    exclude = set(exclude or [])
    chosen = []
    for cf in group["content"]["custom_formats"]:
        tid = cf["trash_id"]
        if cf.get("required") or (cf.get("default") and tid not in exclude) \
                or tid in (select or []) or (select_all and tid not in exclude):
            chosen.append(tid)
    return chosen


def group_includes(group: dict, profile_trash_id: str) -> bool:
    qp = group["content"].get("quality_profiles") or {}
    if "include" in qp:
        return profile_trash_id in qp["include"].values()
    return profile_trash_id not in (qp.get("exclude") or {}).values()


def auto_groups(dm, app: str, profile_trash_ids) -> list:
    """trash_ids of the default CF groups Recyclarr auto-syncs for these guide-backed profiles."""
    return [g["trash_id"] for g in dm.get_includes_by_type(app, "custom-formats")
            if g.get("default") and any(group_includes(g, t) for t in profile_trash_ids)]


def resolve(instance: dict, app: str, dm, includes: list = None) -> dict:
    """Returns {profile_name: {qualities, cutoff, upgrade, until_score, min_score, score_set, cfs{tid: score}}}."""
    instance = dict(instance)
    for frag in includes or []:  # v7 include templates
        for key in ("quality_profiles", "custom_formats"):
            instance[key] = list(instance.get(key) or []) + list(frag.get(key) or [])

    profiles, trash_of = {}, {}
    for qp in instance.get("quality_profiles") or []:
        guide = dm.get_quality_profile_by_id(qp["trash_id"]) if qp.get("trash_id") else None
        if guide:
            p = {
                "qualities": [i["name"] for i in guide["items"] if i.get("allowed")],
                "leaves": sorted(_leaves([{"name": i["name"], "qualities": i.get("items")} for i in guide["items"] if i.get("allowed")])),
                "cutoff": guide.get("cutoff"), "upgrade": guide.get("upgradeAllowed"),
                "until_score": guide.get("cutoffFormatScore"), "min_score": guide.get("minFormatScore", 0),
                "score_set": guide.get("score_set") or "default", "cfs": {},
            }
            p["guide_items"] = list(guide.get("formatItems", {}).values())
            name = qp.get("name") or guide["name"]
            trash_of[name] = qp["trash_id"]
        else:
            p = {"qualities": [], "leaves": [], "cutoff": None, "upgrade": False, "until_score": None,
                 "min_score": 0, "score_set": "default", "cfs": {}, "guide_items": []}
            name = qp["name"]
        if qp.get("qualities"):
            p["qualities"] = [q["name"] for q in qp["qualities"] if q.get("enabled", True)]
            p["leaves"] = sorted(_leaves([q for q in qp["qualities"] if q.get("enabled", True)]))
        up = qp.get("upgrade") or {}
        p["upgrade"] = up.get("allowed", p["upgrade"])
        p["cutoff"] = up.get("until_quality", p["cutoff"])
        p["until_score"] = up.get("until_score", p["until_score"])
        p["min_score"] = qp.get("min_format_score", p["min_score"])
        p["score_set"] = qp.get("score_set", p["score_set"])
        profiles[name] = p

    def add(name, tid):
        p = profiles[name]
        p["cfs"][tid] = _guide_score(dm.get_cf_by_id(tid), p["score_set"])

    # Guide-backed profiles: their own formatItems + auto-synced default groups
    groups_cfg = instance.get("custom_format_groups") or {}
    skip = set(groups_cfg.get("skip") or [])
    all_groups = [g for g in dm.get_includes_by_type(app, "custom-formats")]
    for name, p in profiles.items():
        for tid in p.pop("guide_items"):
            add(name, tid)
        if name in trash_of:
            for g in all_groups:
                if g.get("default") and g["trash_id"] not in skip and group_includes(g, trash_of[name]):
                    for tid in group_cfs(g):
                        add(name, tid)

    for entry in groups_cfg.get("add") or []:
        g = dm.get_include_data(app, entry["trash_id"])
        targets = _targets(entry.get("assign_scores_to"), profiles, trash_of) if entry.get("assign_scores_to") \
            else [n for n in trash_of if group_includes(g, trash_of[n])]
        for name in targets:
            for tid in group_cfs(g, entry.get("select"), entry.get("exclude"), entry.get("select_all")):
                add(name, tid)

    for entry in instance.get("custom_formats") or []:
        assigns = entry.get("assign_scores_to") or entry.get("quality_profiles") or []  # v7 key
        for a in assigns:
            for name in _targets([a], profiles, trash_of):
                for tid in entry["trash_ids"]:
                    score = a.get("score", entry.get("score"))
                    profiles[name]["cfs"][tid] = score if score is not None else \
                        _guide_score(dm.get_cf_by_id(tid), profiles[name]["score_set"])
    return profiles


def _targets(assigns, profiles, trash_of) -> list:
    names = []
    for a in assigns:
        if a.get("name") in profiles:
            names.append(a["name"])
        elif a.get("trash_id"):
            names += [n for n, t in trash_of.items() if t == a["trash_id"]]
    return names
