"""
Electronic in BEV - Basic data
Author: Matthias Roesslein - Empa
Copyright © 2025 & 2026 Empa, Matthias Roesslein

Translated from R/Quarto to Python.
"""

import pandas as pd
import numpy as np
import re
import os

# ─────────────────────────────────────────────────────────────────────────────
# 1. READ DATA
# ─────────────────────────────────────────────────────────────────────────────

filename1_input = "Data/01_VehicleElectronics.xlsx"

sheet_names = [
    "HVPowerElectronics", "Thermal", "LVPower", "Body", "Control",
    "Brakes", "Safety", "ADAS", "Infotainment", "Connectivity",
    "HMI", "HVAC", "Lighting", "Mech", "Suspension", "Driveline",
    "Networking", "Security", "Diagnostics", "DataLogging"
]

frames = []
for sheet in sheet_names:
    df = pd.read_excel(filename1_input, sheet_name=sheet)
    frames.append(df)

electronics = pd.concat(frames, ignore_index=True)

# Make column names unique (mirrors R's make.unique)
cols = list(electronics.columns)
seen = {}
unique_cols = []
for c in cols:
    if c in seen:
        seen[c] += 1
        unique_cols.append(f"{c}_{seen[c]}")
    else:
        seen[c] = 0
        unique_cols.append(c)
electronics.columns = unique_cols

# Convert PCB/PVB columns to numeric
numeric_cols = [c for c in electronics.columns if "PCB" in c or "PVB" in c]
for col in numeric_cols:
    electronics[col] = pd.to_numeric(electronics[col], errors="coerce")


# ─────────────────────────────────────────────────────────────────────────────
# 2. PCB DISTRIBUTION
# ─────────────────────────────────────────────────────────────────────────────

def map_segment_factor(value):
    """Map segment availability text to a numeric factor."""
    if pd.isna(value):
        return 0.0
    v = str(value).strip()
    if v in ("–", "-", ""):
        return 0.0
    if v == "Rare":
        return 0.25
    if v == "Opt":
        return 0.5
    if v == "Std":
        return 1.0
    return 0.0


electronics["AB_factor"] = electronics["A-B Segment"].apply(map_segment_factor)
electronics["CD_factor"] = electronics["C-D Segment"].apply(map_segment_factor)
electronics["EF_factor"] = electronics["E-F Segment"].apply(map_segment_factor)


def distribute_pcbs_by_segment(s_min, s_max, m_min, m_max, l_min, l_max, factor):
    """Multiply base PCB counts by the segment factor."""
    def safe(x):
        x = pd.to_numeric(x, errors="coerce")
        return 0.0 if pd.isna(x) else float(x)

    if pd.isna(factor) or factor == 0:
        return {k: 0.0 for k in ("s_min", "s_max", "m_min", "m_max", "l_min", "l_max")}

    return {
        "s_min": safe(s_min) * factor,
        "s_max": safe(s_max) * factor,
        "m_min": safe(m_min) * factor,
        "m_max": safe(m_max) * factor,
        "l_min": safe(l_min) * factor,
        "l_max": safe(l_max) * factor,
    }


def apply_pcb_distribution(row, prefix, factor_col):
    result = distribute_pcbs_by_segment(
        row.get("Small_PCB_min"),  row.get("Small_PCB_max"),
        row.get("Medium_PCB_min"), row.get("Medium_PCB_max"),
        row.get("Large_PCB_min"),  row.get("Large_PCB_max"),
        row[factor_col]
    )
    return pd.Series({
        f"{prefix}_Small_min":  result["s_min"],
        f"{prefix}_Small_max":  result["s_max"],
        f"{prefix}_Medium_min": result["m_min"],
        f"{prefix}_Medium_max": result["m_max"],
        f"{prefix}_Large_min":  result["l_min"],
        f"{prefix}_Large_max":  result["l_max"],
    })


for prefix, factor_col in [("AB", "AB_factor"), ("CD", "CD_factor"), ("EF", "EF_factor")]:
    dist = electronics.apply(apply_pcb_distribution, axis=1, prefix=prefix, factor_col=factor_col)
    electronics = pd.concat([electronics, dist], axis=1)


# ─────────────────────────────────────────────────────────────────────────────
# 3. PCB CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────

def classify_pcb_category(domain, component):
    """
    Classify each component into one of:
    PE_HVS, BMS, VCC, ITC, SSS, MLIS
    """
    domain    = "" if pd.isna(domain)    else str(domain).strip()
    component = "" if pd.isna(component) else str(component).strip()
    dl  = domain.lower()
    cl  = component.lower()
    comb = f"{dl} {cl}"

    def m(pattern, text=comb):
        return bool(re.search(pattern, text))

    # BMS
    if m(r"battery management system|bms|master bms|slave bms"):
        return "BMS"
    if re.search(r"^bms|battery.*management", cl):
        return "BMS"

    # PE_HVS
    if re.match(r"^hv\s*power", dl):
        return "PE_HVS"
    if m(r"traction inverter|main.*inverter|rear.*inverter|front.*inverter|e-axle.*inverter"):
        return "PE_HVS"
    if m(r"traction battery|traction.*pack|high voltage battery|hv.*battery"):
        return "PE_HVS"
    if m(r"dc/dc|dc-dc converter|hv-lv.*converter|high voltage.*converter"):
        return "PE_HVS"
    if m(r"onboard charger|obc|charging inlet|charge port|charging.*control|charging.*system"):
        return "PE_HVS"
    if m(r"dc fast.*charge|fast.*charge.*interface|external.*charge|rapid.*charge"):
        return "PE_HVS"
    if m(r"hv junction|hv distribution|hv.*pdu|hv.*power distribution"):
        return "PE_HVS"
    if m(r"isolation monitoring|hv.*fuse|hv.*contactor|hv.*interlock|hv.*relay"):
        return "PE_HVS"
    if m(r"power.*modul|powermodul|power.*unit"):
        return "PE_HVS"
    if m(r"12v.*battery|12 v.*battery|auxiliary battery|auxilary battery|aux.*battery"):
        return "PE_HVS"
    if m(r"front.*power distribution|rear.*power distribution|power distribution unit"):
        return "PE_HVS"
    if re.match(r"^thermal$", dl):
        return "PE_HVS"
    if m(r"thermal.*management|coolant.*pump|thermal.*ecu|thermal.*system|thermal.*control"):
        return "PE_HVS"
    if m(r"battery.*cooling|inverter.*cooling|motor.*cooling|hv.*cooling"):
        return "PE_HVS"
    if m(r"chiller|heat exchanger|cooling.*valve|thermal.*valve"):
        return "PE_HVS"
    if m(r"heater|ptc.*heater|battery.*heater|cabin.*heater|coolant.*heater|high voltage.*heater"):
        return "PE_HVS"
    if m(r"high voltage|hv.*system"):
        return "PE_HVS"
    if m(r"seat heater"):
        return "PE_HVS"

    # MLIS
    if re.match(r"^lighting$", dl):
        return "MLIS"
    if m(r"headlamp|headlight|lamp.*control|led.*driver"):
        return "MLIS"
    if m(r"adaptive.*light|matrix.*light|matrix.*beam"):
        return "MLIS"
    if m(r"interior.*lighting|ambient.*light|illumination"):
        return "MLIS"
    if m(r"tail.*light|brake.*light|turn.*signal|fog.*light"):
        return "MLIS"

    # ITC
    if re.match(r"^infotainment$", dl):
        return "ITC"
    if m(r"head unit|infotainment.*system|center.*display|multimedia"):
        return "ITC"
    if m(r"audio.*amplifier|radio|tuner|speaker"):
        return "ITC"
    if re.match(r"^connectivity$", dl):
        return "ITC"
    if m(r"telematics|tcu|modem|wifi|bluetooth|v2x|antenna"):
        return "ITC"
    if re.match(r"^hmi$", dl):
        return "ITC"
    if m(r"instrument cluster|digital.*cluster|head-up display|hud"):
        return "ITC"
    if m(r"touchscreen|display.*controller"):
        return "ITC"
    if re.match(r"^networking$", dl):
        return "ITC"
    if m(r"gateway|ethernet.*switch|can.*gateway|network.*controller"):
        return "ITC"
    if re.match(r"^diagnostics$", dl):
        return "ITC"
    if m(r"obd|diagnostic"):
        return "ITC"
    if re.match(r"^data\s*logging$", dl):
        return "ITC"
    if m(r"data.*logging|data.*recorder"):
        return "ITC"
    if m(r"keyless.*entry|passive.*entry"):
        return "ITC"
    if m(r"event data recorder"):
        return "ITC"

    # SSS
    if re.match(r"^adas$", dl):
        return "SSS"
    if m(r"camera|radar|lidar|ultrasonic.*sensor|parking.*sensor"):
        return "SSS"
    if m(r"parking assist|driver monitoring"):
        return "SSS"
    if re.match(r"^safety$", dl):
        return "SSS"
    if m(r"airbag|restraint|occupant.*detection|crash.*sensor"):
        return "SSS"
    if re.match(r"^security$", dl):
        return "SSS"
    if m(r"alarm|anti-theft|immobilizer"):
        return "SSS"
    if re.match(r"^brakes$", dl):
        return "SSS"
    if m(r"abs|esc|esp|brake.*control|ebcm|brake-by-wire"):
        return "SSS"

    # VCC (explicit + fallback)
    if m(r"adas.*ecu|adas.*controller|adas.*domain|adas.*computer|fusion.*ecu|automated driving"):
        return "VCC"
    if m(r"controller|control unit|ecu|computer"):
        return "VCC"
    if re.match(r"^control$", dl):
        return "VCC"
    if m(r"vehicle control unit|vcu"):
        return "VCC"
    if m(r"domain controller|zone controller"):
        return "VCC"
    if re.match(r"^body$", dl):
        return "VCC"
    if m(r"body control|bcm|door.*control|window.*control"):
        return "VCC"
    if m(r"seat.*control|roof.*module|sunroof"):
        return "VCC"
    if m(r"wiper|washer|horn"):
        return "VCC"
    if re.match(r"^hvac$", dl):
        return "VCC"
    if m(r"hvac|climate.*control|blower|fan.*control|compressor.*control|air.*conditioning"):
        return "VCC"
    if re.match(r"^suspension$", dl):
        return "VCC"
    if m(r"suspension.*control|damper.*control"):
        return "VCC"
    if re.match(r"^driveline$", dl):
        return "VCC"
    if m(r"transmission.*control|gearbox.*control"):
        return "VCC"
    if re.match(r"^lv\s*power$", dl):
        return "VCC"
    if m(r"lv.*distribution|fuse box|junction box"):
        return "VCC"
    if m(r"steering.*control|eps|electric.*steering"):
        return "VCC"
    if re.match(r"^mech$", dl):
        return "VCC"
    if re.match(r"^steering$", dl):
        return "VCC"
    if m(r"actuator|motor(?!.*inverter)|pump(?!.*thermal)|valve(?!.*thermal)"):
        return "VCC"

    return "VCC"  # default fallback


electronics_final = electronics.copy()
electronics_final["PCB_Category"] = electronics_final.apply(
    lambda row: classify_pcb_category(row.get("Domain"), row.get("Component")), axis=1
)

# Move PCB_Category right after "E-F Segment"
cols = list(electronics_final.columns)
ef_pos = cols.index("E-F Segment")
cols.remove("PCB_Category")
cols.insert(ef_pos + 1, "PCB_Category")
electronics_final = electronics_final[cols]

# Summary
print("\n=== CLASSIFICATION SUMMARY ===")
print(electronics_final["PCB_Category"].value_counts().reset_index()
      .rename(columns={"count": "Count"}).to_string(index=False))


# ─────────────────────────────────────────────────────────────────────────────
# 4. ELECTRIC MOTORS DISTRIBUTION
# ─────────────────────────────────────────────────────────────────────────────

def num0(series):
    """Convert to numeric; replace NaN/NaT with 0."""
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


motor_cols = [
    "StepperMotor_Small_min", "StepperMotor_Small_max",
    "DCMotor_Small_min",      "DCMotor_Small_max",
    "DCMoter_Medium_min",     "DCMoter_Medium_max",
    "AB_min", "AB_max",
    "CD_min", "CD_max",
    "EF_min", "EF_max",
]
for col in motor_cols:
    if col in electronics.columns:
        electronics[col] = num0(electronics[col])

md = electronics.copy()

# Stepper Small (override logic: if base == -1, use segment-specific column)
for seg in ("AB", "CD", "EF"):
    factor = md[f"{seg}_factor"]
    base_min = md["StepperMotor_Small_min"]
    base_max = md["StepperMotor_Small_max"]
    seg_min  = md[f"{seg}_min"]
    seg_max  = md[f"{seg}_max"]

    md[f"{seg}_StepperMotor_Small_min"] = np.where(base_min == -1, seg_min, base_min * factor)
    md[f"{seg}_StepperMotor_Small_max"] = np.where(base_max == -1, seg_max, base_max * factor)

# DC Small (always factor-based)
for seg in ("AB", "CD", "EF"):
    factor = md[f"{seg}_factor"]
    md[f"{seg}_DCMotor_Small_min"] = md["DCMotor_Small_min"] * factor
    md[f"{seg}_DCMotor_Small_max"] = md["DCMotor_Small_max"] * factor

# DC Medium (always factor-based)
for seg in ("AB", "CD", "EF"):
    factor = md[f"{seg}_factor"]
    md[f"{seg}_DCMoter_Medium_min"] = md["DCMoter_Medium_min"] * factor
    md[f"{seg}_DCMoter_Medium_max"] = md["DCMoter_Medium_max"] * factor

# Totals
for seg in ("AB", "CD", "EF"):
    md[f"{seg}_Motor_Total_min"] = (
        md[f"{seg}_StepperMotor_Small_min"] +
        md[f"{seg}_DCMotor_Small_min"] +
        md[f"{seg}_DCMoter_Medium_min"]
    )
    md[f"{seg}_Motor_Total_max"] = (
        md[f"{seg}_StepperMotor_Small_max"] +
        md[f"{seg}_DCMotor_Small_max"] +
        md[f"{seg}_DCMoter_Medium_max"]
    )

# Replace any remaining NaN with 0
numeric_md_cols = md.select_dtypes(include=[np.number]).columns
md[numeric_md_cols] = md[numeric_md_cols].fillna(0.0)

# Select relevant columns
keep_motor_cols = [
    "Domain", "Component", "Main Function", "Voltage", "Typical Location",
    "A-B Segment", "C-D Segment", "E-F Segment",
    "AB_factor", "CD_factor", "EF_factor",
    "StepperMotor_Small_min", "StepperMotor_Small_max",
    "DCMotor_Small_min",      "DCMotor_Small_max",
    "DCMoter_Medium_min",     "DCMoter_Medium_max",
    "AB_min", "AB_max", "CD_min", "CD_max", "EF_min", "EF_max",
    "AB_StepperMotor_Small_min", "AB_StepperMotor_Small_max",
    "AB_DCMotor_Small_min",      "AB_DCMotor_Small_max",
    "AB_DCMoter_Medium_min",     "AB_DCMoter_Medium_max",
    "AB_Motor_Total_min",        "AB_Motor_Total_max",
    "CD_StepperMotor_Small_min", "CD_StepperMotor_Small_max",
    "CD_DCMotor_Small_min",      "CD_DCMotor_Small_max",
    "CD_DCMoter_Medium_min",     "CD_DCMoter_Medium_max",
    "CD_Motor_Total_min",        "CD_Motor_Total_max",
    "EF_StepperMotor_Small_min", "EF_StepperMotor_Small_max",
    "EF_DCMotor_Small_min",      "EF_DCMotor_Small_max",
    "EF_DCMoter_Medium_min",     "EF_DCMoter_Medium_max",
    "EF_Motor_Total_min",        "EF_Motor_Total_max",
]
keep_motor_cols = [c for c in keep_motor_cols if c in md.columns]
motors_distribution = md[keep_motor_cols].copy()

# Keep only rows that actually have motors
motors_distribution = motors_distribution[
    (motors_distribution["AB_Motor_Total_min"] > 0) |
    (motors_distribution["AB_Motor_Total_max"] > 0) |
    (motors_distribution["CD_Motor_Total_min"] > 0) |
    (motors_distribution["CD_Motor_Total_max"] > 0) |
    (motors_distribution["EF_Motor_Total_min"] > 0) |
    (motors_distribution["EF_Motor_Total_max"] > 0)
].reset_index(drop=True)

# Summary
print("\n=== MOTOR DISTRIBUTION SUMMARY ===")
summary = pd.DataFrame({
    "MotorType": ["Stepper Small", "DC Small", "DC Medium", "TOTAL"],
    "AB_Min": [
        motors_distribution["AB_StepperMotor_Small_min"].sum(),
        motors_distribution["AB_DCMotor_Small_min"].sum(),
        motors_distribution["AB_DCMoter_Medium_min"].sum(),
        motors_distribution["AB_Motor_Total_min"].sum(),
    ],
    "AB_Max": [
        motors_distribution["AB_StepperMotor_Small_max"].sum(),
        motors_distribution["AB_DCMotor_Small_max"].sum(),
        motors_distribution["AB_DCMoter_Medium_max"].sum(),
        motors_distribution["AB_Motor_Total_max"].sum(),
    ],
    "CD_Min": [
        motors_distribution["CD_StepperMotor_Small_min"].sum(),
        motors_distribution["CD_DCMotor_Small_min"].sum(),
        motors_distribution["CD_DCMoter_Medium_min"].sum(),
        motors_distribution["CD_Motor_Total_min"].sum(),
    ],
    "CD_Max": [
        motors_distribution["CD_StepperMotor_Small_max"].sum(),
        motors_distribution["CD_DCMotor_Small_max"].sum(),
        motors_distribution["CD_DCMoter_Medium_max"].sum(),
        motors_distribution["CD_Motor_Total_max"].sum(),
    ],
    "EF_Min": [
        motors_distribution["EF_StepperMotor_Small_min"].sum(),
        motors_distribution["EF_DCMotor_Small_min"].sum(),
        motors_distribution["EF_DCMoter_Medium_min"].sum(),
        motors_distribution["EF_Motor_Total_min"].sum(),
    ],
    "EF_Max": [
        motors_distribution["EF_StepperMotor_Small_max"].sum(),
        motors_distribution["EF_DCMotor_Small_max"].sum(),
        motors_distribution["EF_DCMoter_Medium_max"].sum(),
        motors_distribution["EF_Motor_Total_max"].sum(),
    ],
})
print(summary.to_string(index=False))


# ─────────────────────────────────────────────────────────────────────────────
# 5. WRITE OUTPUT FILES
# ─────────────────────────────────────────────────────────────────────────────

os.makedirs("Data", exist_ok=True)

# --- PCB Distribution CSV ---
pcb_cols_to_keep = [
    "Domain", "Component", "Main Function", "Voltage", "Typical Location",
    "A-B Segment", "C-D Segment", "E-F Segment", "PCB_Category",
    "PCB_total_min", "PCB_total_max",
    "Small_PCB_min", "Small_PCB_max",
    "Medium_PCB_min", "Medium_PCB_max",
    "Large_PCB_min", "Large_PCB_max",
    "AB_factor", "CD_factor", "EF_factor",
    "AB_Small_min", "AB_Small_max",
    "AB_Medium_min", "AB_Medium_max",
    "AB_Large_min", "AB_Large_max",
    "CD_Small_min", "CD_Small_max",
    "CD_Medium_min", "CD_Medium_max",
    "CD_Large_min", "CD_Large_max",
    "EF_Small_min", "EF_Small_max",
    "EF_Medium_min", "EF_Medium_max",
    "EF_Large_min", "EF_Large_max",
]
pcb_cols_to_keep = [c for c in pcb_cols_to_keep if c in electronics_final.columns]

output_pcb = "Data/11_PCB_Distribution_Classified.csv"
electronics_final[pcb_cols_to_keep].to_csv(output_pcb, index=False)
print(f"\nFile saved: {output_pcb}")
print(f"Total components: {len(electronics_final)}")
print(f"Total columns: {len(pcb_cols_to_keep)}")

# --- Motor Distribution CSV ---
output_motors = "Data/12_Motor_Distribution.csv"
motors_distribution.to_csv(output_motors, index=False)
print(f"\nFile saved: {output_motors}")
print(f"Total components with motors: {len(motors_distribution)}")
print(f"Total columns: {len(motors_distribution.columns)}")