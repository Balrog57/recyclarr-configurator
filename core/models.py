from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class QualityProfileItem:
    """Représente une qualité dans un profil (ex: Bluray-1080p)"""
    name: str
    qualities: List[str] = field(default_factory=list) # Pour les groupes

@dataclass
class QualityProfile:
    """Représente un profil complet (ex: FR-MULTi-VF-UHD)"""
    name: str
    upgrade_allowed: bool = False
    upgrade_until: str = ""
    min_format_score: int = 0
    score_set: str = "french-multi-vf"
    items: List[QualityProfileItem] = field(default_factory=list) # La structure arborescente

@dataclass
class CustomFormatAssignment:
    """Lien entre un CF, son score, et les profils où il s'applique"""
    trash_id: str
    name: str              # Pour l'affichage UI
    description: str       # Pour le tooltip
    score: int             # DEPRECATED/Global score
    default_score: int     # Le score par défaut (référence)
    profiles: List[str]    # DEPRECATED
    # Structure v2 for per-profile scores: [{"name": "ProfileName", "score": 100}, ...]
    profile_scores: List[Dict] = field(default_factory=list)

@dataclass
class InstanceConfig:
    """Configuration d'une instance (Radarr ou Sonarr)"""
    name: str              # ex: fr-films
    base_url: str
    api_key: str
    # Les includes granulaires
    includes_quality_defs: List[str] = field(default_factory=list)
    includes_profiles: List[str] = field(default_factory=list)
    includes_cfs: List[str] = field(default_factory=list)
    # Les créations manuelles
    custom_profiles: List[QualityProfile] = field(default_factory=list)
    active_cfs: List[CustomFormatAssignment] = field(default_factory=list)

@dataclass
class RecyclarrConfiguration:
    """Configuration complète Recyclarr."""
    radarr_instances: List[InstanceConfig] = field(default_factory=list)
    sonarr_instances: List[InstanceConfig] = field(default_factory=list)
