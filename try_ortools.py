from ortools.sat.python import cp_model


def solve_murder_case():
    model = cp_model.CpModel()

    # ====== 定义枚举值 ======
    ROOMS = {'大厅': 1, '马车房': 2}
    SUSPECTS = {'布鲁内特': 0, '怀特夫人': 1}
    WEAPONS = {'左轮手枪': 0, '绳索': 1}

    # ====== 创建决策变量 ======
    # 命案房间（1或2）
    crime_room = model.new_int_var(1, 2, 'crime_room')

    # 嫌疑人位置（网页2中的房间位置逻辑）
    brunet_room = model.new_int_var(1, 2, 'brunet_room')
    white_room = model.new_int_var(1, 2, 'white_room')

    # 凶器位置（网页4的约束设置方法）
    revolver_room = model.new_int_var(1, 2, 'revolver_room')
    rope_room = model.new_int_var(1, 2, 'rope_room')

    # 凶手身份（布尔变量）
    is_brunet_killer = model.new_bool_var('is_brunet_killer')
    is_white_killer = model.new_bool_var('is_white_killer')

    # 添加布尔变量用于约束3
    rope_in_room1 = model.new_bool_var('rope_in_room1')
    rope_in_room2 = model.new_bool_var('rope_in_room2')

    # 添加布尔变量用于约束4
    crime_in_room1 = model.new_bool_var('crime_in_room1')
    brunet_in_room1 = model.new_bool_var('brunet_in_room1')

    # ====== 核心约束 ======
    # 约束1：凶手唯一性（网页5的逻辑约束）
    model.add_exactly_one([is_brunet_killer, is_white_killer])

    # 约束2：命案现场条件（网页1的约束编程思想）
    model.add(crime_room == revolver_room)  # 致命伤来自左轮手枪（网页3的目标约束）

    # 约束3：布鲁内特位置在绳索房间正南方（网页6的空间逻辑）
    model.add(rope_room == 1).only_enforce_if(rope_in_room1)
    model.add(rope_room == 2).only_enforce_if(rope_in_room2)
    model.add(brunet_room > rope_room)

    # 约束4：博迪或布鲁内特在大厅（网页2的布尔或逻辑）
    model.add(crime_room == 1).only_enforce_if(crime_in_room1)
    model.add(brunet_room == 1).only_enforce_if(brunet_in_room1)
    model.add_at_least_one([crime_in_room1, brunet_in_room1])

    # 约束5：凶手与被害人同处一室
    model.add(crime_room == brunet_room).only_enforce_if(is_brunet_killer)
    model.add(crime_room == white_room).only_enforce_if(is_white_killer)

    # 约束6：凶手必须与被害人同处一室，且该房间内至少有一件凶器
    model.add(crime_room == revolver_room).only_enforce_if(is_brunet_killer)
    model.add(crime_room == revolver_room).only_enforce_if(is_white_killer)

    # ====== 求解与解析 ======
    solver = cp_model.CpSolver()
    status = solver.solve(model)

    if status == cp_model.OPTIMAL:
        # 解析结果（网页5的数据处理方式）
        room_mapping = {1: "大厅", 2: "马车房"}
        return {
            'A': '布鲁内特' if solver.value(is_brunet_killer) else '怀特夫人',
            'B': room_mapping[solver.value(crime_room)],
            'C': room_mapping[solver.value(white_room)],
            'D': room_mapping[solver.value(brunet_room)],
            'E': room_mapping[solver.value(revolver_room)],
            'F': room_mapping[solver.value(rope_room)]
        }
    else:
        return {"error": "无可行解"}


# 执行求解
result = solve_murder_case()
print(f"""
A. {result['A']}
B. {result['B']}
C. {result['C']}
D. {result['D']}
E. {result['E']}
F. {result['F']}""")