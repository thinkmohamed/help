"""Target taxonomy — the 5 detection classes."""
from __future__ import annotations

# Order is fixed; ML models depend on this ordering
TARGETS: list[str] = [
    "underground_voids",
    "buried_metals",
    "ancient_ruins",
    "modern_excavations",
    "groundwater",
]

TARGET_LABELS: dict[str, dict[str, str]] = {
    "underground_voids": {"ar": "فراغات تحت الأرض", "en": "Underground voids", "color": "#7c3aed"},
    "buried_metals": {"ar": "معادن مدفونة", "en": "Buried metals", "color": "#dc2626"},
    "ancient_ruins": {"ar": "آثار قديمة", "en": "Ancient ruins", "color": "#d97706"},
    "modern_excavations": {"ar": "حفر/تنقيب حديث", "en": "Modern excavations", "color": "#0891b2"},
    "groundwater": {"ar": "مياه جوفية", "en": "Groundwater", "color": "#2563eb"},
}
