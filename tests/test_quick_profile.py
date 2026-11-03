import copy
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from core.data_manager import DataManager
from core.models import RecyclarrConfiguration
from core.resolver import resolve
from core.yaml_generator import YAMLGenerator
from core import quick_profile as qp


@pytest.fixture(scope="module")
def dm():
    manager = DataManager()
    assert manager.load_data()
    return manager


def bucket_scores(ranking, step=500, reject=-10000):
    """Net language score per release type, from how Radarr/Sonarr match the language CFs."""
    s = qp.language_cf_scores(ranking, step, reject)
    return {
        "multi": s["orig_french"],               # Original + French audio
        "vf": s["not_original"],                 # French audio only
        "vostfr": s["not_french"] + s["vostfr"],  # original audio, VOSTFR in title
        "vo": s["not_french"],                   # original audio only
    }


def test_language_order_films():
    net = bucket_scores(["multi", "vf", "vostfr"])
    assert net["multi"] > net["vf"] > net["vostfr"] >= 0
    assert net["vo"] <= -10000


def test_language_order_anime_no_vf():
    net = bucket_scores(["multi", "vostfr"])
    assert net["multi"] > net["vostfr"] >= 0
    assert net["vf"] <= -10000 and net["vo"] <= -10000


def test_no_language_rejected():
    with pytest.raises(ValueError):
        qp.language_cf_scores([])


def test_profiles_and_scores_detected_from_data(dm):
    for app in ("radarr", "sonarr"):
        tiers = qp.profile_tiers(dm, app, anime=False)
        assert tiers, f"no French TRaSH profile detected for {app}"
        for variants in tiers.values():
            assert {"french-multi-vf", "french-multi-vo", "french-vostfr"} <= set(variants)
        assert qp.profile_tiers(dm, app, anime=True)


def test_wizard_follows_guide_score_changes(dm):
    """If TRaSH changes a profile's until score or refuses a new criterion, the wizard follows without code changes."""
    changed = copy.deepcopy(dm)
    profile_id = qp.profile_tiers(changed, "radarr", False)["HD Bluray + WEB"]["french-multi-vf"]
    changed.get_quality_profile_by_id(profile_id)["cutoffFormatScore"] = 20000
    plan = qp.build_quick_profile(changed, "radarr", False, "HD Bluray + WEB", ["multi", "vf", "vostfr"])
    scores = {changed.get_cf_by_id(e["trash_ids"][0])["name"]: e["assign_scores_to"][0]["score"] for e in plan["custom_formats"]}
    assert scores["Language: Original + French"] == 40000 and scores["Language: Not Original"] == 20000
    assert plan["until_score"] == 60000


def test_rejected_criteria_lists_codecs(dm):
    names = {name for _, name, _ in qp.rejected_criteria(dm, "radarr", False, "HD Bluray + WEB", ["multi", "vf", "vostfr"])}
    assert {"x265 (HD)", "AV1"} <= names
    assert not names & set(qp.LANGUAGE_CF_NAMES.values())


def _accept(dm, app, anime, tier, ranking, wanted=("x265", "AV1")):
    return [tid for tid, name, _ in qp.rejected_criteria(dm, app, anime, tier, ranking) if any(w in name for w in wanted)]


def _wizard_instance(dm, tmp_path, app_type, anime, tier, ranking, name="x"):
    from PySide6.QtWidgets import QApplication
    from main_gui_app import InstanceEditor
    app = QApplication.instance() or QApplication([])
    ed = InstanceEditor(dm, app_type)
    ed.config.name = name
    ed.apply_quick_profile(anime, tier, ranking, _accept(dm, app_type, anime, tier, ranking))
    for tab in (1, 2, 3, 0):  # visiting acts must not lose anything
        ed.tabs.setCurrentIndex(tab)
    return ed.get_config()


def _export(cfg, tmp_path, fname):
    gen = YAMLGenerator()
    return gen.load_yaml(gen.generate_config(cfg, filename=str(tmp_path / fname)))


def test_three_instances_end_to_end(dm, tmp_path):
    """Films (Radarr), Séries (Sonarr), Animés (Sonarr): MULTi > VF > VOSTFR, anime without VF, x265 + AV1 OK."""
    cfg = RecyclarrConfiguration(
        radarr_instances=[_wizard_instance(dm, tmp_path, "radarr", False, "HD Bluray + WEB", ["multi", "vf", "vostfr"], "films")],
        sonarr_instances=[_wizard_instance(dm, tmp_path, "sonarr", False, "HD Bluray + WEB (1080p)", ["multi", "vf", "vostfr"], "series"),
                          _wizard_instance(dm, tmp_path, "sonarr", True, "Remux-1080p", ["multi", "vostfr"], "animes")],
    )
    out = _export(cfg, tmp_path, "quick.yml")
    assert out["radarr"]["films"]["quality_definition"]["type"] == "movie"
    assert out["radarr"]["films"]["quality_profiles"][0]["name"].startswith("[French MULTi.VF]")
    animes = out["sonarr"]["animes"]
    assert animes["quality_definition"]["type"] == "anime"
    assert animes["quality_profiles"][0]["score_set"] == "french-anime-multi"
    # Groups the guide scores for French anime; their effect is checked in test_wizard_anime_keeps_french_release_groups
    assert animes["custom_format_groups"]["add"]

    for app_type, inst in (("radarr", out["radarr"]["films"]), ("sonarr", out["sonarr"]["series"]), ("sonarr", animes)):
        (_, profile), = resolve(inst, app_type, dm).items()
        names = {(dm.get_cf_by_id(t) or {}).get("name", t): s for t, s in profile["cfs"].items()}
        assert names.get("AV1") == 0
        assert all(s == 0 for n, s in names.items() if n.startswith("x265"))


@pytest.mark.parametrize("app_type,template,tier", [
    ("radarr", "french-multi-vf-hd-bluray-web", "HD Bluray + WEB"),
    ("sonarr", "french-multi-vf-bluray-web-1080p", "HD Bluray + WEB (1080p)"),
])
def test_wizard_matches_official_template_except_overrides(dm, tmp_path, app_type, template, tier):
    """Effective profile (Recyclarr resolution) = official v8 template + only the language/codec overrides."""
    official = list(dm.get_template_by_name(app_type, template)["content"][app_type].values())[0]
    (_, ref), = resolve(official, app_type, dm).items()
    cfg = RecyclarrConfiguration(**{f"{app_type}_instances": [_wizard_instance(dm, tmp_path, app_type, False, tier, ["multi", "vf", "vostfr"])]})
    (_, got), = resolve(_export(cfg, tmp_path, "w.yml")[app_type]["x"], app_type, dm).items()

    overridden = {t for e in qp.build_quick_profile(dm, app_type, False, tier, ["multi", "vf", "vostfr"],
                                                    _accept(dm, app_type, False, tier, ["multi", "vf", "vostfr"]))["custom_formats"]
                  for t in e["trash_ids"]}
    for key in ("leaves", "cutoff", "min_score", "score_set", "upgrade"):
        assert got[key] == ref[key], key
    assert {t: s for t, s in got["cfs"].items() if t not in overridden} == {t: s for t, s in ref["cfs"].items() if t not in overridden}


def test_wizard_anime_keeps_french_release_groups(dm, tmp_path):
    """Former v7 French anime recipe: FR anime / FR release group tiers scored, FastSUB and FR LQ rejected."""
    cfg = RecyclarrConfiguration(sonarr_instances=[_wizard_instance(dm, tmp_path, "sonarr", True, "Remux-1080p", ["multi", "vostfr"])])
    (_, got), = resolve(_export(cfg, tmp_path, "a.yml")["sonarr"]["x"], "sonarr", dm).items()
    by_name = {(dm.get_cf_by_id(t) or {}).get("name", t): s for t, s in got["cfs"].items()}
    for tier in ("FR Anime Tier 01", "FR Anime Tier 02", "FR Anime Tier 03", "FR Anime FanSub", "FR Scene Groups", "FR WEB Tier 01"):
        assert by_name.get(tier, 0) > 0, tier
    for unwanted in ("FastSUB", "FR LQ"):
        assert by_name.get(unwanted, 0) <= -10000, unwanted
    assert "Language: Not English" not in by_name  # select, not select_all, on language groups


@pytest.mark.parametrize("ranking", [["vo"], ["vo", "vostfr"], ["vostfr"], ["vostfr", "vo"], ["multi", "vf", "vostfr"], ["multi", "vf", "vostfr", "vo"]])
def test_language_order_beats_any_release_without_undoing_refusals(dm, ranking):
    """Every profile: a better language beats a worse one with the best group, audio and HDR; refusals still refuse."""
    roles = {"multi": ["orig_french"], "vf": ["not_original"], "vo": ["not_french"], "vostfr": ["not_french", "vostfr"]}
    for app in ("radarr", "sonarr"):
        group_of = {cf["trash_id"]: g["name"] for g in dm.get_includes_by_type(app, "custom-formats") for cf in g["content"]["custom_formats"]}
        for anime in (False, True):
            for tier in qp.profile_tiers(dm, app, anime):
                plan = qp.build_quick_profile(dm, app, anime, tier, ranking)
                by_id = {t: e["assign_scores_to"][0]["score"] for e in plan["custom_formats"] for t in e["trash_ids"]}
                cfs = qp._language_cfs(dm, app)
                language = {cf["trash_id"] for cf in cfs.values()}
                nets = [sum(by_id[cfs[r]["trash_id"]] for r in roles[lang]) for lang in ranking]
                (_, profile), = resolve(qp._instance(plan, app, dm), app, dm).items()
                # A release matches at most one CF of a group: its best possible total outside languages
                best_by_group = {}
                for t, s in profile["cfs"].items():
                    if t not in language and s > 0:
                        key = group_of.get(t, t)
                        best_by_group[key] = max(best_by_group.get(key, 0), s)
                best_release = sum(best_by_group.values())
                context = (app, tier, ranking, nets)
                assert nets[-1] >= profile["min_score"], context
                assert all(a > b + best_release for a, b in zip(nets, nets[1:])), context
                assert nets[0] + best_release <= plan["until_score"], context
                refusals = [by_id[t] for t, s in profile["cfs"].items() if s <= qp.GUIDE_REFUSAL and t not in language]
                assert refusals and all(nets[0] + best_release + r < profile["min_score"] for r in refusals), context
