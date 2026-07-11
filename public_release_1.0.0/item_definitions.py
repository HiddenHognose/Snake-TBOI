"""
Item definitions - 200+ non-stackable items and 20+ stackable items
"""

# Stackable items (can collect multiple times)
STACKABLE_ITEMS = [
    'health', 'damage', 'speed', 'health_up', 'damage_up', 'speed_up',
    'bullet_size', 'bullet_speed', 'fire_rate', 'knockback', 'armor', 'regen',
    'lucky', 'crit_chance', 'life_steal', 'bullet_bounce', 'magnet',
    'rapid_fire', 'mega_bullet', 'damage_boost', 'speed_boost', 'health_boost'
]

# Non-stackable items (unique, can only have one)
NON_STACKABLE_ITEMS = [
    # Multi-shot upgrades
    'double_shot', 'triple_shot', 'quad_shot', 'penta_shot', 'hexa_shot',
    'octa_shot', 'spread_shot', 'shotgun', 'burst_fire', 'volley_shot',
    
    # Special bullet types
    'piercing', 'explosive', 'homing', 'chain_lightning', 'split_shot',
    'bouncing_bullets', 'seeking_missiles', 'flame_bullets', 'ice_bullets',
    'poison_bullets', 'electric_bullets', 'acid_bullets', 'void_bullets',
    'light_bullets', 'dark_bullets', 'chaos_bullets', 'order_bullets',
    
    # Defensive items
    'shield', 'barrier', 'force_field', 'armor_plating', 'damage_reflect',
    'invincibility_frame_boost', 'damage_immunity', 'knockback_immunity',
    'status_immunity', 'shield_regen', 'barrier_burst',
    
    # Movement abilities
    'teleport', 'dash', 'blink', 'phase_shift', 'speed_boost_active',
    'wall_climb', 'double_jump', 'air_dash', 'ground_slam', 'charge',
    
    # Time manipulation
    'slow_time', 'stop_time', 'rewind', 'time_dilation', 'bullet_time',
    'haste', 'slow_enemies', 'freeze_enemies', 'stun_enemies',
    
    # Utility items
    'magnet', 'item_radar', 'enemy_radar', 'treasure_sense', 'luck_boost',
    'extra_life', 'second_chance', 'revive', 'auto_collect', 'item_duplication',
    
    # Damage modifiers
    'crit_master', 'headshot', 'weak_spot', 'vulnerability', 'damage_amplify',
    'execution', 'finisher', 'overkill', 'devastation', 'annihilation',
    
    # Special effects
    'life_steal', 'mana_steal', 'energy_steal', 'health_on_kill', 'ammo_on_kill',
    'rage_mode', 'berserker', 'frenzy', 'adrenaline', 'overdrive',
    
    # Follower upgrades
    'follower', 'follower_boost', 'follower_shield', 'follower_heal',
    'follower_damage', 'follower_speed', 'follower_armor', 'follower_regen',
    
    # Size and scale
    'giant_bullets', 'tiny_bullets', 'micro_bullets', 'macro_bullets',
    'expanding_bullets', 'shrinking_bullets', 'growing_bullets',
    
    # Pattern upgrades
    'spiral_shot', 'wave_shot', 'zigzag_shot', 'sine_shot', 'cosine_shot',
    'figure_eight', 'orbit_shot', 'boomerang', 'returning_bullets',
    
    # Elemental
    'fire_mastery', 'ice_mastery', 'lightning_mastery', 'poison_mastery',
    'acid_mastery', 'void_mastery', 'light_mastery', 'dark_mastery',
    'chaos_mastery', 'order_mastery', 'nature_mastery', 'metal_mastery',
    
    # Weapon types
    'laser_beam', 'plasma_bolt', 'energy_wave', 'shockwave', 'sonic_boom',
    'gravity_well', 'black_hole', 'white_hole', 'singularity', 'rift',
    
    # Status effects
    'burn', 'freeze', 'shock', 'poison', 'bleed', 'curse', 'charm',
    'fear', 'confusion', 'sleep', 'stun', 'slow', 'root', 'silence',
    
    # Special mechanics
    'ricochet', 'penetration', 'overpenetration', 'pierce_all', 'bounce_all',
    'split_on_hit', 'chain_on_hit', 'explode_on_hit', 'multiply_on_hit',
    
    # Power ups
    'damage_boost_active', 'speed_boost_active', 'health_boost_active',
    'crit_boost_active', 'fire_rate_boost_active', 'range_boost_active',
    
    # Unique abilities
    'phase_through_walls', 'fly', 'hover', 'glide', 'wall_jump',
    'grapple', 'hook', 'swing', 'climb', 'crawl',
    
    # Defensive abilities
    'dodge', 'parry', 'counter', 'block', 'absorb', 'redirect',
    'reflect', 'deflect', 'evade', 'sidestep', 'backstep',
    
    # Offensive abilities
    'melee_attack', 'slam', 'stomp', 'charge_attack', 'spin_attack',
    'whirlwind', 'tornado', 'cyclone', 'hurricane', 'typhoon',
    
    # Special projectiles
    'seeking_orbs', 'guided_missiles', 'smart_bombs', 'cluster_bombs',
    'napalm', 'incendiary', 'explosive_tipped', 'armor_piercing',
    
    # Buffs
    'damage_buff', 'speed_buff', 'health_buff', 'armor_buff', 'regen_buff',
    'crit_buff', 'luck_buff', 'range_buff', 'fire_rate_buff',
    
    # Debuffs on enemies
    'weaken_enemies', 'slow_enemies', 'damage_enemies', 'mark_enemies',
    'expose_enemies', 'vulnerable_enemies', 'cripple_enemies',
    
    # Resource management
    'ammo_conservation', 'energy_efficiency', 'cooldown_reduction',
    'resource_generation', 'infinite_ammo', 'no_reload',
    
    # Vision and detection
    'x_ray', 'thermal_vision', 'night_vision', 'true_sight', 'detect_all',
    'highlight_enemies', 'highlight_items', 'highlight_secrets',
    
    # Movement enhancements
    'sprint', 'sprint_boost', 'jump_boost', 'climb_boost', 'swim',
    'underwater_breathing', 'no_fall_damage', 'wall_run',
    
    # Special mechanics
    'combo_system', 'multiplier', 'streak', 'momentum', 'chain_kills',
    'overkill_bonus', 'style_points', 'execution_bonus',
    
    # Unique items
    'legendary_weapon', 'mythic_armor', 'epic_accessory', 'rare_artifact',
    'unique_trinket', 'special_relic', 'ancient_power', 'divine_blessing',
    
    # Transformation
    'transform', 'morph', 'shapeshift', 'evolve', 'ascend', 'transcend',
    
    # Summoning
    'summon_minion', 'summon_turret', 'summon_drone', 'summon_ally',
    'summon_pet', 'summon_guardian', 'summon_avatar',
    
    # Area effects
    'aoe_damage', 'aoe_heal', 'aoe_buff', 'aoe_debuff', 'aoe_clear',
    'nuke', 'meteor', 'earthquake', 'tsunami', 'volcano',
    
    # Final items
    'god_mode', 'infinite_power', 'ultimate_weapon', 'perfect_armor',
    'divine_protection', 'immortality', 'omnipotence', 'transcendence'
]

# All items combined
ALL_ITEMS = STACKABLE_ITEMS + NON_STACKABLE_ITEMS

# Item colors (will be auto-generated if not specified)
ITEM_COLORS = {
    # Stackable items (keep existing colors)
    'health': (255, 0, 0),
    'damage': (255, 200, 0),
    'speed': (0, 200, 255),
    'health_up': (255, 100, 100),
    'damage_up': (255, 220, 50),
    'speed_up': (100, 255, 255),
    'bullet_size': (255, 150, 0),
    'bullet_speed': (255, 255, 100),
    'fire_rate': (255, 0, 150),
    'knockback': (150, 150, 255),
    'armor': (200, 200, 200),
    'regen': (0, 255, 0),
    'lucky': (255, 215, 0),
    'crit_chance': (255, 200, 100),
    'life_steal': (200, 0, 100),
    'bullet_bounce': (100, 200, 255),
    'magnet': (200, 100, 255),
    'rapid_fire': (255, 0, 100),
    'mega_bullet': (255, 100, 50),
    'damage_boost': (255, 180, 0),
    'speed_boost': (0, 255, 200),
    'health_boost': (255, 150, 150),
    
    # Non-stackable items (generate colors for all)
    'double_shot': (255, 100, 255),
    'triple_shot': (255, 50, 255),
    'quad_shot': (200, 0, 200),
    'follower': (0, 255, 255),
    'piercing': (255, 100, 0),
    'explosive': (255, 50, 0),
    'homing': (100, 255, 100),
    'chain_lightning': (200, 200, 255),
    'shield': (100, 150, 255),
    'teleport': (150, 0, 255),
    'slow_time': (150, 150, 200),
    'split_shot': (255, 150, 200),
    'poison': (100, 255, 50),
    'freeze': (100, 200, 255),
    'extra_life': (255, 50, 50),
    'trapdoor': (50, 50, 50),
}

def generate_item_color(item_name):
    """Generate a unique color for an item based on its name"""
    if item_name in ITEM_COLORS:
        return ITEM_COLORS[item_name]
    
    # Generate color from hash of item name
    import hashlib
    hash_obj = hashlib.md5(item_name.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    
    # Generate RGB values (avoid too dark or too light)
    r = (hash_int & 0xFF) % 200 + 55
    g = ((hash_int >> 8) & 0xFF) % 200 + 55
    b = ((hash_int >> 16) & 0xFF) % 200 + 55
    
    return (r, g, b)

def is_stackable(item_name):
    """Check if an item is stackable"""
    return item_name in STACKABLE_ITEMS

def is_non_stackable(item_name):
    """Check if an item is non-stackable"""
    return item_name in NON_STACKABLE_ITEMS

