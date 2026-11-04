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


def test_profiles_and_scores_detected_from_data(dm):
    for app in ("radarr", "sonarr"):
        tiers = qp.profile_tiers(dm, app, anime=False)
        assert tiers, f"no French TRaSH profile detected for {app}"
        for variants in tiers.values():
            assert {"french-multi-vf", "french-multi-vo", "french-vostfr"} <= set(variants)
        assert qp.profile_tiers(dm, app, anime=True)


def test_wizard_writes_guide_scores_only(dm):
    """Every profile and variant: nothing overridden unless the user accepts a criterion."""
    for app in ("radarr", "sonarr"):
        for anime in (False, True):
            for tier in qp.profile_tiers(dm, app, anime):
                found = qp.variants(dm, app, anime, tier)
                assert found, (app, tier)
                for variant in found:
                    plan = qp.build_quick_profile(dm, app, anime, tier, variant)
                    assert plan["custom_formats"] == [] and dm.get_quality_profile_by_id(plan["profile_trash_id"])
                    (_, profile), = resolve(qp._instance(plan, app, dm), app, dm).items()
                    for tid, score in profile["cfs"].items():
                        scores = dm.get_cf_by_id(tid).get("trash_scores") or {}
                        assert score == scores.get(variant, scores.get("default", 0)), (app, tier, variant, tid)


def test_unknown_variant_is_refused(dm):
    with pytest.raises(ValueError):
        qp.build_quick_profile(dm, "radarr", False, "HD Bluray + WEB", "french-inconnu")


def test_describe_follows_guide_scores(dm):
    text = qp.describe(dm, "radarr", False, "HD Bluray + WEB", "french-multi-vf")
    assert text == "Préférée : MULTi — Acceptée : VF — Refusée : VO, VOSTFR"
    text = qp.describe(dm, "radarr", True, "Remux-1080p", "french-anime-vostfr")
    assert text == "Préférée : VOSTFR — Acceptée si le groupe est reconnu : VO — Refusée : MULTi, VF"


def _base_wizard(ed):
    ed.apply_quick_profile(False, "HD Bluray + WEB", "french-multi-vf")


def _base_other_guide_profile(ed):
    standard = next(p["trash_id"] for p in ed.data_manager.get_quality_profiles_for_app("radarr") if not p.get("score_set") or p["score_set"] == "default")
    ed.act1_widget.set_selected_includes([standard])
    ed.tabs.setCurrentIndex(2)


def _base_custom(ed):
    from core.models import QualityProfile, QualityProfileItem
    ed.act2_widget.profiles.append(QualityProfile(name="Mon profil", active=True, items=[QualityProfileItem("Bluray-1080p")]))
    ed.tabs.setCurrentIndex(2)


@pytest.mark.parametrize("base", [_base_wizard, _base_other_guide_profile, _base_custom])
def test_step4_adds_changes_and_removes_any_score_on_any_base(dm, tmp_path, base):
    """Whatever the starting profile, any CF can get a score, even one the profile doesn't use (5000 on AV1, on a fansub CF)."""
    from PySide6.QtWidgets import QApplication
    from main_gui_app import InstanceEditor
    QApplication.instance() or QApplication([])
    ed = InstanceEditor(dm, "radarr")
    ed.config.name = "x"
    base(ed)
    ed.tabs.setCurrentIndex(3)
    editor = ed.act3_widget
    assert editor.profiles

    def pick(name):
        item = next(editor.list_widget.item(i) for i in range(editor.list_widget.count()) if editor.list_widget.item(i).data(98) == name)
        editor.list_widget.setCurrentItem(item)
        editor.load_details(item)
        return item

    def set_score(name, value):
        item = pick(name)
        editor.profile_table.cellWidget(0, 1).layout().itemAt(0).widget().setChecked(value is not None)
        if value is not None:
            editor.profile_table.cellWidget(0, 2).setValue(value)
        return item

    def scores():
        cfg = RecyclarrConfiguration(radarr_instances=[ed.get_config()])
        (_, got), = resolve(_export(cfg, tmp_path, "s.yml")["radarr"]["x"], "radarr", dm).items()
        return {dm.get_cf_by_id(t)["name"]: s for t, s in got["cfs"].items()}

    guide = scores()
    av1 = set_score("AV1", 5000)
    fansub = set_score("FR Anime FanSub", 5000)
    assert "✎ 5000" in av1.text() and "✎ 5000" in fansub.text()
    got = scores()
    assert got["AV1"] == 5000 and got["FR Anime FanSub"] == 5000

    set_score("AV1", -300)
    assert scores()["AV1"] == -300 and "✎ -300" in av1.text()

    editor.only_mine.setChecked(True)
    assert not av1.isHidden() and all(editor.list_widget.item(i).isHidden() for i in range(editor.list_widget.count())
                                      if editor.list_widget.item(i).data(98) not in ("AV1", "FR Anime FanSub"))
    editor.only_mine.setChecked(False)

    pick("AV1")
    editor.neutralize()
    assert scores()["AV1"] == 0

    set_score("AV1", None)
    set_score("FR Anime FanSub", None)
    assert scores() == guide and av1.text() == "AV1"


def test_rejected_criteria_lists_codecs(dm):
    names = {name for _, name, _ in qp.rejected_criteria(dm, "radarr", False, "HD Bluray + WEB", "french-multi-vf")}
    assert {"x265 (HD)", "AV1"} <= names
    assert not names & set(qp.LANGUAGE_CF_NAMES.values())


def _accept(dm, app, anime, tier, variant, wanted=("x265", "AV1")):
    return [tid for tid, name, _ in qp.rejected_criteria(dm, app, anime, tier, variant) if any(w in name for w in wanted)]


def _wizard_instance(dm, tmp_path, app_type, anime, tier, variant, name="x"):
    from PySide6.QtWidgets import QApplication
    from main_gui_app import InstanceEditor
    app = QApplication.instance() or QApplication([])
    ed = InstanceEditor(dm, app_type)
    ed.config.name = name
    ed.apply_quick_profile(anime, tier, variant, _accept(dm, app_type, anime, tier, variant))
    for tab in (1, 2, 3, 0):  # visiting acts must not lose anything
        ed.tabs.setCurrentIndex(tab)
    return ed.get_config()


def _export(cfg, tmp_path, fname):
    gen = YAMLGenerator()
    return gen.load_yaml(gen.generate_config(cfg, filename=str(tmp_path / fname)))


def test_three_instances_end_to_end(dm, tmp_path):
    """Films (Radarr), Séries (Sonarr), Animés (Sonarr): TRaSH variants, x265 + AV1 accepted."""
    cfg = RecyclarrConfiguration(
        radarr_instances=[_wizard_instance(dm, tmp_path, "radarr", False, "HD Bluray + WEB", "french-multi-vf", "films")],
        sonarr_instances=[_wizard_instance(dm, tmp_path, "sonarr", False, "HD Bluray + WEB (1080p)", "french-multi-vf", "series"),
                          _wizard_instance(dm, tmp_path, "sonarr", True, "Remux-1080p", "french-anime-multi", "animes")],
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
    cfg = RecyclarrConfiguration(**{f"{app_type}_instances": [_wizard_instance(dm, tmp_path, app_type, False, tier, "french-multi-vf")]})
    (_, got), = resolve(_export(cfg, tmp_path, "w.yml")[app_type]["x"], app_type, dm).items()

    overridden = {t for e in qp.build_quick_profile(dm, app_type, False, tier, "french-multi-vf",
                                                    _accept(dm, app_type, False, tier, "french-multi-vf"))["custom_formats"]
                  for t in e["trash_ids"]}
    for key in ("leaves", "cutoff", "min_score", "score_set", "upgrade"):
        assert got[key] == ref[key], key
    assert {t: s for t, s in got["cfs"].items() if t not in overridden} == {t: s for t, s in ref["cfs"].items() if t not in overridden}


def test_wizard_anime_keeps_french_release_groups(dm, tmp_path):
    """Former v7 French anime recipe: FR anime / FR release group tiers scored, FastSUB and FR LQ rejected."""
    cfg = RecyclarrConfiguration(sonarr_instances=[_wizard_instance(dm, tmp_path, "sonarr", True, "Remux-1080p", "french-anime-multi")])
    (_, got), = resolve(_export(cfg, tmp_path, "a.yml")["sonarr"]["x"], "sonarr", dm).items()
    by_name = {(dm.get_cf_by_id(t) or {}).get("name", t): s for t, s in got["cfs"].items()}
    for tier in ("FR Anime Tier 01", "FR Anime Tier 02", "FR Anime Tier 03", "FR Anime FanSub", "FR Scene Groups", "FR WEB Tier 01"):
        assert by_name.get(tier, 0) > 0, tier
    for unwanted in ("FastSUB", "FR LQ"):
        assert by_name.get(unwanted, 0) <= -10000, unwanted
    assert "Language: Not English" not in by_name  # select, not select_all, on language groups
