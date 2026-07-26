"""Gold-by-construction calibration cases for content scorers (Phase 3c).

Each case pairs a generated set with a reference set whose correct score is
known by construction, plus the inclusive bands each scorer kind is expected to
land in. Cases use the canonical test-case schema.

``paraphrase`` is the discriminating case: the deterministic overlap scorer
matches on string similarity and is EXPECTED to fail it, while the LLM judge
must clear it to justify its cost. Paraphrases are hand-authored rather than
model-generated, so the ground truth never depends on a model's opinion.
"""

from src.training.judge_calibration import (
    CalibrationCase,  # noqa: TC001 -- must resolve at runtime for get_type_hints()
)

# --- Reference scenarios -----------------------------------------------------

_REF_DOOR_LOCK: dict = {
    "summary_suffix": "Door locks when vehicle exceeds 20 km/h",
    "preconditions": "Vehicle stationary, all doors closed and unlocked",
    "test_steps": (
        "1. Start the engine\n"
        "2. Accelerate the vehicle to 25 km/h\n"
        "3. Observe the door lock actuators"
    ),
    "expected_result": "All four doors lock automatically once speed exceeds 20 km/h",
    "test_type": "Functional",
}

_REF_ANTI_PINCH: dict = {
    "summary_suffix": "Driver window reverses on obstruction during auto-close",
    "preconditions": "Ignition on, driver window fully open",
    "test_steps": (
        "1. Trigger auto-close on the driver window\n2. Insert a test obstacle in the window path"
    ),
    "expected_result": "Window stops and reverses direction within 100 ms of contact",
    "test_type": "Safety",
}

_REF_MIRROR_FOLD: dict = {
    "summary_suffix": "Exterior mirrors fold when vehicle is locked",
    "preconditions": "Vehicle unlocked, mirrors unfolded, ignition off",
    "test_steps": ("1. Lock the vehicle with the remote key fob\n2. Observe both exterior mirrors"),
    "expected_result": "Both exterior mirrors fold inward within 3 seconds of locking",
    "test_type": "Functional",
}

_REF_HAZARD: dict = {
    "summary_suffix": "Hazard lights activate on emergency braking",
    "preconditions": "Vehicle travelling at 80 km/h on a dry surface",
    "test_steps": "1. Apply full braking force\n2. Observe the hazard indicators",
    "expected_result": (
        "Hazard lights flash automatically while deceleration exceeds the threshold"
    ),
    "test_type": "Safety",
}

# --- Paraphrases: same scenarios, deliberately different wording -------------

_PARA_DOOR_LOCK: dict = {
    "summary_suffix": "Automatic central locking engages above 20 kph",
    "preconditions": "Car at rest, every door shut and in the unlocked state",
    "test_steps": (
        "1. Switch on the powertrain\n"
        "2. Drive until the speedometer reads 25 kph\n"
        "3. Listen for the latch motors"
    ),
    "expected_result": ("Every door latches by itself as soon as the threshold speed is passed"),
    "test_type": "Functional",
}

_PARA_ANTI_PINCH: dict = {
    "summary_suffix": "Anti-pinch protection retracts the driver glass",
    "preconditions": "Power mode on, glass on the driver side lowered completely",
    "test_steps": (
        "1. Activate one-touch up on the driver side\n"
        "2. Place a blocking object into the glass travel path"
    ),
    "expected_result": (
        "Travel halts and the glass retreats no later than 100 ms after touching the object"
    ),
    "test_type": "Safety",
}

_PARA_MIRROR_FOLD: dict = {
    "summary_suffix": "Wing mirrors retract on central locking",
    "preconditions": "Doors in open state, mirrors extended, engine switched off",
    "test_steps": ("1. Press lock on the keyless remote\n2. Watch the wing mirrors on both sides"),
    "expected_result": "Each wing mirror swings inward no more than 3 seconds after lock",
    "test_type": "Functional",
}

# --- Unrelated scenarios -----------------------------------------------------

_OTHER_AIR_FILTER: dict = {
    "summary_suffix": "Cabin air filter replacement interval warning",
    "preconditions": "Odometer at 14,900 km, filter service counter active",
    "test_steps": (
        "1. Drive until the odometer reads 15,000 km\n2. Read the driver information cluster"
    ),
    "expected_result": "Cluster shows the cabin air filter service reminder",
    "test_type": "Functional",
}

_OTHER_BLUETOOTH: dict = {
    "summary_suffix": "Infotainment Bluetooth pairing with two phones",
    "preconditions": "Infotainment on, no devices paired",
    "test_steps": (
        "1. Pair the first handset\n"
        "2. Pair the second handset\n"
        "3. Play audio from the second handset"
    ),
    "expected_result": "Both handsets remain paired and audio streams from the second",
    "test_type": "Functional",
}

_OTHER_TYRE_PRESSURE: dict = {
    "summary_suffix": "Tyre pressure warning at 1.8 bar",
    "preconditions": "All tyres inflated to 2.4 bar, ignition on",
    "test_steps": (
        "1. Deflate the front left tyre to 1.8 bar\n2. Drive above 25 km/h for two minutes"
    ),
    "expected_result": "Low tyre pressure telltale illuminates for the front left wheel",
    "test_type": "Functional",
}

_THREE_REFS = [_REF_DOOR_LOCK, _REF_ANTI_PINCH, _REF_MIRROR_FOLD]

DEFAULT_CALIBRATION_CASES: tuple[CalibrationCase, ...] = (
    {
        "name": "identity",
        "description": "generated == reference (3 cases)",
        "generated": list(_THREE_REFS),
        "reference": list(_THREE_REFS),
        "expected": {
            "overlap": {"precision": (0.9, 1.0), "recall": (0.9, 1.0), "f1": (0.9, 1.0)},
            "llm": {"precision": (0.9, 1.0), "recall": (0.9, 1.0), "f1": (0.9, 1.0)},
        },
    },
    {
        "name": "disjoint",
        "description": "3 completely unrelated cases",
        "generated": [_OTHER_AIR_FILTER, _OTHER_BLUETOOTH, _OTHER_TYRE_PRESSURE],
        "reference": list(_THREE_REFS),
        "expected": {
            "overlap": {"recall": (0.0, 0.1), "f1": (0.0, 0.1)},
            "llm": {"recall": (0.0, 0.1), "f1": (0.0, 0.1)},
        },
    },
    {
        "name": "subset",
        "description": "2 of 4 reference cases, verbatim",
        "generated": [_REF_DOOR_LOCK, _REF_MIRROR_FOLD],
        "reference": [_REF_DOOR_LOCK, _REF_ANTI_PINCH, _REF_MIRROR_FOLD, _REF_HAZARD],
        "expected": {
            "overlap": {"recall": (0.4, 0.6), "precision": (0.9, 1.0)},
            "llm": {"recall": (0.4, 0.6), "precision": (0.9, 1.0)},
        },
    },
    {
        "name": "paraphrase",
        "description": "3 reference scenarios reworded — the discriminating case",
        "generated": [_PARA_DOOR_LOCK, _PARA_ANTI_PINCH, _PARA_MIRROR_FOLD],
        "reference": list(_THREE_REFS),
        "expected": {
            # Overlap matches on string similarity and is EXPECTED to miss these.
            "overlap": {"f1": (0.0, 0.35)},
            # The judge's claimed advantage — this is what Phase 3b must earn.
            "llm": {"f1": (0.7, 1.0)},
        },
    },
    {
        "name": "noise",
        "description": "all 3 reference cases verbatim plus 2 unrelated extras",
        "generated": [*_THREE_REFS, _OTHER_AIR_FILTER, _OTHER_TYRE_PRESSURE],
        "reference": list(_THREE_REFS),
        "expected": {
            "overlap": {"recall": (0.9, 1.0), "precision": (0.4, 0.8)},
            "llm": {"recall": (0.9, 1.0), "precision": (0.4, 0.8)},
        },
    },
)
