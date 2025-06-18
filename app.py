import streamlit as st
import math
import matplotlib.pyplot as plt

# --- 0. Global Simulation Parameters ---
TIME_STEP = 0.05
DEBUG_MODE = False

# --- 1. Data Definitions for Items ---
ITEM_STATS = {
    "Rabadon's Deathcap": {"ap": 130, "passive_ap_multiplier": 0.30},
    "Shadowflame": {"ap": 110, "flat_mpen": 15, "amp_threshold_percent": 0.40, "amp_value": 1.20},
    "Sorcerer's Shoes": {"flat_mpen": 12},
    "Hextech Rocketbelt": {"ap": 70},
    "Void Staff": {"ap": 90, "percent_mpen": 0.40},
    "Banshee's Veil": {"ap": 105},
    "Zhonya's Hourglass": {"ap": 105},
    "Liandry's Torment": {"ap": 60, "burn_percent_max_hp": 0.01, "burn_tick_interval": 0.5, "burn_initial_delay": 0.15, "amp_trigger_delay": 0.10, "amp_tier_1_relative_time": 1.00, "amp_tier_2_relative_time": 2.00, "amp_level_1_value": 1.02, "amp_level_2_value": 1.04, "amp_level_3_value": 1.06, "extension_duration_after_combo": 2.65},
    "Needlessly Large Rod": {"ap": 65},
    "Spellslingers Shoes": {"flat_mpen": 18, "percent_mpen": 0.07},
    "Blasting Wand": {"ap": 45},
    "Cryptbloom": {"ap": 75, "percent_mpen": 0.30},
    "Blighting Jewel": {"ap": 25, "percent_mpen": 0.13},
    "Haunting Guise": {"ap": 30, "amp_trigger_delay": 0.10, "amp_tier_1_relative_time": 1.00, "amp_tier_2_relative_time": 2.00, "amp_level_1_value": 1.02, "amp_level_2_value": 1.04, "amp_level_3_value": 1.06},
    "Amplifying Tome": {"ap": 20},
    "Hextech Alternator": {"ap": 45, "proc_damage": 65},
    "Fated Ashes": {"ap": 30, "burn_damage": 2.5, "burn_tick_interval": 0.5, "burn_initial_delay": 0.15, "extension_duration_after_combo": 2.65}
}

# --- 2. Fiddlesticks Ability Data ---
ABILITY_DATA = {
    "E_Reap": {"base_damages": {1: 70, 2: 105, 3: 140, 4: 175, 5: 210}, "ap_ratio": 0.50, "cast_time": 0.4},
    "W_Drain": {"base_tick_damages": {1: 15, 2: 22.5, 3: 30, 4: 37.5, 5: 45}, "ap_ratio_tick": 0.10, "missing_health_percents": {1: 0.12, 2: 0.145, 3: 0.17, 4: 0.195, 5: 0.22}, "total_damage_ticks": 8, "channel_duration": 2, "cast_time": 0.25},
    "Q_Terrify": {"base_health_percents": {1: 0.04, 2: 0.045, 3: 0.05, 4: 0.055, 5: 0.06}, "ap_ratio_per_100_ap": 0.03, "feared_multiplier": 2, "cast_time": 0.35},
    "R_Crowstorm": {"base_tick_damages": {1: 37.5, 2: 62.5, 3: 87.5}, "ap_ratio_tick": 0.125, "total_ticks": 20, "channel_duration": 4.75, "cast_time": 0.0}
}

# --- 3. Magic Damage Calculation Helper Functions ---
def calculate_magic_damage_reduction(effective_mr):
    if effective_mr >= 0: return effective_mr / (100 + effective_mr)
    else: return 1 - (100 / (100 - effective_mr))

def calculate_effective_mr(enemy_mr, flat_mpen, percent_mpen):
    effective_mr_after_percent_pen = enemy_mr * (1 - percent_mpen)
    return max(0, effective_mr_after_percent_pen - flat_mpen)

# --- 4. Function to Aggregate Stats from Items ---
def get_stats_from_items(item_list):
    total_ap, total_flat_mpen = 18, 0
    flags = {name: False for name in ["rabadons", "liandrys", "shadowflame", "void_staff", "spellslingers_shoes", "cryptbloom", "blighting_jewel", "haunting_guise", "alternator", "fated_ashes"]}
    for item_name in item_list:
        if item_name in ITEM_STATS:
            stats = ITEM_STATS[item_name]
            total_ap += stats.get("ap", 0)
            total_flat_mpen += stats.get("flat_mpen", 0)
            if item_name == "Rabadon's Deathcap": flags["rabadons"] = True
            if item_name == "Liandry's Torment": flags["liandrys"] = True
            if item_name == "Shadowflame": flags["shadowflame"] = True
            if item_name == "Void Staff": flags["void_staff"] = True
            if item_name == "Spellslingers Shoes": flags["spellslingers_shoes"] = True
            if item_name == "Cryptbloom": flags["cryptbloom"] = True
            if item_name == "Blighting Jewel": flags["blighting_jewel"] = True
            if item_name == "Haunting Guise": flags["haunting_guise"] = True
            if item_name == "Hextech Alternator": flags["alternator"] = True
            if item_name == "Fated Ashes": flags["fated_ashes"] = True
    mpen_multiplier = 1.0
    if flags["void_staff"]: mpen_multiplier *= (1 - ITEM_STATS["Void Staff"]["percent_mpen"])
    if flags["spellslingers_shoes"]: mpen_multiplier *= (1 - ITEM_STATS["Spellslingers Shoes"]["percent_mpen"])
    if flags["cryptbloom"]: mpen_multiplier *= (1 - ITEM_STATS["Cryptbloom"]["percent_mpen"])
    if flags["blighting_jewel"]: mpen_multiplier *= (1 - ITEM_STATS["Blighting Jewel"]["percent_mpen"])
    total_percent_mpen = 1 - mpen_multiplier
    if flags["rabadons"]: total_ap *= (1 + ITEM_STATS["Rabadon's Deathcap"]["passive_ap_multiplier"])
    return {
        "total_ap": total_ap, "total_flat_mpen": total_flat_mpen, "total_percent_mpen": total_percent_mpen,
        "has_liandrys": flags["liandrys"], "has_shadowflame": flags["shadowflame"], 
        "has_haunting_guise": flags["haunting_guise"], "has_alternator": flags["alternator"],
        "has_fated_ashes": flags["fated_ashes"]
    }

# --- 5. Fiddlesticks Ability & Item Damage Calculation Functions ---
def calculate_fiddlesticks_e_damage(e_ability_level, total_ap, mpen_flat, mpen_perc, mr):
    e_data = ABILITY_DATA["E_Reap"]
    if e_ability_level not in e_data["base_damages"]: return 0
    raw_damage = e_data["base_damages"][e_ability_level] + (total_ap * e_data["ap_ratio"])
    reduction = calculate_magic_damage_reduction(calculate_effective_mr(mr, mpen_flat, mpen_perc))
    return raw_damage * (1 - reduction)

def calculate_fiddlesticks_w_tick_damage(w_ability_level, current_hp, max_hp, total_ap, mpen_flat, mpen_perc, mr, is_final, ap_ratio_tick):
    w_data = ABILITY_DATA["W_Drain"]
    if w_ability_level not in w_data["base_tick_damages"]: return 0
    reduction = calculate_magic_damage_reduction(calculate_effective_mr(mr, mpen_flat, mpen_perc))
    raw_tick_damage = w_data["base_tick_damages"][w_ability_level] + (total_ap * ap_ratio_tick) # Use passed-in ratio
    if is_final:
        hp_after_tick = current_hp - (raw_tick_damage * (1 - reduction))
        raw_tick_damage += max(0, max_hp - hp_after_tick) * w_data["missing_health_percents"][w_ability_level]
    return raw_tick_damage * (1 - reduction)

def calculate_fiddlesticks_q_damage(q_ability_level, current_hp, max_hp, total_ap, mpen_flat, mpen_perc, mr, is_feared):
    q_data = ABILITY_DATA["Q_Terrify"]
    if q_ability_level not in q_data["base_health_percents"]: return 0
    base_perc = q_data["base_health_percents"][q_ability_level]
    ap_bonus_perc = (total_ap / 100) * q_data["ap_ratio_per_100_ap"]
    raw_damage = current_hp * (base_perc + ap_bonus_perc)
    if is_feared: raw_damage *= q_data["feared_multiplier"]
    reduction = calculate_magic_damage_reduction(calculate_effective_mr(mr, mpen_flat, mpen_perc))
    return raw_damage * (1 - reduction)

def calculate_fiddlesticks_r_tick_damage(r_ability_level, total_ap, mpen_flat, mpen_perc, mr):
    r_data = ABILITY_DATA["R_Crowstorm"]
    if r_ability_level not in r_data["base_tick_damages"]: return 0
    raw_damage = r_data["base_tick_damages"][r_ability_level] + (total_ap * r_data["ap_ratio_tick"])
    reduction = calculate_magic_damage_reduction(calculate_effective_mr(mr, mpen_flat, mpen_perc))
    return raw_damage * (1 - reduction)

def calculate_liandrys_burn_damage(max_hp, mpen_flat, mpen_perc, mr):
    raw_damage = ITEM_STATS["Liandry's Torment"]["burn_percent_max_hp"] * max_hp
    reduction = calculate_magic_damage_reduction(calculate_effective_mr(mr, mpen_flat, mpen_perc))
    return raw_damage * (1 - reduction)

def calculate_alternator_proc_damage(mpen_flat, mpen_perc, mr):
    raw_damage = ITEM_STATS["Hextech Alternator"]["proc_damage"]
    reduction = calculate_magic_damage_reduction(calculate_effective_mr(mr, mpen_flat, mpen_perc))
    return raw_damage * (1 - reduction)

def calculate_fated_ashes_burn_damage(mpen_flat, mpen_perc, mr):
    raw_damage = ITEM_STATS["Fated Ashes"]["burn_damage"]
    reduction = calculate_magic_damage_reduction(calculate_effective_mr(mr, mpen_flat, mpen_perc))
    return raw_damage * (1 - reduction)

def is_at_or_past_precise_time(current_time, target_time):
    return current_time >= target_time or math.isclose(current_time, target_time, abs_tol=TIME_STEP / 2)

# --- 6. Main Simulation Function ---
def simulate_damage_over_time(combo_type, e_level, w_level, q_level, r_level,
                              enemy_max_hp, enemy_current_hp, enemy_mr,
                              total_ap, total_flat_mpen, total_percent_mpen, is_q_feared=False,
                              has_liandrys_flag=False, has_shadowflame_flag=False,
                              has_haunting_guise_flag=False, has_alternator_flag=False,
                              has_fated_ashes_flag=False,
                              w_ap_ratio_override=None,
                              total_simulation_duration_for_this_build=0.0):
    current_enemy_hp, total_damage_dealt = enemy_current_hp, 0.0
    time_points, damage_log, hp_log, damage_events = [], [], [], []
    
    # --- This is your full, untouched combo logic block ---
    if combo_type == "Just Q":
        damage_events.append((round(ABILITY_DATA["Q_Terrify"]["cast_time"], 2), 'Q', q_level, is_q_feared, False))
    elif combo_type == "Just E":
        damage_events.append((round(ABILITY_DATA["E_Reap"]["cast_time"], 2), 'E', e_level, False, False))
    elif combo_type == "Just W":
        w_start = round(ABILITY_DATA["W_Drain"]["cast_time"], 2)
        for i in range(ABILITY_DATA["W_Drain"]["total_damage_ticks"]):
            is_final = (i == ABILITY_DATA["W_Drain"]["total_damage_ticks"] - 1)
            damage_events.append((round(w_start + (i*0.25), 2), 'W', w_level, False, is_final))
    elif combo_type == "Just R":
        for i in range(ABILITY_DATA["R_Crowstorm"]["total_ticks"]):
            damage_events.append((round(i * 0.25, 2), 'R', r_level, False, False))
    elif combo_type == "R then W":
        for i in range(ABILITY_DATA["R_Crowstorm"]["total_ticks"]):
            damage_events.append((round(i * 0.25, 2), 'R', r_level, False, False))
        w_start = round(ABILITY_DATA["W_Drain"]["cast_time"], 2)
        for i in range(ABILITY_DATA["W_Drain"]["total_damage_ticks"]):
            is_final = (i == ABILITY_DATA["W_Drain"]["total_damage_ticks"] - 1)
            damage_events.append((round(w_start + (i*0.25), 2), 'W', w_level, False, is_final))
    elif combo_type == "E then W":
        e_dmg_time = round(ABILITY_DATA["E_Reap"]["cast_time"], 2)
        damage_events.append((e_dmg_time, 'E', e_level, False, False))
        w_start = round(e_dmg_time + ABILITY_DATA["W_Drain"]["cast_time"], 2)
        for i in range(ABILITY_DATA["W_Drain"]["total_damage_ticks"]):
            is_final = (i == ABILITY_DATA["W_Drain"]["total_damage_ticks"] - 1)
            damage_events.append((round(w_start + (i*0.25), 2), 'W', w_level, False, is_final))
    elif combo_type == "W then E":
        w_start = round(ABILITY_DATA["W_Drain"]["cast_time"], 2)
        last_w_time = 0
        for i in range(ABILITY_DATA["W_Drain"]["total_damage_ticks"]):
            is_final = (i == ABILITY_DATA["W_Drain"]["total_damage_ticks"] - 1)
            tick_time = round(w_start + (i*0.25), 2)
            damage_events.append((tick_time, 'W', w_level, False, is_final))
            last_w_time = tick_time
        damage_events.append((round(last_w_time + ABILITY_DATA["E_Reap"]["cast_time"], 2), 'E', e_level, False, False))
    elif combo_type == "E then Q then W":
        e_dmg_time = round(ABILITY_DATA["E_Reap"]["cast_time"], 2)
        damage_events.append((e_dmg_time, 'E', e_level, False, False))
        q_dmg_time = round(e_dmg_time + ABILITY_DATA["Q_Terrify"]["cast_time"], 2)
        damage_events.append((q_dmg_time, 'Q', q_level, is_q_feared, False))
        w_start = round(q_dmg_time + ABILITY_DATA["W_Drain"]["cast_time"], 2)
        for i in range(ABILITY_DATA["W_Drain"]["total_damage_ticks"]):
            is_final = (i == ABILITY_DATA["W_Drain"]["total_damage_ticks"] - 1)
            damage_events.append((round(w_start + (i*0.25), 2), 'W', w_level, False, is_final))
    elif combo_type == "Q then E then W":
        q_dmg_time = round(ABILITY_DATA["Q_Terrify"]["cast_time"], 2)
        damage_events.append((q_dmg_time, 'Q', q_level, is_q_feared, False))
        e_dmg_time = round(q_dmg_time + ABILITY_DATA["E_Reap"]["cast_time"], 2)
        damage_events.append((e_dmg_time, 'E', e_level, False, False))
        w_start = round(e_dmg_time + ABILITY_DATA["W_Drain"]["cast_time"], 2)
        for i in range(ABILITY_DATA["W_Drain"]["total_damage_ticks"]):
            is_final = (i == ABILITY_DATA["W_Drain"]["total_damage_ticks"] - 1)
            damage_events.append((round(w_start + (i*0.25), 2), 'W', w_level, False, is_final))
    elif combo_type == "R then Q then E then W (Normal) Combo":
        for i in range(int(2.75 / 0.25) + 1): damage_events.append((round(i*0.25, 2), 'R', r_level, False, False))
        damage_events.append((round(ABILITY_DATA["Q_Terrify"]["cast_time"], 2), 'Q', q_level, is_q_feared, False))
        damage_events.append((round(0.35 + ABILITY_DATA["E_Reap"]["cast_time"], 2), 'E', e_level, False, False))
        w_start = round(0.75 + ABILITY_DATA["W_Drain"]["cast_time"], 2)
        for i in range(ABILITY_DATA["W_Drain"]["total_damage_ticks"]):
            is_final = (i == ABILITY_DATA["W_Drain"]["total_damage_ticks"] - 1)
            damage_events.append((round(w_start + (i*0.25), 2), 'W', w_level, False, is_final))
    elif combo_type == "R then Q then E then W Layered Combo":
        for i in range(int(4.00 / 0.25) + 1): damage_events.append((round(i*0.25, 2), 'R', r_level, False, False))
        damage_events.append((round(ABILITY_DATA["Q_Terrify"]["cast_time"], 2), 'Q', q_level, is_q_feared, False))
        damage_events.append((round(1.60 + ABILITY_DATA["E_Reap"]["cast_time"], 2), 'E', e_level, False, False))
        w_start = round(2.00 + ABILITY_DATA["W_Drain"]["cast_time"], 2)
        for i in range(ABILITY_DATA["W_Drain"]["total_damage_ticks"]):
            is_final = (i == ABILITY_DATA["W_Drain"]["total_damage_ticks"] - 1)
            damage_events.append((round(w_start+(i*0.25), 2), 'W', w_level, False, is_final))
    
    damage_events.sort(key=lambda x: x[0])
    
    if has_alternator_flag:
        first_damage_time = next((event[0] for event in damage_events if event[1] in ['Q','E','W','R']), -1)
        if first_damage_time != -1:
            damage_events.append((first_damage_time, 'ALTERNATOR_PROC', 0, False, False)); damage_events.sort(key=lambda x: x[0])

    first_actual_damage_time = damage_events[0][0] if damage_events else 0.0
    if has_liandrys_flag or has_haunting_guise_flag:
        amp_data = ITEM_STATS["Liandry's Torment"]
        amp_vals = [1.0, 1.0, 1.0]
        if has_liandrys_flag: amp_vals = [v*amp_data[k] for v,k in zip(amp_vals, ["amp_level_1_value","amp_level_2_value","amp_level_3_value"])]
        if has_haunting_guise_flag: amp_vals = [v*amp_data[k] for v,k in zip(amp_vals, ["amp_level_1_value","amp_level_2_value","amp_level_3_value"])]
        trigger_time = round(first_actual_damage_time + amp_data["amp_trigger_delay"], 2)
        damage_events.append((round(trigger_time-0.01,2), 'AMP_CHANGE', amp_vals[0], False, False))
        damage_events.append((round(trigger_time+amp_data["amp_tier_1_relative_time"]-0.01,2), 'AMP_CHANGE', amp_vals[1], False, False))
        damage_events.append((round(trigger_time+amp_data["amp_tier_2_relative_time"]-0.01,2), 'AMP_CHANGE', amp_vals[2], False, False))

    if has_liandrys_flag:
        liandrys = ITEM_STATS["Liandry's Torment"]
        burn_start_time = round(first_actual_damage_time + liandrys["burn_initial_delay"], 2)
        num_burns = math.floor((total_simulation_duration_for_this_build - burn_start_time) / liandrys["burn_tick_interval"])
        if num_burns >= 0:
            for i in range(num_burns+1):
                tick_time = round(burn_start_time+(i*liandrys["burn_tick_interval"]), 2)
                if tick_time <= total_simulation_duration_for_this_build: damage_events.append((tick_time, 'LIANDRYS_BURN', 0, False, False))
    if has_fated_ashes_flag:
        fated = ITEM_STATS["Fated Ashes"]
        burn_start_time = round(first_actual_damage_time + fated["burn_initial_delay"], 2)
        num_burns = math.floor((total_simulation_duration_for_this_build - burn_start_time) / fated["burn_tick_interval"])
        if num_burns >= 0:
            for i in range(num_burns + 1):
                tick_time = round(burn_start_time + (i * fated["burn_tick_interval"]), 2)
                if tick_time <= total_simulation_duration_for_this_build: damage_events.append((tick_time, 'FATED_ASHES_BURN', 0, False, False))

    damage_events.sort(key=lambda x: x[0])
    
    max_event_time = damage_events[-1][0] if damage_events else 0.0
    sim_loop_duration = max(total_simulation_duration_for_this_build, max_event_time) + TIME_STEP
    current_event_index, global_amp, shadowflame_amp = 0, 1.0, 1.0
    for step in range(int(sim_loop_duration/TIME_STEP)+1):
        current_time = round(step*TIME_STEP, 2)
        if has_shadowflame_flag:
            shadowflame_amp = ITEM_STATS["Shadowflame"]["amp_value"] if current_enemy_hp <= (ITEM_STATS["Shadowflame"]["amp_threshold_percent"] * enemy_max_hp) else 1.0
        while current_event_index < len(damage_events) and is_at_or_past_precise_time(current_time, damage_events[current_event_index][0]):
            _, e_type, val, is_feared, is_final = damage_events[current_event_index]
            raw_dmg = 0.0
            
            w_ratio_to_use = w_ap_ratio_override if w_ap_ratio_override is not None else ABILITY_DATA['W_Drain']['ap_ratio_tick']

            if e_type == 'AMP_CHANGE': global_amp = val
            elif e_type == 'E': raw_dmg = calculate_fiddlesticks_e_damage(val, total_ap, total_flat_mpen, total_percent_mpen, enemy_mr)
            elif e_type == 'Q': raw_dmg = calculate_fiddlesticks_q_damage(val, current_enemy_hp, enemy_max_hp, total_ap, total_flat_mpen, total_percent_mpen, enemy_mr, is_feared)
            elif e_type == 'W': raw_dmg = calculate_fiddlesticks_w_tick_damage(val, current_enemy_hp, enemy_max_hp, total_ap, total_flat_mpen, total_percent_mpen, enemy_mr, is_final, w_ratio_to_use)
            elif e_type == 'R': raw_dmg = calculate_fiddlesticks_r_tick_damage(val, total_ap, total_flat_mpen, total_percent_mpen, enemy_mr)
            elif e_type == 'LIANDRYS_BURN': raw_dmg = calculate_liandrys_burn_damage(enemy_max_hp, total_flat_mpen, total_percent_mpen, enemy_mr)
            elif e_type == 'ALTERNATOR_PROC': raw_dmg = calculate_alternator_proc_damage(total_flat_mpen, total_percent_mpen, enemy_mr)
            elif e_type == 'FATED_ASHES_BURN': raw_dmg = calculate_fated_ashes_burn_damage(total_flat_mpen, total_percent_mpen, enemy_mr)
            
            if raw_dmg > 0:
                final_damage = raw_dmg * global_amp * shadowflame_amp
                total_damage_dealt += final_damage
                current_enemy_hp = max(0, current_enemy_hp - final_damage)
            current_event_index += 1
        time_points.append(current_time); damage_log.append(total_damage_dealt); hp_log.append(current_enemy_hp)
    return total_damage_dealt, current_enemy_hp, time_points, damage_log, hp_log

# This function is no longer cached
def run_and_get_results(items, q, w, e, r, max_hp, mr, combo, feared, w_ratio_override=None):
    item_stats = get_stats_from_items(items)
    base_duration = 0.0
    if combo == "Just Q": base_duration = ABILITY_DATA["Q_Terrify"]["cast_time"]
    elif combo == "Just W": base_duration = ABILITY_DATA["W_Drain"]["channel_duration"]
    elif combo == "Just E": base_duration = ABILITY_DATA["E_Reap"]["cast_time"]
    elif combo == "Just R": base_duration = ABILITY_DATA["R_Crowstorm"]["channel_duration"]
    elif combo == "R then W": base_duration = ABILITY_DATA["R_Crowstorm"]["channel_duration"]
    elif combo == "E then W": base_duration = ABILITY_DATA["W_Drain"]["channel_duration"] + ABILITY_DATA["E_Reap"]["cast_time"]
    elif combo == "W then E": base_duration = ABILITY_DATA["W_Drain"]["channel_duration"] + ABILITY_DATA["E_Reap"]["cast_time"]
    elif combo == "E then Q then W": base_duration = ABILITY_DATA["E_Reap"]["cast_time"] + ABILITY_DATA["Q_Terrify"]["cast_time"] + ABILITY_DATA["W_Drain"]["channel_duration"]
    elif combo == "Q then E then W": base_duration = ABILITY_DATA["Q_Terrify"]["cast_time"] + ABILITY_DATA["E_Reap"]["cast_time"] + ABILITY_DATA["W_Drain"]["channel_duration"]
    elif combo == "R then Q then E then W (Normal) Combo": base_duration = 2.75
    elif combo == "R then Q then E then W Layered Combo": base_duration = 4.00
    
    sim_duration = base_duration
    if item_stats["has_liandrys"] or item_stats["has_fated_ashes"]:
        sim_duration += ITEM_STATS["Liandry's Torment"]["extension_duration_after_combo"]

    total_damage, final_hp, time_points, damage_log, hp_log = simulate_damage_over_time(
        combo, e, w, q, r, max_hp, max_hp, mr,
        item_stats["total_ap"], item_stats["total_flat_mpen"], item_stats["total_percent_mpen"],
        feared, item_stats["has_liandrys"], item_stats["has_shadowflame"],
        item_stats["has_haunting_guise"], item_stats["has_alternator"], 
        item_stats["has_fated_ashes"], w_ratio_override, sim_duration
    )
    dps = total_damage / sim_duration if sim_duration > 0 else 0
    mr_values = list(range(0, 201, 5))
    damage_vs_mr = []
    for mr_val in mr_values:
        total_damage_at_mr, _, _, _, _ = simulate_damage_over_time(
            combo, e, w, q, r, max_hp, max_hp, mr_val,
            item_stats["total_ap"], item_stats["total_flat_mpen"], item_stats["total_percent_mpen"],
            feared, item_stats["has_liandrys"], item_stats["has_shadowflame"],
            item_stats["has_haunting_guise"], item_stats["has_alternator"],
            item_stats["has_fated_ashes"], w_ratio_override, sim_duration
        )
        damage_vs_mr.append(total_damage_at_mr)

    return {
        "build_name": ", ".join(items) if items else "No Items",
        "total_damage": total_damage, "final_hp": final_hp, "dps": dps,
        "time_points": time_points, "damage_log": damage_log,
        "mr_values": mr_values, "damage_vs_mr": damage_vs_mr,
        "reported_duration": sim_duration
    }

# --- 7. Streamlit Web Application ---
st.set_page_config(layout="wide")
st.title("Fiddlesticks Damage Simulator")

if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = []

available_items = sorted(list(ITEM_STATS.keys()))
combo_options = {'1':"Just Q",'2':"Just W",'3':"Just E",'4':"Just R",'5':"R then W",'6':"E then W",'7':"W then E",'8':"E then Q then W",'9':"Q then E then W",'10':"R then Q then E then W (Normal) Combo",'11':"R then Q then E then W Layered Combo"}

with st.sidebar:
    st.header("Configuration")
    chosen_item_names = st.multiselect("Select Items:", available_items, default=["Sorcerer's Shoes", "Liandry's Torment", "Zhonya's Hourglass"])
    q_level = st.slider("Q Level", 1, 5, 5)
    w_level = st.slider("W Level", 1, 5, 5)
    e_level = st.slider("E Level", 1, 5, 5)
    r_level = st.slider("R Level", 1, 3, 3)
    enemy_max_hp_input = st.number_input("Enemy Max HP", min_value=100, value=3000, step=50)
    enemy_mr_input = st.number_input("Enemy Magic Resist", min_value=0, value=100, step=5)
    selected_combo = st.selectbox("Choose a Combo:", list(combo_options.values()), index=10)
    is_q_feared_input = st.checkbox("Is target feared by Q?", value=True)
    st.divider()
    compare_w_buff = st.checkbox("Compare W Buff (10% vs 11.25% AP Ratio)")

st.header("Actions")
btn_col1, btn_col2, btn_col3 = st.columns(3)
simulate_button = btn_col1.button("Simulate Current Build", use_container_width=True)
add_button = btn_col2.button("Add Build to Comparison", use_container_width=True, type="primary")
clear_button = btn_col3.button("Clear Comparison Data", use_container_width=True)

if clear_button:
    st.session_state.comparison_results = []
    st.info("Comparison data cleared.")

if simulate_button or add_button:
    results_to_process = []
    with st.spinner("Calculating..."):
        base_results = run_and_get_results(
            chosen_item_names, q_level, w_level, e_level, r_level, 
            enemy_max_hp_input, enemy_mr_input, selected_combo, is_q_feared_input,
            w_ratio_override=0.10
        )
        results_to_process.append(base_results)
        
        if compare_w_buff:
            buffed_results = run_and_get_results(
                chosen_item_names, q_level, w_level, e_level, r_level, 
                enemy_max_hp_input, enemy_mr_input, selected_combo, is_q_feared_input,
                w_ratio_override=0.1125
            )
            results_to_process.append(buffed_results)
    
    if simulate_button:
        st.subheader(f"Preview for: {chosen_item_names}")
        for i, result in enumerate(results_to_process):
            w_ratio_label = "10% (Base)" if i == 0 else "11.25% (Buffed)"
            if not compare_w_buff: w_ratio_label = "Current"
            
            st.write(f"---")
            st.write(f"**Results for W Ratio: {w_ratio_label}**")
            res_col1, res_col2, res_col3 = st.columns(3)
            res_col1.metric("Total Damage", f"{result['total_damage']:.0f}")
            res_col2.metric("Final HP", f"{result['final_hp']:.0f}")
            res_col3.metric("DPS", f"{result['dps']:.2f}")

    if add_button:
        for i, result in enumerate(results_to_process):
            w_ratio_label = "10%" if i == 0 else "11.25%"
            if not compare_w_buff and len(results_to_process) == 1:
                 result['build_name'] = f"{result['build_name']}"
            else:
                result['build_name'] = f"{result['build_name']} (W: {w_ratio_label})"
            st.session_state.comparison_results.append(result)
        st.success(f"Added build to comparison!")

if st.session_state.comparison_results:
    st.header("Build Comparison Graphs")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 9))
    
    max_duration = 0
    for result in st.session_state.comparison_results:
        ax1.plot(result["time_points"], result["damage_log"], label=f'{result["build_name"]} ({result["total_damage"]:.0f} dmg)', marker='o', markersize=2)
        if result["reported_duration"] > max_duration: max_duration = result["reported_duration"]
    ax1.set_title("Damage Over Time Comparison")
    ax1.set_xlabel("Time (s)"); ax1.set_ylabel("Total Damage"); ax1.grid(True); ax1.legend(fontsize='x-small'); ax1.set_xlim(left=0, right=max_duration); ax1.set_ylim(bottom=0)
    
    if st.session_state.comparison_results:
        mr_values = st.session_state.comparison_results[0]["mr_values"]
        for result in st.session_state.comparison_results:
            ax2.plot(mr_values, result["damage_vs_mr"], label=result["build_name"], marker='s', markersize=2)
        ax2.set_title("Total Damage vs. Enemy Magic Resist Comparison")
        ax2.set_xlabel("Enemy Magic Resist (MR)"); ax2.set_ylabel("Total Damage Dealt"); ax2.grid(True); ax2.legend(fontsize='x-small'); ax2.set_xlim(left=0); ax2.set_ylim(bottom=0)
    
    fig.tight_layout(pad=3.0)
    st.pyplot(fig)
else:
    st.info("Configure a build and click 'Add to Comparison' to see the graphs.")