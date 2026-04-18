from __future__ import annotations

from pathlib import Path

IRACING_FOLDERS: list[str] = sorted([
    "acuraarx06gtp", "acuransxevo22gt3", "amvantageevogt3", "amvantagegt4",
    "audir8lmsevo2gt3", "audirs3lms", "audirs3lmsgen2", "bmwlmdh", "bmwm2csr",
    "bmwm4evogt4", "bmwm4gt3", "bmwm4gt4", "bmwm8gte", "c8rvettegte", "cadillacctsvr",
    "cadillacvseriesrgtp", "chevyvettez06rgt3", "crosscartn11", "dallaradw12",
    "dallarap217", "dirtmicrosprint nonwinged", "dirtmicrosprint nonwinged outlaw",
    "dirtmicrosprint winged", "dirtmicrosprint winged outlaw", "dirtministock",
    "dirtstreetstock", "dirtumpmod", "ferrari296gt3", "ferrari488gte", "ferrari499p",
    "fordgt2017", "fordmustanggt3", "fordmustanggt4", "formulair04", "formulavee",
    "hondacivictyper", "hyundaielantracn7", "hyundaivelostern", "jettatdi", "kiaoptima",
    "lamborghinievogt3", "legends dirtford34c", "legends ford34c", "legends ford34c rookie",
    "ligierjsp320", "mclaren570sgt4", "mclaren720sgt3", "mercedesamgevogt3", "mercedesamggt4",
    "ministock", "mx5 cup", "mx5 mx52016", "mx5 roadster", "porsche718gt4", "porsche963gtp",
    "porsche991rsr", "porsche9922cup", "porsche992cup", "porsche992rgt3", "protrucks pro2lite",
    "radical sr8", "raygr22", "renaultcliocup", "solstice", "solstice rookie", "specracer",
    "stockcarbrasil corolla", "stockcarbrasil cruze", "streetstock",
    "supercars chevycamarogen3", "supercars fordmustanggen3", "toyotagr86",
    "trucks silverado", "vwbeetlegrc", "vwbeetlegrc lite",
])

IRACING_FOLDERS_SET: frozenset[str] = frozenset(IRACING_FOLDERS)


def load_folders_from_scan(setups_root: Path) -> frozenset[str]:
    """Liest tatsächliche Unterordner aus setups_root als Live-Fahrzeugordner."""
    if not setups_root.is_dir():
        return IRACING_FOLDERS_SET
    try:
        found = frozenset(child.name for child in setups_root.iterdir() if child.is_dir())
    except OSError:
        return IRACING_FOLDERS_SET
    return found if found else IRACING_FOLDERS_SET
