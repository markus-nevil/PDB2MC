config_path = "../docs/config.json"

decorative_blocks = ["acacia_log", "acacia_planks", "amethyst_block", "ancient_debris", "andesite", "barrel", "basalt", "bedrock", "bee_nest", "beehive", "birch_log", "birch_planks", "black_concrete", "black_concrete_powder", "black_glazed_terracotta", "black_shulker_box", "black_stained_glass", "black_terracotta", "black_wool", "blackstone", "blast_furnace", "blue_concrete", "blue_concrete_powder", "blue_glazed_terracotta", "blue_ice", "blue_shulker_box", "blue_stained_glass", "blue_terracotta", "blue_wool", "bone_block", "bookshelf", "brain_coral_block", "bricks", "brown_concrete", "brown_concrete_powder", "brown_glazed_terracotta", "brown_mushroom_block", "brown_shulker_box", "brown_stained_glass", "brown_terracotta", "brown_wool", "bubble_coral_block", "budding_amethyst", "calcite", "chiseled_deepslate", "chiseled_nether_bricks", "chiseled_polished_blackstone", "chiseled_quartz_block", "chiseled_red_sandstone", "chiseled_sandstone", "chiseled_stone_bricks", "clay", "coal_block", "coal_ore", "coarse_dirt", "cobbled_deepslate", "cobblestone", "composter", "copper_block", "copper_ore", "cracked_deepslate_bricks", "cracked_deepslate_tiles", "cracked_nether_bricks", "cracked_polished_blackstone_bricks", "cracked_stone_bricks", "crafting_table", "crimson_nylium", "crimson_planks", "crimson_stem", "crying_obsidian", "cut_copper", "cut_red_sandstone", "cut_sandstone", "cyan_concrete", "cyan_concrete_powder", "cyan_glazed_terracotta", "cyan_shulker_box", "cyan_stained_glass", "cyan_terracotta", "cyan_wool", "dark_oak_log", "dark_oak_planks", "dark_prismarine", "daylight_detector", "dead_brain_coral_block", "dead_bubble_coral_block", "dead_fire_coral_block", "dead_horn_coral_block", "dead_tube_coral_block", "deepslate", "deepslate_bricks", "deepslate_coal_ore", "deepslate_copper_ore", "deepslate_diamond_ore", "deepslate_emerald_ore", "deepslate_gold_ore", "deepslate_iron_ore", "deepslate_lapis_ore", "deepslate_redstone_ore", "deepslate_tiles", "deepslate", "diamond_block", "diamond_ore", "diorite", "dirt", "dried_kelp", "dripstone_block", "emerald_block", "emerald_ore", "end_portal_frame", "end_stone", "end_stone_bricks", "exposed_copper", "exposed_cut_copper", "farmland", "farmland_moist", "fire_coral_block", "furnace", "gilded_blackstone", "glass", "glowstone", "gold_block", "gold_ore", "granite", "grass_block", "gravel", "gray_concrete", "gray_concrete_powder", "gray_glazed_terracotta", "gray_shulker_box", "gray_stained_glass", "gray_terracotta", "gray_wool", "green_concrete", "green_concrete_powder", "green_glazed_terracotta", "green_shulker_box", "green_stained_glass", "green_terracotta", "green_wool", "hay_block", "honey_block", "honeycomb_block", "horn_coral_block", "ice", "iron_bars", "iron_block", "iron_ore", "jukebox", "jungle_log", "jungle_planks", "lapis_block", "lapis_ore", "light_blue_concrete", "light_blue_concrete_powder", "light_blue_glazed_terracotta", "light_blue_shulker_box", "light_blue_stained_glass", "light_blue_terracotta", "light_blue_wool", "light_gray_concrete", "light_gray_concrete_powder", "light_gray_glazed_terracotta", "light_gray_shulker_box", "light_gray_stained_glass", "light_gray_terracotta", "light_gray_wool", "lime_concrete", "lime_concrete_powder", "lime_glazed_terracotta", "lime_shulker_box", "lime_stained_glass", "lime_terracotta", "lime_wool", "lodestone", "loom", "magenta_concrete", "magenta_concrete_powder", "magenta_glazed_terracotta", "magenta_shulker_box", "magenta_stained_glass", "magenta_terracotta", "magenta_wool", "magma", "melon", "moss_block", "mossy_cobblestone", "mossy_stone_bricks", "mushroom_stem", "mycelium", "nether_bricks", "nether_gold_ore", "nether_quartz_ore", "nether_wart_block", "netherite_block", "netherrack", "note_block", "oak_log", "oak_planks", "observer", "obsidian", "orange_concrete", "orange_concrete_powder", "orange_glazed_terracotta", "orange_shulker_box", "orange_stained_glass", "orange_terracotta", "orange_wool", "oxidized_copper", "oxidized_cut_copper", "packed_ice", "pink_concrete", "pink_concrete_powder", "pink_glazed_terracotta", "pink_shulker_box", "pink_stained_glass", "pink_terracotta", "pink_wool", "piston", "podzol", "polished_andesite", "polished_basalt", "polished_blackstone", "polished_blackstone_bricks", "polished_deepslate", "polished_diorite", "polished_granite", "potted_azalea_bush_plant", "potted_flowering_azalea_bush_plant", "powder_snow", "prismarine", "prismarine_bricks", "pumpkin", "purple_concrete", "purple_concrete_powder", "purple_glazed_terracotta", "purple_shulker_box", "purple_stained_glass", "purple_terracotta", "purple_wool", "purpur_block", "purpur_pillar", "quartz_block", "quartz_bricks", "quartz_pillar", "raw_copper_block", "raw_gold_block", "raw_iron_block", "red_concrete", "red_concrete_powder", "red_glazed_terracotta", "red_mushroom_block", "red_nether_bricks", "red_sand", "red_sandstone", "red_shulker_box", "red_stained_glass", "red_terracotta", "red_wool", "redstone_block", "redstone_lamp", "redstone_lamp_on", "redstone_ore", "respawn_anchor", "rooted_dirt", "sand", "sandstone", "sea_lantern", "shroomlight", "shulker_box", "slime_block", "smithing_table", "smoker", "smooth_basalt", "smooth_stone", "smooth_stone_slab", "snow_block", "soul_sand", "soul_soil", "sponge", "spruce_log", "spruce_planks", "stone", "stone_bricks", "stonecutter", "stripped_acacia_log",  "stripped_birch_log",  "stripped_crimson_stem",  "stripped_dark_oak_log", "stripped_jungle_log", "stripped_oak_log", "stripped_spruce_log",  "stripped_warped_stem", "target", "terracotta", "tinted_glass", "tnt", "tube_coral_block", "tuff", "warped_nylium", "warped_planks", "warped_stem", "warped_wart_block", "weathered_copper", "weathered_cut_copper", "wet_sponge", "white_concrete", "white_concrete_powder", "white_glazed_terracotta", "white_shulker_box", "white_stained_glass", "white_terracotta", "white_wool", "yellow_concrete", "yellow_concrete_powder", "yellow_glazed_terracotta", "yellow_shulker_box", "yellow_stained_glass", "yellow_terracotta", "yellow_wool", "bamboo_block", "bamboo_planks", "cherry_leaves", "cherry_log", "cherry_planks", "mangrove_leaves", "mangrove_log", "mangrove_planks", "mangrove_roots", "mud", "mud_bricks", "muddy_mangrove_roots", "ochre_froglight", "packed_mud", "pearlescent_froglight", "reinforced_deepslate", "sculk_catalyst", "stripped_bamboo_block", "stripped_cherry_log", "stripped_mangrove_log", "suspicious_gravel_2", "suspicious_sand_2", "verdant_froglight"]
hex_dict = {"acacia_log": "#5c564d", "acacia_planks": "#a0562f", "amethyst_block": "#6b4da5", "ancient_debris": "#4e2b22", "andesite": "#9d9e9a", "barrel": "#8a673b", "basalt": "#565456", "bedrock": "#3f3f3f",  "bee_nest": "#d6a154", "beehive": "#755a32", "birch_log": "#f6f5f4", "birch_planks": "#d1c083", "black_concrete": "#080a0f", "black_concrete_powder": "#12141a", "black_glazed_terracotta": "#18181b", "black_shulker_box": "#1e1e22", "black_stained_glass": "#191919", "black_terracotta": "#251610", "black_wool": "#1f1f23", "blackstone": "#201819", "blast_furnace": "#4e4e4e", "blue_concrete": "#2d2f8f", "blue_concrete_powder": "#474aa7", "blue_glazed_terracotta": "#292a7d", "blue_ice": "#6b9ffb", "blue_shulker_box": "#323499", "blue_stained_glass": "#334cb1", "blue_terracotta": "#4c3d5c", "blue_wool": "#303294", "bone_block": "#e7e4d2", "bookshelf": "#b3925f", "brain_coral_block": "#d861a2", "bricks": "#a66757", "brown_concrete": "#613c20", "brown_concrete_powder": "#764f31", "brown_glazed_terracotta": "#714829", "brown_mushroom_block": "#967251", "brown_shulker_box": "#724727", "brown_stained_glass": "#664c33", "brown_terracotta": "#4e3524", "brown_wool": "#6d4325", "bubble_coral_block": "#ae27aa", "budding_amethyst": "#62449b", "calcite": "#e9e9e3", "chiseled_deepslate": "#282828", "chiseled_nether_bricks": "#291518", "chiseled_polished_blackstone": "#4e4b54", "chiseled_quartz_block": "#dcd8ca", "chiseled_red_sandstone": "#9e4e0b", "chiseled_sandstone": "#d3c293", "chiseled_stone_bricks": "#5a5a5a", "clay": "#9ca2ac", "coal_block": "#080808", "coal_ore": "#7f7f7f", "coarse_dirt": "#a27651", "cobbled_deepslate": "#3c3c42", "cobblestone": "#a8a8a8",  "composter": "#815328", "copper_block": "#d2795c", "copper_ore": "#677470", "cracked_deepslate_bricks": "#474749", "cracked_deepslate_tiles": "#282828", "cracked_nether_bricks": "#3b1b21", "cracked_polished_blackstone_bricks": "#1f1618", "cracked_stone_bricks": "#8d8b8d", "crafting_table": "#49351e", "crimson_nylium": "#721e1e", "crimson_planks": "#7a3953", "crimson_stem": "#4a1f27",  "crying_obsidian": "#06040c", "cut_copper": "#a65a40", "cut_red_sandstone": "#ba6521", "cut_sandstone": "#e5e0b8", "cyan_concrete": "#157686", "cyan_concrete_powder": "#238a97", "cyan_glazed_terracotta": "#15848e", "cyan_shulker_box": "#168590", "cyan_stained_glass": "#4c7f98", "cyan_terracotta": "#555959", "cyan_wool": "#158d92", "dark_oak_log": "#332815", "dark_oak_planks": "#4e3218", "dark_prismarine": "#396252", "dead_brain_coral_block": "#686361", "dead_bubble_coral_block": "#9a958f", "dead_fire_coral_block": "#6b6563", "dead_horn_coral_block": "#6a6361", "dead_tube_coral_block": "#666261", "deepslate": "#565656", "deepslate_bricks": "#616161", "deepslate_coal_ore": "#636363", "deepslate_copper_ore": "#495e58", "deepslate_diamond_ore": "#454649", "deepslate_emerald_ore": "#6b6d6c", "deepslate_gold_ore": "#48484b", "deepslate_iron_ore": "#49494c", "deepslate_lapis_ore": "#4e4e50", "deepslate_redstone_ore": "#444144", "deepslate_tiles": "#2a2a2a", "deepslate": "#5e5e5e", "diamond_block": "#3ddedb", "diamond_ore": "#94a1a2", "diorite": "#adacad", "dirt": "#8d6545", "dried_kelp": "#192314", "dripstone_block": "#806155", "emerald_block": "#19b138", "emerald_ore": "#939895", "end_portal_frame": "#d9dc9c", "end_stone": "#cece8e", "end_stone_bricks": "#e7f2b1", "exposed_copper": "#b47f6f", "exposed_cut_copper": "#a27d65", "farmland": "#a67852", "farmland_moist": "#42220a", "fire_coral_block": "#971f2c", "furnace": "#a9a9a9", "gilded_blackstone": "#221a1b", "glass": "#cfe9e8", "glowstone": "#784e27", "gold_block": "#edbb2a", "gold_ore": "#6a6a6a", "granite": "#835949", "grass_block": "#848484", "gravel": "#787372", "gray_concrete": "#36393d", "gray_concrete_powder": "#494c50", "gray_glazed_terracotta": "#3b3f43", "gray_shulker_box": "#3d4145", "gray_stained_glass": "#4c4c4c", "gray_terracotta": "#392923", "gray_wool": "#454c4f", "green_concrete": "#495a24", "green_concrete_powder": "#5c702e", "green_glazed_terracotta": "#5d7b1e", "green_shulker_box": "#536c1c", "green_stained_glass": "#667f33", "green_terracotta": "#4c532a", "green_wool": "#577118", "hay_block": "#b7a02b", "honey_block": "#f8a91b", "honeycomb_block": "#d67a06", "horn_coral_block": "#e3dc47", "ice": "#89b1fc", "iron_bars": "#6d706b", "iron_block": "#e8e8e8", "iron_ore": "#767574", "jukebox": "#86563d", "jungle_log": "#6c5421", "jungle_planks": "#b48361", "lapis_block": "#1c3f83", "lapis_ore": "#737373", "light_blue_concrete": "#2387c5", "light_blue_concrete_powder": "#4cb8d6", "light_blue_glazed_terracotta": "#2a72b5", "light_blue_shulker_box": "#3ab2d9", "light_blue_stained_glass": "#6698d7", "light_blue_terracotta": "#726c89", "light_blue_wool": "#45bde0", "light_gray_concrete": "#7c7c72", "light_gray_concrete_powder": "#92928a", "light_gray_glazed_terracotta": "#c2c5c7", "light_gray_shulker_box": "#8a8a81", "light_gray_stained_glass": "#989898", "light_gray_terracotta": "#876b62", "light_gray_wool": "#999993", "lime_concrete": "#5da618", "lime_concrete_powder": "#78b627", "lime_glazed_terracotta": "#5da517", "lime_shulker_box": "#6fba18", "lime_stained_glass": "#7fcb19", "lime_terracotta": "#657433", "lime_wool": "#63ac18", "lodestone": "#727272", "loom": "#774a3a", "magenta_concrete": "#a62f9c", "magenta_concrete_powder": "#c256ba", "magenta_glazed_terracotta": "#bb43b2", "magenta_shulker_box": "#b83ead", "magenta_stained_glass": "#b14cd7", "magenta_terracotta": "#92566b", "magenta_wool": "#b23aa8", "magma": "#561f1f", "melon": "#a6ab1d", "moss_block": "#4a6029", "mossy_cobblestone": "#5c6c40", "mossy_stone_bricks": "#828182", "mushroom_block": "#ceae7c", "mushroom_stem": "#cfc8c0", "mycelium": "#7e6a6e", "nether_bricks": "#271417", "nether_gold_ore": "#581f1f", "nether_quartz_ore": "#592020", "nether_wart_block": "#650100", "netherite_block": "#4d494d", "netherrack": "#763535", "note_block": "#2a281f", "oak_log": "#80643b", "oak_planks": "#b7945c", "observer": "#333333", "obsidian": "#030106", "orange_concrete": "#e06100", "orange_concrete_powder": "#dd7b17", "orange_glazed_terracotta": "#ee7713", "orange_shulker_box": "#f3730f", "orange_stained_glass": "#d77f33", "orange_terracotta": "#9e5224", "orange_wool": "#e96a09", "oxidized_copper": "#5ab293", "oxidized_cut_copper": "#5aad8d", "packed_ice": "#80a9f5", "pink_concrete": "#d5658e", "pink_concrete_powder": "#de8aaa", "pink_glazed_terracotta": "#e9b4c5", "pink_shulker_box": "#f188a7", "pink_stained_glass": "#f17fa4", "pink_terracotta": "#9e4c4d", "pink_wool": "#f395b1", "piston": "#545353", "podzol": "#4e3817", "polished_andesite": "#9d9e9d", "polished_basalt": "#6b6b6b", "polished_blackstone": "#3f3c48", "polished_blackstone_bricks": "#211b18", "polished_deepslate": "#2d2d2d", "polished_diorite": "#d8d6d8", "polished_granite": "#a77765", "potted_azalea_bush_plant": "#4e662a", "potted_flowering_azalea_bush_plant": "#525924", "powder_snow": "#fefefe", "prismarine": "#529584", "prismarine_bricks": "#5da89d", "pumpkin": "#b66611", "purple_concrete": "#65209c", "purple_concrete_powder": "#7f35ae", "purple_glazed_terracotta": "#8f3ac3", "purple_shulker_box": "#7225a7", "purple_stained_glass": "#7f3fb1", "purple_terracotta": "#744454", "purple_wool": "#6e23a2", "purpur_block": "#9c6e9c", "purpur_pillar": "#a676a5", "quartz_block": "#eae2da", "quartz_bricks": "#eae2da", "quartz_pillar": "#efece9", "raw_copper_block": "#be6e54", "raw_gold_block": "#c3831f", "raw_iron_block": "#755d3c", "red_concrete": "#8e2121", "red_concrete_powder": "#a03230", "red_glazed_terracotta": "#a02723", "red_mushroom_block": "#c02624", "red_nether_bricks": "#340103", "red_sand": "#bb6520", "red_sandstone": "#a3510d", "red_shulker_box": "#992421", "red_stained_glass": "#983333", "red_terracotta": "#8c3b2d", "red_wool": "#9a2421", "redstone_block": "#8b1202", "redstone_lamp": "#3d2214", "redstone_lamp_on": "#422816", "redstone_ore": "#757373", "respawn_anchor": "#4b278a", "rooted_dirt": "#a87c5f", "sand": "#d5c699", "sandstone": "#c9b17a", "sea_lantern": "#dbe7df", "shroomlight": "#fda565", "shulker_box": "#956895", "slime_block": "#75c463", "smithing_table": "#481e19", "smoker": "#443726", "smooth_basalt": "#575657", "smooth_stone": "#a9a9a9", "snow_block": "#f2fcfc", "soul_sand": "#413127", "soul_soil": "#392b23", "sponge": "#d0d04b", "spruce_log": "#321e0c", "spruce_planks": "#806037", "stone": "#8a8a8a", "stone_bricks": "#747374", "stonecutter": "#848384", "stripped_acacia_log": "#9e5938", "stripped_birch_log": "#ccb87e", "stripped_crimson_stem": "#8a395c", "stripped_dark_oak_log": "#463723",  "stripped_jungle_log": "#ba8c61", "stripped_oak_log": "#bb985d", "stripped_spruce_log": "#7d5d37", "stripped_warped_stem": "#3f9d9b", "target": "#f5efe7", "terracotta": "#955d43", "tinted_glass": "#272329",  "tnt": "#bd2b19", "tube_coral_block": "#3a66e1", "tuff": "#55564c", "warped_nylium": "#2c6057", "warped_planks": "#398886", "warped_stem": "#49263c", "warped_wart_block": "#186b6c", "weathered_copper": "#6aa77f", "weathered_cut_copper": "#768e5d", "wet_sponge": "#c9cb4a", "white_concrete": "#cdd2d3", "white_concrete_powder": "#d6d8d9", "white_glazed_terracotta": "#cce0e9", "white_shulker_box": "#e3e8e8", "white_stained_glass": "#fefefe", "white_terracotta": "#d2b4a1", "white_wool": "#eff1f1", "yellow_concrete": "#f0ae15", "yellow_concrete_powder": "#e5bf2e", "yellow_glazed_terracotta": "#e8ac21", "yellow_shulker_box": "#fac523", "yellow_stained_glass": "#e4e433", "yellow_terracotta": "#b78222", "yellow_wool": "#f9ca2b", "bamboo_block": "#6e7c31", "bamboo_planks": "#cdb650", "cherry_leaves": "#f7c8e4", "cherry_log": "#2c1a25", "cherry_planks": "#e6c1ba", "mangrove_leaves": "#555353", "mangrove_log": "#59472b", "mangrove_planks": "#743134", "mangrove_roots": "#463723", "mud": "#363339", "mud_bricks": "#997555", "muddy_mangrove_roots": "#493a25", "ochre_froglight": "#fbfbda", "packed_mud": "#88654d", "pearlescent_froglight": "#faf7f6", "reinforced_deepslate": "#3b3f43", "sculk_catalyst": "#112229", "stripped_bamboo_block": "#cdb650",  "stripped_cherry_log": "#d9959b", "stripped_mangrove_log": "#712f2f", "suspicious_gravel_2": "#746e6c", "suspicious_sand_2": "#c5ac73", "verdant_froglight": "#f0f9f0"}

#decorative_blocks = ["andesite",    "bedrock",    "blackstone",    "blackstone_bricks",    "brick",    "chiseled_nether_bricks",    "chiseled_polished_blackstone",    "cobblestone",    "cracked_nether_bricks",    "cracked_polished_blackstone_bricks",    "cut_red_sandstone",    "cut_sandstone",    "diorite",    "end_stone_bricks",    "gilded_blackstone",    "glowstone",    "granite",    "gravel",    "infested_chiseled_stone_bricks",    "infested_cobblestone",    "infested_cracked_stone_bricks",    "infested_mossy_stone_bricks",    "infested_stone",    "infested_stone_bricks",    "mossy_cobblestone",    "mossy_stone_bricks",    "nether_bricks",    "nether_gold_ore",    "nether_quartz_ore",    "obsidian",    "polished_andesite",    "polished_blackstone",    "polished_blackstone_bricks",    "polished_diorite",    "polished_granite",    "red_nether_bricks",    "red_sandstone",    "sandstone",    "smooth_quartz",    "smooth_red_sandstone",    "smooth_sandstone",    "soul_sand",    "soul_soil",    "stone",    "stone_bricks",    "terracotta",    "white_wool",    "orange_wool",    "magenta_wool",    "light_blue_wool",    "yellow_wool",    "lime_wool",    "pink_wool",    "gray_wool",    "light_gray_wool",    "cyan_wool",    "purple_wool",    "blue_wool",    "brown_wool",    "green_wool",    "red_wool",    "black_wool",    "grass_block",    "mycelium",    "podzol"]
concrete_blocks = [  "black_concrete",    "blue_concrete",    "brown_concrete",    "cyan_concrete",    "gray_concrete",    "green_concrete",    "light_blue_concrete",    "lime_concrete",    "magenta_concrete",    "orange_concrete",    "pink_concrete",    "purple_concrete",    "red_concrete",    "white_concrete",    "yellow_concrete"]


block_colors = {(143, 61, 46), (224, 97, 0), (57, 42, 35), (218, 224, 162), (186, 99, 29), (42, 35, 40), (76, 83, 42),
                (188, 188, 188), (169, 48, 159), (216, 202, 155), (152, 94, 67), (99, 171, 158), (119, 118, 119),
                (30, 67, 140), (216, 215, 210), (233, 236, 236), (192, 193, 194), (99, 156, 151), (216, 203, 155),
                (58, 175, 217), (73, 91, 36), (127, 127, 127), (94, 168, 24), (16, 15, 15), (58, 58, 77),
                (142, 142, 134), (229, 148, 29), (112, 185, 25), (189, 101, 31), (171, 131, 84), (169, 125, 169),
                (217, 206, 159), (84, 109, 27), (62, 68, 71), (158, 158, 158), (149, 103, 85), (85, 67, 25),
                (122, 121, 122), (246, 208, 61), (125, 125, 125), (132, 134, 133), (0, 0, 3), (209, 178, 161),
                (171, 132, 84), (109, 85, 50), (96, 76, 49), (35, 137, 198), (213, 101, 142), (207, 213, 214),
                (125, 125, 115), (196, 176, 118), (231, 226, 218), (160, 166, 179), (177, 144, 86), (53, 48, 56),
                (118, 117, 118), (240, 175, 21), (15, 10, 24), (161, 83, 37), (103, 96, 86), (161, 78, 78),
                (186, 133, 35), (174, 92, 59), (154, 106, 89), (183, 96, 27), (115, 89, 52), (58, 37, 16), (60, 46, 26),
                (142, 32, 32), (116, 167, 253), (189, 68, 179), (136, 136, 136), (220, 220, 220), (98, 237, 228),
                (54, 57, 61)}

chain_blocks = {"0" : "white_concrete",
                "1" : "red_concrete",
                "2" : "blue_concrete",
                "3" : "yellow_concrete",
                "4" : "lime_concrete",
                "5" : "pink_concrete",
                "6" : "light_concrete",
                "7" : "purple_concrete",
                "8" : "light_concrete",
                "9" : "green_concrete",
                "10": "orange_concrete"}

dark_skeleton_blocks = {"0b": "white_terracotta",
                        "1b": "red_terracotta",
                        "2b": "blue_terracotta",
                        "3b": "yellow_terracotta",
                        "4b": "lime_terracotta",
                        "5b": "pink_terracotta",
                        "6b": "light_gray_terracotta",
                        "7b": "purple_terracotta",
                        "8b": "light_blue_terracotta",
                        "9b": "green_terracotta",
                        "10b": "orange_terracotta"}

radii = {"C": 1.0,
         "N": 0.9285,
         "O": 0.857,
         "S": 1.428,
         "P": 1.428,
         "Mg": 2.142,
         "K": 3.1428,
         "Ca": 2.5714}

hydrophobic = {"ASP": "nether_wart_block",
               "GLU": "red_wool",
               "LYS": "red_mushroom_block",
               "ARG": "copper_block",
               "HIS": "pink_concrete",
               "GLN": "stripped_cherry_log",
               "PRO": "cherry_planks",
               "ASN": "quartz_block",
               "ALA": "snow_block",
               "THR": "snow_block",
               "SER": "snow_block",
               "VAL": "snow_block",
               "GLY": "snow_block",
               "MET": "white_shulker_box",
               "CYS": "diorite",
               "ILE": "light_gray_glazed_terracotta",
               "LEU": "packed_ice",
               "TYR": "blue_ice",
               "PHE": "tube_coral_block",
               "TRP": "blue_concrete"}

group = {"ARG": "red_wool",
         "HIS": "red_wool",
         "LYS": "red_wool",
         "ASP": "blue_wool",
         "GLU": "blue_wool",
         "SER": "yellow_wool",
         "THR": "yellow_wool",
         "ASN": "yellow_wool",
         "GLN": "yellow_wool",
         "CYS": "orange_wool",
         "GLY": "orange_wool",
         "PRO": "orange_wool",
         "ALA": "green_wool",
         "ILE": "green_wool",
         "LEU": "green_wool",
         "MET": "green_wool",
         "PHE": "green_wool",
         "TRP": "green_wool",
         "TYR": "green_wool",
         "VAL": "green_wool"}

charge = {"ARG": "emerald_block",
          "LYS": "weathered_copper",
          "ASP": "cobblestone",
          "GLU": "light_gray_wool",
          "ASN": "end_stone",
          "GLN": "end_stone_bricks",
          "HIS": "white_glazed_terracotta",
          "PRO": "verdant_froglight",
          "TYR": "white_wool",
          "TRP": "snow_block",
          "SER": "snow_block",
          "THR": "snow_block",
          "GLY": "snow_block",
          "ALA": "pearlescent_froglight",
          "MET": "ochre_froglight",
          "CYS": "cherry_leaves",
          "PHE": "cherry_planks",
          "LEU": "pink_wool",
          "VAL": "pink_concrete",
          "ILE": "red_mushroom_block"}


