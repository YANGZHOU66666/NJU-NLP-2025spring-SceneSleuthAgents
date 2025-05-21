from ortools.sat.python import cp_model

def solver_tool(
    victim: str,
    suspects: list[str],
    weapons: list[str],
    motives: list[str],
    room_grid: list[list[str]],
    times: list[str],
    clues: list[dict[str, any]],
):
    """
    使用OR-Tools求解谋杀案谜题

    参数说明 (Args):
        victim (str): 被害人的姓名。
            示例: "博迪"

        suspects (list[str]): 嫌疑人姓名列表。
            示例: ["玫瑰夫人", "蜜桃小姐"]

        weapons (list[str]): 可能的凶器名称列表。
            示例: ["绳索", "马蹄铁"]

        motives (list[str]): 可能的作案动机列表。
            如果列表为空，系统会使用一个默认的“未知动机”。
            注意：当前版本的求解器主要使用一个全局的“凶杀动机”，
            更复杂的将特定动机分配给特定嫌疑人的逻辑需要额外的线索类型或模型调整。
            示例: ["复仇", "贪婪"] 或 []

        room_grid (list[list[str]]): 房间布局网格。一个二维列表，其中每个内部列表代表一行。
            - 字符串元素是房间的名称。
            - 用 "-" 表示该位置没有房间或是障碍物。
            - 列表的索引定义了房间的相对位置（例如，grid[0][0] 是左上角的房间）。
            示例:
            [
                ["书房", "客厅", "-"],
                ["餐厅", "-", "厨房"]
            ]
            这表示一个2x3的网格，书房在(0,0)，客厅在(0,1)，餐厅在(1,0)，厨房在(1,2)。

        times (list[str]): 案件相关的时间点列表。
            - 如果列表为空或只有一个元素，系统会将其视为一个单一的、代表性的时间点（内部处理为 "t0"）。
            - 如果有多个时间点，它们应该是有序的（尽管当前求解器对时间顺序的利用有限，主要用于区分不同时刻的状态）。
            示例: ["19:00", "19:15", "19:30"] 或 []

        clues (list[dict[str, any]]): 线索列表。每个线索是一个字典，其结构取决于 'type' 字段。
            支持的线索类型及格式如下：

            1.  `WeaponClue` (确定凶器线索):
                -   含义: 直接指明了本案使用的凶器。
                -   格式: `{"type": "WeaponClue", "weapon": "凶器名称"}`
                -   示例: `{"type": "WeaponClue", "weapon": "绳索"}`

            2.  `ItemRoomTimeClue` (物品-房间-时间线索):
                -   含义: 指明某个物品（被害人、嫌疑人或凶器）在特定时间点位于特定房间。
                -   格式: `{"type": "ItemRoomTimeClue", "item": "物品名称", "room": "房间名称", "time": "时间点"}`
                -   `item`: 可以是 `victim` 的名字，`suspects` 列表中的一个名字，或 `weapons` 列表中的一个名字。
                -   `time`: 应该是 `times` 列表中定义的一个时间点。如果为 `None` 或缺失，则默认为第一个处理后的时间点 (通常是 "t0")。
                -   示例: `{"type": "ItemRoomTimeClue", "item": "玫瑰夫人", "room": "书房", "time": "19:00"}`
                -   示例 (时间点为None): `{"type": "ItemRoomTimeClue", "item": "马蹄铁", "room": "厨房", "time": None}`

            3.  `RelativeLocationClue` (相对位置线索):
                -   含义: 指明物品1相对于物品2的位置关系（目前仅支持上、下、左、右，即北、南、西、东）。
                -   格式: `{"type": "RelativeLocationClue", "item1": "物品1名称", "item2": "物品2名称", "direction": "方向"}`
                -   `item1`, `item2`: 可以是 `suspects` 或 `weapons` 列表中的名字。
                -   `direction`: "北", "南", "东", "西"。
                -   注意: 当前实现假设此线索应用于第一个处理后的时间点 (通常是 "t0")。如果需要指定特定时间，此线索类型需要扩展。
                -   示例: `{"type": "RelativeLocationClue", "item1": "绳索", "item2": "蜜桃小姐", "direction": "南"}`
                    (表示“绳索”在“蜜桃小姐”的正南方，即“绳索”的行索引 > “蜜桃小姐”的行索引，列索引相同)

            4.  `IfAndOnlyIfClue` (当且仅当关系线索):
                -   含义: 指明两个子线索之间是逻辑上的充分必要关系（等价关系）。
                -   格式: `{"type": "IfAndOnlyIfClue", "clue1": <子线索1字典>, "clue2": <子线索2字典>}`
                -   `clue1`, `clue2`: **必须是** `ItemRoomTimeClue` 类型的线索字典。
                -   示例:
                    ```json
                    {
                        "type": "IfAndOnlyIfClue",
                        "clue1": {"type": "ItemRoomTimeClue", "item": "马蹄铁", "room": "书房", "time": None},
                        "clue2": {"type": "ItemRoomTimeClue", "item": "博迪", "room": "书房", "time": None}
                    }
                    ```
                    (表示“马蹄铁在书房”当且仅当“博迪在书房”)

    返回值 (Returns):
        dict: 一个包含求解结果的字典，或在无解/出错时包含 "error" 键。
              成功时的结构示例:
              {
                  'murderer': '凶手名称',
                  'weapon': '凶器名称',
                  'murder_time': '凶杀时间点',
                  'murder_location': '凶杀房间名称',
                  'murder_motive': '凶杀动机',
                  'suspect_locations': {
                      '嫌疑人1': {'时间点1': '房间A', '时间点2': '房间B'},
                      '嫌疑人2': {'时间点1': '房间C', '时间点2': '房间D'}
                  },
                  'weapon_locations': {
                      '凶器1': {'时间点1': '房间X', '时间点2': '房间Y'},
                      '凶器2': {'时间点1': '房间Z', '时间点2': '房间W'}
                  },
                  'motives': { # 注意：这通常反映的是全局凶杀动机，除非有更复杂的动机分配
                      '嫌疑人1': '推断出的动机或默认值',
                      '嫌疑人2': '推断出的动机或默认值'
                  }
              }
    """
    # 初始化CP-SAT模型
    model = cp_model.CpModel()

    # 获取房间网格的尺寸
    grid_height = len(room_grid)
    grid_width = len(room_grid[0]) if grid_height > 0 else 0

    # 创建房间名称到坐标的映射，并收集所有有效房间的坐标列表
    room_to_coords = {}  # 字典：房间名 -> (行, 列)
    valid_room_coords_list = []  # 列表：[(行1, 列1), (行2, 列2), ...]
    for r_idx_grid in range(grid_height): 
        for c_idx_grid in range(grid_width): 
            room_name = room_grid[r_idx_grid][c_idx_grid]
            if room_name != "-":  # 如果不是空房间标记
                room_to_coords[room_name] = (r_idx_grid, c_idx_grid)
                valid_room_coords_list.append((r_idx_grid, c_idx_grid))
    
    # 如果网格中没有有效的房间，则返回错误
    if not valid_room_coords_list:
        return {"error": "房间网格中没有有效的房间"}

    # 处理时间和动机列表为空的情况，提供默认值
    processed_times = times if times else ["t0"]  # 如果times为空，使用默认时间点 "t0"
    processed_motives = motives if motives else ["未知动机"] # 如果motives为空，使用默认动机

    # --- 变量定义 ---

    # 1. 凶手身份变量 (布尔变量列表，每个嫌疑人对应一个)
    murderer_vars = {s: model.NewBoolVar(f'murderer_{s}') for s in suspects}
    if suspects: model.AddExactlyOne(murderer_vars.values())  # 约束：有且仅有一个凶手 (如果嫌疑人列表不为空)

    # 2. 凶器变量 (布尔变量列表，每个凶器对应一个)
    weapon_vars = {w: model.NewBoolVar(f'weapon_{w}') for w in weapons}
    if weapons: model.AddExactlyOne(weapon_vars.values())  # 约束：有且仅使用一个凶器 (如果凶器列表不为空)

    # 3. 凶杀时间变量 (整数变量，表示在processed_times列表中的索引)
    murder_time_idx = model.NewIntVar(0, len(processed_times) - 1, 'murder_time_idx')

    # 4. 凶杀地点变量 (行、列坐标)
    murder_location_x = model.NewIntVar(0, grid_height - 1, 'murder_location_x')
    murder_location_y = model.NewIntVar(0, grid_width - 1, 'murder_location_y')
    # 约束：凶杀地点必须是有效的房间坐标
    if valid_room_coords_list: model.AddAllowedAssignments((murder_location_x, murder_location_y), valid_room_coords_list)

    # 5. 凶杀动机变量 (整数变量，表示在processed_motives列表中的索引)
    murder_motive_idx = model.NewIntVar(0, len(processed_motives) - 1, 'murder_motive_idx')

    # 6. 嫌疑人位置变量 (字典：嫌疑人 -> 时间点 -> {'x': x坐标变量, 'y': y坐标变量, 't_idx': 时间索引})
    suspect_locations = {}
    for s in suspects:
        suspect_locations[s] = {}
        for t_idx, t_val in enumerate(processed_times):
            s_loc_x = model.NewIntVar(0, grid_height - 1, f'loc_{s}_{t_val}_x')
            s_loc_y = model.NewIntVar(0, grid_width - 1, f'loc_{s}_{t_val}_y')
            # 约束：嫌疑人位置必须是有效的房间坐标
            if valid_room_coords_list: model.AddAllowedAssignments((s_loc_x, s_loc_y), valid_room_coords_list)
            suspect_locations[s][t_val] = {'x': s_loc_x, 'y': s_loc_y, 't_idx': t_idx}
            
    # 7. 被害人位置变量 (字典：时间点 -> {'x': x坐标变量, 'y': y坐标变量, 't_idx': 时间索引})
    victim_locations = {}
    for t_idx, t_val in enumerate(processed_times):
        v_loc_x = model.NewIntVar(0, grid_height - 1, f'loc_{victim}_{t_val}_x')
        v_loc_y = model.NewIntVar(0, grid_width - 1, f'loc_{victim}_{t_val}_y')
        # 约束：被害人位置必须是有效的房间坐标
        if valid_room_coords_list: model.AddAllowedAssignments((v_loc_x, v_loc_y), valid_room_coords_list)
        victim_locations[t_val] = {'x': v_loc_x, 'y': v_loc_y, 't_idx': t_idx}

    # 8. 凶器位置变量 (字典：凶器 -> 时间点 -> {'x': x坐标变量, 'y': y坐标变量, 't_idx': 时间索引})
    weapon_locations = {}
    for w in weapons:
        weapon_locations[w] = {}
        for t_idx, t_val in enumerate(processed_times):
            w_loc_x = model.NewIntVar(0, grid_height - 1, f'loc_{w}_{t_val}_x')
            w_loc_y = model.NewIntVar(0, grid_width - 1, f'loc_{w}_{t_val}_y')
            # 约束：凶器位置必须是有效的房间坐标
            if valid_room_coords_list: model.AddAllowedAssignments((w_loc_x, w_loc_y), valid_room_coords_list)
            weapon_locations[w][t_val] = {'x': w_loc_x, 'y': w_loc_y, 't_idx': t_idx}

    # --- 凶杀核心约束 ---
    # 约束：凶手、被害人、被选中的凶器必须在凶杀发生的时间点共同位于凶杀地点。
    for t_idx, t_val in enumerate(processed_times):
        # 创建一个布尔变量 time_is_murder_time，表示当前时间点 t_val 是否是凶杀发生的时间点
        time_is_murder_time = model.NewBoolVar(f'time_is_murder_time_{t_val}')
        # 实体化：time_is_murder_time <==> (murder_time_idx == t_idx)
        model.Add(murder_time_idx == t_idx).OnlyEnforceIf(time_is_murder_time)
        model.Add(murder_time_idx != t_idx).OnlyEnforceIf(time_is_murder_time.Not())

        # 1. 如果当前时间是凶杀时间，则被害人必须在凶杀地点
        model.Add(victim_locations[t_val]['x'] == murder_location_x).OnlyEnforceIf(time_is_murder_time)
        model.Add(victim_locations[t_val]['y'] == murder_location_y).OnlyEnforceIf(time_is_murder_time)

        # 2. 如果当前时间是凶杀时间且某嫌疑人是凶手，则该嫌疑人必须在凶杀地点
        for s_name, s_var in murderer_vars.items(): # s_var 是布尔变量：s_name 是否是凶手
            murderer_at_scene_at_time = model.NewBoolVar(f'murderer_{s_name}_at_scene_at_{t_val}')
            # 实体化：murderer_at_scene_at_time <==> (s_var == True AND time_is_murder_time == True)
            model.AddImplication(murderer_at_scene_at_time, s_var) # 如果凶手在现场在此时，那么他一定是凶手
            model.AddImplication(murderer_at_scene_at_time, time_is_murder_time) # 并且此时一定是凶杀时间
            model.Add(murderer_at_scene_at_time == 1).OnlyEnforceIf([s_var, time_is_murder_time]) # 如果他是凶手且此时是凶杀时间，则此变量为真
            
            model.Add(suspect_locations[s_name][t_val]['x'] == murder_location_x).OnlyEnforceIf(murderer_at_scene_at_time)
            model.Add(suspect_locations[s_name][t_val]['y'] == murder_location_y).OnlyEnforceIf(murderer_at_scene_at_time)

        # 3. 如果当前时间是凶杀时间且某凶器是被选中的凶器，则该凶器必须在凶杀地点
        for w_name, w_var in weapon_vars.items(): # w_var 是布尔变量：w_name 是否是被选中的凶器
            weapon_at_scene_at_time = model.NewBoolVar(f'weapon_{w_name}_at_scene_at_{t_val}')
            # 实体化：weapon_at_scene_at_time <==> (w_var == True AND time_is_murder_time == True)
            model.AddImplication(weapon_at_scene_at_time, w_var)
            model.AddImplication(weapon_at_scene_at_time, time_is_murder_time)
            model.Add(weapon_at_scene_at_time == 1).OnlyEnforceIf([w_var, time_is_murder_time])
            
            model.Add(weapon_locations[w_name][t_val]['x'] == murder_location_x).OnlyEnforceIf(weapon_at_scene_at_time)
            model.Add(weapon_locations[w_name][t_val]['y'] == murder_location_y).OnlyEnforceIf(weapon_at_scene_at_time)
            
    # --- 线索处理辅助函数 ---
    def get_item_location_vars(item_name, time_value):
        """根据物品名称和时间点，返回其对应的x, y位置变量元组。"""
        if item_name == victim:
            return victim_locations[time_value]['x'], victim_locations[time_value]['y']
        elif item_name in suspects:
            return suspect_locations[item_name][time_value]['x'], suspect_locations[item_name][time_value]['y']
        elif item_name in weapons:
            return weapon_locations[item_name][time_value]['x'], weapon_locations[item_name][time_value]['y']
        else: # 未知物品
            raise ValueError(f"获取位置变量时遇到未知物品: {item_name}")

    def reify_item_at_location_time(item_name, room_name, time_value, clue_id_suffix):
        """
        创建一个布尔变量，该变量当且仅当 item_name 在 time_value 时位于 room_name 时为真。
        用于将“物品-房间-时间”的条件实体化。
        """
        # 处理时间，如果为None，则使用第一个处理后的时间点
        target_time = time_value if time_value is not None else processed_times[0]
        # 检查时间点和房间名的有效性
        if target_time not in processed_times:
             raise ValueError(f"线索中使用了无效的时间点 '{target_time}'。可用时间点: {processed_times}")
        if room_name not in room_to_coords:
            raise ValueError(f"线索中使用了无效的房间名 '{room_name}'。可用房间: {list(room_to_coords.keys())}")
        
        r_x, r_y = room_to_coords[room_name] # 获取目标房间的坐标
        item_loc_x_var, item_loc_y_var = get_item_location_vars(item_name, target_time) # 获取物品的位置变量
        
        # 创建表示“条件满足”的布尔变量
        condition_met_var = model.NewBoolVar(f'item_{item_name}_at_{room_name}_at_{target_time}_{clue_id_suffix}')
        
        # 创建辅助布尔变量，表示x坐标和y坐标是否分别匹配
        x_matches = model.NewBoolVar(f'x_match_{clue_id_suffix}')
        model.Add(item_loc_x_var == r_x).OnlyEnforceIf(x_matches)
        model.Add(item_loc_x_var != r_x).OnlyEnforceIf(x_matches.Not())

        y_matches = model.NewBoolVar(f'y_match_{clue_id_suffix}')
        model.Add(item_loc_y_var == r_y).OnlyEnforceIf(y_matches)
        model.Add(item_loc_y_var != r_y).OnlyEnforceIf(y_matches.Not())
        
        # 核心实体化逻辑: condition_met_var <==> (x_matches AND y_matches)
        # 1. condition_met_var => x_matches  (如果条件满足，则x必须匹配)
        model.AddImplication(condition_met_var, x_matches)
        # 2. condition_met_var => y_matches  (如果条件满足，则y必须匹配)
        model.AddImplication(condition_met_var, y_matches)
        # 3. (x_matches AND y_matches) => condition_met_var (如果x和y都匹配，则条件满足)
        model.Add(condition_met_var == 1).OnlyEnforceIf([x_matches, y_matches])
        # （注意：(x_matches.Not() OR y_matches.Not()) => condition_met_var.Not() 也被隐含满足了）

        return condition_met_var

    # --- 遍历并处理所有线索 ---
    clue_idx = 0 # 用于为线索相关的内部变量生成唯一名称
    for clue_data_item in clues: 
        clue_type = clue_data_item.get('type')
        clue_idx_str = str(clue_idx) # 将索引转为字符串，用于变量名
        clue_idx += 1

        if clue_type == 'WeaponClue': # 处理确定凶器线索
            weapon_name = clue_data_item['weapon']
            if weapon_name in weapon_vars:
                model.Add(weapon_vars[weapon_name] == 1) # 将指定凶器的变量设为真
                # 同时，将其他所有凶器的变量设为假
                for w, w_var in weapon_vars.items():
                    if w != weapon_name:
                        model.Add(w_var == 0)
            else: # 如果线索中的凶器名不在已知的凶器列表中
                 print(f"警告: WeaponClue 指定了未知的凶器 '{weapon_name}'")

        elif clue_type == 'ItemRoomTimeClue': # 处理物品-房间-时间线索
            item = clue_data_item['item']
            room = clue_data_item['room']
            time = clue_data_item.get('time') # time 可能为 None
            try:
                # 实体化该条件，并断言该条件必须为真
                condition_true_var = reify_item_at_location_time(item, room, time, f"irtc_{clue_idx_str}")
                model.Add(condition_true_var == 1)
            except ValueError as e: # 捕获因无效房间名/时间点等引发的错误
                print(f"跳过 ItemRoomTimeClue 因为发生错误: {e}. 线索: {clue_data_item}")


        elif clue_type == 'RelativeLocationClue': # 处理相对位置线索
            item1 = clue_data_item['item1']
            item2 = clue_data_item['item2']
            direction = clue_data_item['direction']
            # 当前简化实现：假设相对位置线索应用于第一个时间点
            time_val_for_relative_clue = processed_times[0]
            try:
                pos1_x, pos1_y = get_item_location_vars(item1, time_val_for_relative_clue)
                pos2_x, pos2_y = get_item_location_vars(item2, time_val_for_relative_clue)

                # 根据方向添加约束
                if direction == '南': # item1 在 item2 的南方 (行索引更大)
                    model.Add(pos1_x > pos2_x)
                    model.Add(pos1_y == pos2_y) # 列索引相同
                elif direction == '北': # item1 在 item2 的北方 (行索引更小)
                    model.Add(pos1_x < pos2_x)
                    model.Add(pos1_y == pos2_y) # 列索引相同
                elif direction == '东': # item1 在 item2 的东方 (列索引更大)
                    model.Add(pos1_y > pos2_y)
                    model.Add(pos1_x == pos2_x) # 行索引相同
                elif direction == '西': # item1 在 item2 的西方 (列索引更小)
                    model.Add(pos1_y < pos2_y)
                    model.Add(pos1_x == pos2_x) # 行索引相同
                else:
                    print(f"警告: RelativeLocationClue 中使用了未知的方向 '{direction}'")
            except ValueError as e: # 捕获因无效物品名等引发的错误
                print(f"跳过 RelativeLocationClue 因为发生错误: {e}. 线索: {clue_data_item}")


        elif clue_type == 'IfAndOnlyIfClue': # 处理当且仅当关系线索
            clue1_data = clue_data_item.get('clue1') # 获取第一个子线索
            clue2_data = clue_data_item.get('clue2') # 获取第二个子线索

            # 检查子线索是否有效且类型正确 (都应为 ItemRoomTimeClue)
            if not clue1_data or clue1_data.get('type') != 'ItemRoomTimeClue' or \
               not clue2_data or clue2_data.get('type') != 'ItemRoomTimeClue':
                print(f"警告: IfAndOnlyIfClue 需要两个 ItemRoomTimeClue 类型的子线索。跳过线索: {clue_data_item}")
                continue
            try:
                # 实体化第一个子线索的条件
                cond1_var = reify_item_at_location_time(
                    clue1_data['item'], clue1_data['room'], clue1_data.get('time'), f"iffc1_{clue_idx_str}"
                )
                # 实体化第二个子线索的条件
                cond2_var = reify_item_at_location_time(
                    clue2_data['item'], clue2_data['room'], clue2_data.get('time'), f"iffc2_{clue_idx_str}"
                )
                # 添加约束：两个条件的布尔变量必须相等 (即逻辑等价)
                model.Add(cond1_var == cond2_var)
            except ValueError as e: # 捕获因无效房间名/时间点/物品名等引发的错误
                 print(f"跳过 IfAndOnlyIfClue 因为其子线索发生错误: {e}. 线索: {clue_data_item}")
    
    # --- 求解模型 ---
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # --- 处理求解结果 ---
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE: # 如果找到最优解或可行解
        # 提取凶手
        solved_murderer = next((s for s, var in murderer_vars.items() if solver.Value(var)), "未确定") if suspects else "无嫌疑人"
        # 提取凶器
        solved_weapon = next((w for w, var in weapon_vars.items() if solver.Value(var)), "未确定") if weapons else "无凶器"
        
        # 提取凶杀时间
        solved_time_idx = solver.Value(murder_time_idx)
        solved_murder_time = processed_times[solved_time_idx]
        
        # 提取凶杀地点
        solved_murder_loc_x = solver.Value(murder_location_x)
        solved_murder_loc_y = solver.Value(murder_location_y)
        solved_murder_location = room_grid[solved_murder_loc_x][solved_murder_loc_y] if valid_room_coords_list else "地点无效"
        
        # 提取凶杀动机
        solved_motive_idx = solver.Value(murder_motive_idx)
        solved_murder_motive = processed_motives[solved_motive_idx]

        # 提取所有嫌疑人在所有时间点的位置
        result_suspect_locs = {}
        for s_name, s_loc_map in suspect_locations.items():
            result_suspect_locs[s_name] = {}
            for t_val, loc_vars_dict in s_loc_map.items(): 
                if isinstance(loc_vars_dict, dict) and 'x' in loc_vars_dict and 'y' in loc_vars_dict : 
                    r, c = solver.Value(loc_vars_dict['x']), solver.Value(loc_vars_dict['y'])
                    result_suspect_locs[s_name][t_val] = room_grid[r][c]
        
        # 提取所有凶器在所有时间点的位置
        result_weapon_locs = {}
        for w_name, w_loc_map in weapon_locations.items():
            result_weapon_locs[w_name] = {}
            for t_val, loc_vars_dict in w_loc_map.items(): 
                 if isinstance(loc_vars_dict, dict) and 'x' in loc_vars_dict and 'y' in loc_vars_dict :
                    r, c = solver.Value(loc_vars_dict['x']), solver.Value(loc_vars_dict['y'])
                    result_weapon_locs[w_name][t_val] = room_grid[r][c]
        
        # 构建动机结果（当前为占位符，除非有特定动机分配线索）
        result_motives = {s: "未知 (需动机分配线索)" for s in suspects}
        # 如果凶手已确定，将其动机设为已解出的全局凶杀动机
        if solved_murderer != "未确定" and solved_murderer != "无嫌疑人" and solved_murderer in result_motives:
            result_motives[solved_murderer] = solved_murder_motive

        # 返回包含所有解的字典
        return {
            'murderer': solved_murderer,
            'weapon': solved_weapon,
            'murder_time': solved_murder_time,
            'murder_location': solved_murder_location,
            'murder_motive': solved_murder_motive,
            'suspect_locations': result_suspect_locs,
            'weapon_locations': result_weapon_locs,
            'motives': result_motives 
        }
    elif status == cp_model.INFEASIBLE: # 如果模型无解
        # 可以取消注释下一行来打印模型原型以进行调试
        # print(model.Proto()) 
        return {"error": "模型无可行解 (INFEASIBLE)"}
    elif status == cp_model.MODEL_INVALID: # 如果模型本身无效
        return {"error": f"模型无效 (MODEL_INVALID)\n{model.Validate()}"}
    else: # 其他未知求解器状态
        return {"error": f"求解器状态未知: {status}"}

# --- 示例调用 (与用户提供的一致) ---
'''
result = solver_tool(
    victim="博迪",
    suspects=["玫瑰夫人", "蜜桃小姐"],
    weapons=["绳索", "马蹄铁"],
    motives=[], 
    room_grid=[
        ["书房"], 
        ["餐厅"]
    ],
    times=[],
    clues=[
        {
            "type": "WeaponClue",
            "weapon": "绳索"
        },
        {
            "type": "IfAndOnlyIfClue",
            "clue1": {
                "type": "ItemRoomTimeClue",
                "item": "马蹄铁",
                "room": "书房",
                "time": None 
            },
            "clue2": {
                "type": "ItemRoomTimeClue",
                "item": "博迪",
                "room": "书房",
                "time": None
            }
        },
        {
            "type": "RelativeLocationClue",
            "item1": "绳索",
            "item2": "蜜桃小姐",
            "direction": "南"
        }
    ]
)
'''

if __name__ == "__main__":
    result = solver_tool(
        victim="博迪",
        # 嫌疑人列表
    suspects=["布鲁内特先生", "怀特夫人"],
    
    # 凶器列表
    weapons=["左轮手枪", "绳索"],
    
    # 动机列表（这里没有提供动机信息，使用空列表）
    motives=[],
    
    # 房间布局网格
    room_grid=[
        ["大厅"], 
        ["马车房"]
    ],
    
    # 时间点（只有一个时间点，所以用空列表）
    times=[],
    
    # 线索列表
    clues=[
        # 1. 确定凶器线索：致命伤来自左轮手枪
        {
            "type": "WeaponClue",
            "weapon": "左轮手枪"
        },
        
        # 2. 或关系线索：博迪先生曾在大厅出现，或者布鲁内特先生曾在大厅出现
        {
            "type": "IfAndOnlyIfClue",
            "clue1": {
                "type": "ItemRoomTimeClue",
                "item": "博迪",
                "room": "大厅",
                "time": None
            },
            "clue2": {
                "type": "ItemRoomTimeClue",
                "item": "布鲁内特先生",
                "room": "大厅",
                "time": None
            }
        },
        
        # 3. 相对位置线索：布鲁内特先生当时所在的位置，恰好在绳索所在房间的正南方
        {
            "type": "RelativeLocationClue",
            "item1": "布鲁内特先生",
            "item2": "绳索",
            "direction": "南"
        }
        ]   
    )
    print(result)