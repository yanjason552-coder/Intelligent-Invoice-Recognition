import pandas as pd
import numpy as np
import itertools
import math


def two_sided_matching(MaterialInformation, classifiedOrder):
    """
    双订单组合匹配函数（仅处理两个不同订单的组合，两种订单数量全部用尽）

    参数:
        MaterialInformation (pd.DataFrame): 原材料信息表（含钢卷数据）
        classifiedOrder (pd.DataFrame): 分类后的订单表（订单编号列名为itemSeq）

    返回:
        FailedOrders (pd.DataFrame): 未匹配订单
        BestMatches (pd.DataFrame): 所有组合的最佳匹配信息
        PairFinalTable (pd.DataFrame): 匹配成功的订单详情
        PairUtilizationTable (pd.DataFrame): 利用率统计
        MaterialInformation_updated (pd.DataFrame): 更新后的钢卷信息（实时扣减长度）
    """
    # 初始化结果数据结构
    PairFinalTable = pd.DataFrame()  # 匹配成功的订单详情
    PairUtilizationTable = pd.DataFrame()  # 利用率表
    best_matches_data = []  # 所有组合的最佳匹配信息
    matched_order_ids = set()  # 记录已匹配的订单ID（避免重复匹配）

    # 复制钢卷数据用于实时更新（不修改原输入）
    SteelRollData = MaterialInformation[MaterialInformation['Material'] == '钢卷'].copy()
    if SteelRollData.empty:
        print("无钢卷数据，直接返回所有订单为未匹配")
        return classifiedOrder, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), MaterialInformation

    # 获取分类总数，按类别处理
    ClassifyTotal = classifiedOrder['Classify'].nunique()

    for classIdx in range(1, ClassifyTotal + 1):
        # 筛选当前类别的订单
        current_orders = classifiedOrder[classifiedOrder['Classify'] == classIdx].copy()
        current_orders = current_orders[
            current_orders['Quantity'].notna() & (current_orders['Quantity'] > 0)
            ].reset_index(drop=True)  # 过滤无效订单（数量为0或NaN）
        order_count = len(current_orders)

        # 仅生成两个不同订单的组合（若订单数<2，跳过当前类别）
        if order_count < 2:
            continue  # 订单数不足，无法组合

        # 生成所有两个不同订单的组合（索引组合）
        all_combinations = list(itertools.combinations(range(order_count), 2))

        # 初始化当前类别的最佳组合参数
        best_ratio = 0.90  # 利用率阈值90%
        best_combination = None  # 最佳组合的订单索引
        best_steel_roll = None  # 最佳匹配钢卷
        best_width_details = ""  # 宽度组合详情
        best_used_length = 0  # 钢卷使用长度

        # 遍历所有钢卷
        for steel_idx, steel_roll in SteelRollData.iterrows():
            steel_width = steel_roll['Width']
            steel_remaining_length = SteelRollData.loc[steel_idx, 'Length']  # 实时剩余长度
            steel_id = steel_roll['Identifier']

            # 遍历所有双订单组合
            for combo in all_combinations:
                idx1, idx2 = combo  # 两个订单的索引
                order1 = current_orders.iloc[idx1]
                order2 = current_orders.iloc[idx2]

                # 订单1信息（处理工艺和可能的宽度）
                process1 = str(order1['ProcessOrder']) if not pd.isna(order1['ProcessOrder']) else ""
                q1 = order1['Quantity']  # 订单1数量（用尽）
                # 拉丝工艺：仅用Width；否则可用Width或Length作为宽度
                widths1 = [order1['Width']] if 'Brushed' in process1 else [order1['Width'], order1['Length']]

                # 订单2信息
                process2 = str(order2['ProcessOrder']) if not pd.isna(order2['ProcessOrder']) else ""
                q2 = order2['Quantity']  # 订单2数量（用尽）
                widths2 = [order2['Width']] if 'Brushed' in process2 else [order2['Width'], order2['Length']]

                # 遍历所有可能的宽度组合（笛卡尔积）
                for w1 in widths1:
                    for w2 in widths2:
                        # 总宽度 = 订单1宽度×数量 + 订单2宽度×数量（用尽数量）
                        total_width = w1 + w2
                        # 宽度利用率 = 总宽度 / 钢卷宽度
                        width_ratio = total_width / steel_width if steel_width != 0 else 0

                        # 检查宽度利用率（90%-100%）和钢卷长度是否足够
                        if 0.90 < width_ratio <= 1.0:
                            # 计算订单所需长度（单张长度×数量，取两者最大值作为钢卷使用长度）
                            # 订单1实际长度：若宽度用了Length，则长度为原Width；否则为原Length
                            len1 = order1['Length'] if w1 == order1['Width'] else order1['Width']
                            # 订单2实际长度：同理
                            len2 = order2['Length'] if w2 == order2['Width'] else order2['Width']
                            required_len1 = len1 * q1  # 订单1总长度
                            required_len2 = len2 * q2  # 订单2总长度
                            used_length = max(required_len1, required_len2)  # 钢卷需提供的长度

                            # 检查钢卷剩余长度是否足够
                            if steel_remaining_length >= used_length:
                                # 计算总面积利用率（实际用料/钢卷使用面积）
                                real_area = (w1 * len1 * q1) + (w2 * len2 * q2)  # 订单总面积
                                steel_used_area = steel_width * used_length  # 钢卷使用面积
                                total_ratio = real_area / steel_used_area if steel_used_area != 0 else 0

                                # 筛选出利用率更高的组合
                                if total_ratio > best_ratio:
                                    best_ratio = total_ratio
                                    best_combination = combo
                                    best_steel_roll = (steel_roll, steel_idx)  # 钢卷数据及索引
                                    best_width_details = f"{q1}x{w1} + {q2}x{w2}"  # 宽度组合详情
                                    best_used_length = used_length
                                    # 记录订单实际长宽（可能已调换）
                                    best_order1_dim = (w1, len1)
                                    best_order2_dim = (w2, len2)

        # 处理最佳组合（若存在）
        if best_combination is not None and best_steel_roll is not None:
            idx1, idx2 = best_combination
            order1 = current_orders.iloc[idx1]
            order2 = current_orders.iloc[idx2]
            steel_roll, steel_idx = best_steel_roll
            steel_id = steel_roll['Identifier']
            w1, len1 = best_order1_dim
            w2, len2 = best_order2_dim

            # 1. 实时扣减钢卷长度
            SteelRollData.loc[steel_idx, 'Length'] -= best_used_length
            if SteelRollData.loc[steel_idx, 'Length'] < 0:
                SteelRollData.loc[steel_idx, 'Length'] = 0  # 避免负长度

            # 2. 记录匹配成功的订单到PairFinalTable（订单编号用itemSeq）
            # 订单1详情
            pair1 = {
                'SteelRollIdentifier': steel_id,
                'docNo': order1['itemSeq'],  # 订单编号列名：itemSeq
                'docDate': order1['docDate'],
                'UsedQuantity': order1['Quantity'],  # 数量已用尽
                'deliveryDate': order1['deliveryDate'],
                'materialCode': order1['materialCode'],
                'surfaceDescCombination': order1['ProcessOrder'],

                'SteelWidth': steel_roll['Width'],
                'Length': len1,  # 可能已调换的长度
                'Width': w1,  # 可能已调换的宽度
                'Thickness': order1['Thickness'],
                'UsedLength': best_used_length,
                'MatchMultiplier': 1  # 双订单组合倍数为1
            }
            # 订单2详情
            pair2 = {
                'SteelRollIdentifier': steel_id,
                'docNo': order2['itemSeq'],  # 订单编号列名：itemSeq
                'docDate': order2['docDate'],
                'UsedQuantity': order2['Quantity'],  # 数量已用尽
                'deliveryDate': order2['deliveryDate'],
                'materialCode': order2['materialCode'],
                'surfaceDescCombination': order2['ProcessOrder'],

                'SteelWidth': steel_roll['Width'],
                'Length': len2,  # 可能已调换的长度
                'Width': w2,  # 可能已调换的宽度
                'Thickness': order2['Thickness'],
                'UsedLength': best_used_length,
                'MatchMultiplier': 1
            }
            PairFinalTable = pd.concat([PairFinalTable, pd.DataFrame([pair1, pair2])], ignore_index=True)

            # 3. 记录利用率数据到PairUtilizationTable（订单编号用itemSeq）
            util_row = {
                'SteelWidth': steel_roll['Width'],
                'OrderSequence': f"{order1['itemSeq']}, {order2['itemSeq']}",  # 组合订单编号
                'UsedLength': best_used_length,
                'UsedWidth': w1 * order1['Quantity'] + w2 * order2['Quantity'],  # 总宽度
                'MaterialUtilization': round(best_ratio * 100, 2)  # 利用率（%）
            }
            PairUtilizationTable = pd.concat([PairUtilizationTable, pd.DataFrame([util_row])], ignore_index=True)

            # 4. 记录最佳匹配信息到BestMatches（订单编号用itemSeq）
            best_match_row = {
                'Classify': classIdx,
                'CombinationOrders': f"{order1['itemSeq']}, {order2['itemSeq']}",  # 组合订单
                'SteelRollIdentifier': steel_id,
                'SteelWidth': steel_roll['Width'],
                'TotalWidth': w1 * order1['Quantity'] + w2 * order2['Quantity'],
                'UsedLength': best_used_length,
                'MaterialUtilization': round(best_ratio * 100, 2),
                'IsMatched': True
            }
            best_matches_data.append(best_match_row)

            # 5. 标记已匹配订单（用itemSeq作为唯一标识）
            matched_order_ids.add(order1['itemSeq'])
            matched_order_ids.add(order2['itemSeq'])

    # 生成未匹配订单（未出现在已匹配集合中的订单，用itemSeq筛选）
    FailedOrders = classifiedOrder[~classifiedOrder['itemSeq'].isin(matched_order_ids)].reset_index(drop=True)

    # 生成BestMatches（若无匹配则为空）
    BestMatches = pd.DataFrame(best_matches_data)

    # 更新原始钢卷信息（同步实时扣减后的长度）
    MaterialInformation_updated = MaterialInformation.copy()
    steel_index = SteelRollData.index.intersection(MaterialInformation_updated.index)
    MaterialInformation_updated.loc[steel_index, 'Length'] = SteelRollData.loc[steel_index, 'Length']

    return FailedOrders, BestMatches, PairFinalTable, PairUtilizationTable, MaterialInformation_updated


# 调用测试
if __name__ == "__main__":
    # 读取分类后订单（classifiedOrder，订单编号列名为itemSeq）和原材料数据
    classifiedOrder = pd.read_excel('分类数据.xlsx', sheet_name='分类结果')
    MaterialInformation_input = pd.read_excel('MaterialInformation_self.xlsx', sheet_name='Sheet1')

    # 执行双订单组合匹配
    FailedOrders, BestMatches, PairFinalTable, PairUtilizationTable, MaterialInformation_updated = two_sided_matching(
        MaterialInformation_input, classifiedOrder
    )

    # 保存结果
    FailedOrders.to_excel('FailedOrders.xlsx', index=False)
    BestMatches.to_excel('BestMatches.xlsx', index=False)
    PairFinalTable.to_excel('PairFinalTable.xlsx', index=False)
    PairUtilizationTable.to_excel('PairUtilizationTable.xlsx', index=False)
    MaterialInformation_updated.to_excel('MaterialInformation_updated.xlsx', index=False)

    print("双订单组合匹配完成，输出文件：")
    print("1. FailedOrders.xlsx（未匹配订单）")
    print("2. BestMatches.xlsx（最佳组合匹配信息）")
    print("3. PairFinalTable.xlsx（匹配成功的订单详情）")
    print("4. PairUtilizationTable.xlsx（利用率统计）")
    print("5. MaterialInformation_updated.xlsx（更新后的钢卷信息）")