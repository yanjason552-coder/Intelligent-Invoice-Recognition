import pandas as pd
import numpy as np
import math
import itertools


def Failed_matching(MaterialInformation_failed, FailedOrders):
    """
    处理未匹配订单的函数，无利用率限制，只取最高利用率匹配

    参数:
        MaterialInformation_failed (pd.DataFrame): 原材料信息表（含钢卷数据）
        FailedOrders (pd.DataFrame): 未匹配订单表

    返回:
        FailedTable (pd.DataFrame): 匹配成功的订单详情
        FailedUtilizationTable (pd.DataFrame): 利用率统计
        MaterialInformation_updated (pd.DataFrame): 更新后的钢卷信息
    """
    # 初始化结果数据结构
    matched_orders_data = []
    utilization_data = []

    # 复制数据避免修改原输入
    MaterialInformation = MaterialInformation_failed.copy()
    Orders = FailedOrders.copy()

    # 筛选钢卷数据
    SteelRollData = MaterialInformation[MaterialInformation['Material'] == '钢卷'].copy()
    if SteelRollData.empty:
        return pd.DataFrame(), pd.DataFrame(), MaterialInformation

    # 分离数量为1和数量大于1的订单
    single_orders = Orders[Orders['Quantity'] == 1].copy().reset_index(drop=True)
    multi_orders = Orders[Orders['Quantity'] > 1].copy().reset_index(drop=True)

    # 处理数量大于1的订单（类似self_matching逻辑，无利用率限制）
    for i in multi_orders.index:
        OrderProcess = multi_orders.loc[i, 'ProcessOrder']
        OrderProcess = str(OrderProcess) if not pd.isna(OrderProcess) else ""

        best_steel = None
        best_k = 0
        best_utilization = -1
        best_orientation = None
        best_order_w = 0
        best_order_l = 0

        # 拉丝工艺：长宽不可调换
        if 'Brushed' in OrderProcess:
            order_w = multi_orders.loc[i, 'Width']
            order_l = multi_orders.loc[i, 'Length']
            order_q = multi_orders.loc[i, 'Quantity']
            order_total_len = order_l * order_q

            for idx, steel in SteelRollData.iterrows():
                max_possible_k = int(steel['Width'] / order_w) if order_w != 0 else 0
                for k in range(1, max_possible_k + 1):
                    if steel['Length'] >= order_total_len:
                        # 计算利用率
                        used_width = order_w * k
                        used_length = math.ceil(order_q / k) * order_l
                        real_area = order_w * order_l * order_q
                        used_area = steel['Width'] * used_length
                        utilization = real_area / used_area if used_area != 0 else 0

                        # 只关注最高利用率，无阈值限制
                        if utilization > best_utilization:
                            best_utilization = utilization
                            best_steel = steel
                            best_k = k
                            best_order_w = order_w
                            best_order_l = order_l

        else:
            # 非拉丝工艺：长宽可调换
            ow1 = multi_orders.loc[i, 'Width']
            ow2 = multi_orders.loc[i, 'Length']
            order_q = multi_orders.loc[i, 'Quantity']

            for orientation in ['w', 'l']:
                order_w = ow1 if orientation == 'w' else ow2
                order_l = ow2 if orientation == 'w' else ow1
                order_total_len = order_l * order_q

                for idx, steel in SteelRollData.iterrows():
                    max_possible_k = int(steel['Width'] / order_w) if order_w != 0 else 0
                    for k in range(1, max_possible_k + 1):
                        if steel['Length'] >= order_total_len:
                            # 计算利用率
                            used_width = order_w * k
                            used_length = math.ceil(order_q / k) * order_l
                            real_area = order_w * order_l * order_q
                            used_area = steel['Width'] * used_length
                            utilization = real_area / used_area if used_area != 0 else 0

                            if utilization > best_utilization:
                                best_utilization = utilization
                                best_steel = steel
                                best_k = k
                                best_orientation = orientation
                                best_order_w = order_w
                                best_order_l = order_l

        # 记录最佳匹配
        if best_steel is not None and best_utilization > 0:
            # 扣减钢卷长度
            used_length = math.ceil(multi_orders.loc[i, 'Quantity'] / best_k) * best_order_l
            MaterialInformation.loc[best_steel.name, 'Length'] -= used_length
            if MaterialInformation.loc[best_steel.name, 'Length'] < 0:
                MaterialInformation.loc[best_steel.name, 'Length'] = 0

            # 记录匹配信息
            matched_order = {
                'SteelRollIdentifier': best_steel['Identifier'],
                'docNo': multi_orders.loc[i, 'itemSeq'] if 'itemSeq' in multi_orders.columns else multi_orders.loc[
                    i, 'NO'],
                'docDate': multi_orders.loc[i, 'docDate'],
                'UsedQuantity': multi_orders.loc[i, 'Quantity'],
                'deliveryDate': multi_orders.loc[i, 'deliveryDate'],
                'materialCode': multi_orders.loc[i, 'materialCode'],
                'surfaceDescCombination': OrderProcess,

                'SteelWidth': best_steel['Width'],
                'Length': best_order_l,
                'Width': best_order_w,
                'Thickness': multi_orders.loc[i, 'Thickness'],
                'UsedLength': used_length,
                'MatchMultiplier': best_k
            }
            matched_orders_data.append(matched_order)

            utilization_row = {
                'SteelWidth': best_steel['Width'],
                'OrderSequence': multi_orders.loc[i, 'itemSeq'] if 'itemSeq' in multi_orders.columns else
                multi_orders.loc[i, 'NO'],
                'UsedLength': used_length,
                'UsedWidth': best_order_w * best_k,
                'MaterialUtilization': round(best_utilization * 100, 2)
            }
            utilization_data.append(utilization_row)

    # 处理数量为1的订单（类似two_sided_matching的组合逻辑，无利用率限制）
    if len(single_orders) >= 2:
        all_combinations = list(itertools.combinations(range(len(single_orders)), 2))
        best_combinations = []

        # 寻找所有可能组合的最佳匹配
        for combo in all_combinations:
            idx1, idx2 = combo
            order1 = single_orders.iloc[idx1]
            order2 = single_orders.iloc[idx2]

            # 订单1信息
            process1 = str(order1['ProcessOrder']) if not pd.isna(order1['ProcessOrder']) else ""
            widths1 = [order1['Width']] if 'Brushed' in process1 else [order1['Width'], order1['Length']]

            # 订单2信息
            process2 = str(order2['ProcessOrder']) if not pd.isna(order2['ProcessOrder']) else ""
            widths2 = [order2['Width']] if 'Brushed' in process2 else [order2['Width'], order2['Length']]

            # 遍历所有可能的宽度组合
            for w1 in widths1:
                for w2 in widths2:
                    total_width = w1 + w2

                    # 遍历所有钢卷
                    for steel_idx, steel in SteelRollData.iterrows():
                        if steel['Length'] <= 0:
                            continue

                        steel_width = steel['Width']
                        width_ratio = total_width / steel_width if steel_width != 0 else 0

                        # 宽度需能容纳组合
                        if width_ratio <= 1.0:
                            # 计算订单所需长度
                            len1 = order1['Length'] if w1 == order1['Width'] else order1['Width']
                            len2 = order2['Length'] if w2 == order2['Width'] else order2['Width']
                            used_length = max(len1, len2)

                            if steel['Length'] >= used_length:
                                # 计算面积利用率
                                real_area = (w1 * len1) + (w2 * len2)
                                steel_used_area = steel_width * used_length
                                total_ratio = real_area / steel_used_area if steel_used_area != 0 else 0

                                best_combinations.append({
                                    'combo': combo,
                                    'steel': steel,
                                    'steel_idx': steel_idx,
                                    'w1': w1,
                                    'len1': len1,
                                    'w2': w2,
                                    'len2': len2,
                                    'used_length': used_length,
                                    'utilization': total_ratio
                                })

        # 按利用率排序，选择最高的组合（避免重复匹配）
        best_combinations.sort(key=lambda x: x['utilization'], reverse=True)
        matched_indices = set()

        for combo_info in best_combinations:
            idx1, idx2 = combo_info['combo']
            if idx1 in matched_indices or idx2 in matched_indices:
                continue

            # 扣减钢卷长度
            steel = combo_info['steel']
            steel_idx = combo_info['steel_idx']
            MaterialInformation.loc[steel_idx, 'Length'] -= combo_info['used_length']
            if MaterialInformation.loc[steel_idx, 'Length'] < 0:
                MaterialInformation.loc[steel_idx, 'Length'] = 0

            # 记录订单1信息
            order1 = single_orders.iloc[idx1]
            matched_order1 = {
                'SteelRollIdentifier': steel['Identifier'],
                'docNo': order1['itemSeq'] if 'itemSeq' in order1.index else order1['NO'],
                'docDate': order1['docDate'],
                'UsedQuantity': 1,
                'deliveryDate': order1['deliveryDate'],
                'materialCode': order1['materialCode'],
                'surfaceDescCombination': order1['ProcessOrder'],

                'SteelWidth': steel['Width'],
                'Length': combo_info['len1'],
                'Width': combo_info['w1'],
                'Thickness': order1['Thickness'],
                'UsedLength': combo_info['used_length'],
                'MatchMultiplier': 1
            }
            matched_orders_data.append(matched_order1)

            # 记录订单2信息
            order2 = single_orders.iloc[idx2]
            matched_order2 = {
                'SteelRollIdentifier': steel['Identifier'],
                'docNo': order2['itemSeq'] if 'itemSeq' in order2.index else order2['NO'],
                'docDate': order2['docDate'],
                'UsedQuantity': 1,
                'deliveryDate': order2['deliveryDate'],
                'materialCode': order2['materialCode'],
                'surfaceDescCombination': order2['ProcessOrder'],

                'SteelWidth': steel['Width'],
                'Length': combo_info['len2'],
                'Width': combo_info['w2'],
                'Thickness': order2['Thickness'],
                'UsedLength': combo_info['used_length'],
                'MatchMultiplier': 1
            }
            matched_orders_data.append(matched_order2)

            # 记录利用率信息
            utilization_row = {
                'SteelWidth': steel['Width'],
                'OrderSequence': f"{order1['itemSeq'] if 'itemSeq' in order1.index else order1['NO']}, {order2['itemSeq'] if 'itemSeq' in order2.index else order2['NO']}",
                'UsedLength': combo_info['used_length'],
                'UsedWidth': combo_info['w1'] + combo_info['w2'],
                'MaterialUtilization': round(combo_info['utilization'] * 100, 2)
            }
            utilization_data.append(utilization_row)

            # 标记已匹配
            matched_indices.add(idx1)
            matched_indices.add(idx2)

    # 构建结果表
    FailedTable = pd.DataFrame(matched_orders_data)
    FailedUtilizationTable = pd.DataFrame(utilization_data)

    # 处理尺寸描述列
    if not FailedTable.empty:
        FailedTable['dimensionsDesc'] = (
                FailedTable['Thickness'].astype(str) + '*' +
                FailedTable['Length'].astype(str) + '*' +
                FailedTable['SteelWidth'].astype(str)
        )

    return FailedTable, FailedUtilizationTable, MaterialInformation


# 补充调用测试：模拟另一批数据的匹配过程
if __name__ == "__main__":
    # 测试场景1：使用原始测试数据
    print("开始测试场景1：原始数据匹配")
    FailedOrders = pd.read_excel('FailedOrders.xlsx', sheet_name='Sheet1')
    MaterialInformation_input1 = pd.read_excel('MaterialInformation_updated.xlsx', sheet_name='Sheet1')

    FailedOrders1, BestMatches1, FailedTable, FailedUtilizationTable, MaterialInformation = two_sided_matching(
        MaterialInformation_input1, FailedOrders
    )

    # 保存场景1结果
    FailedOrders1.to_excel('FailedOrders_scenario1.xlsx', index=False)
    BestMatches1.to_excel('BestMatches_scenario1.xlsx', index=False)
    PairFinalTable1.to_excel('PairFinalTable_scenario1.xlsx', index=False)
    PairUtilizationTable1.to_excel('PairUtilizationTable_scenario1.xlsx', index=False)
    MaterialInformation_updated1.to_excel('MaterialInformation_updated_scenario1.xlsx', index=False)

    # 测试场景2：使用备用测试数据（可替换为实际备用文件路径）
    print("开始测试场景2：备用数据匹配")
    try:
        classifiedOrder2 = pd.read_excel('分类数据_备用.xlsx', sheet_name='分类结果')
        MaterialInformation_input2 = pd.read_excel('MaterialInformation_备用.xlsx', sheet_name='Sheet1')

        FailedOrders2, BestMatches2, PairFinalTable2, PairUtilizationTable2, MaterialInformation_updated2 = two_sided_matching(
            MaterialInformation_input2, classifiedOrder2
        )

        # 保存场景2结果
        FailedOrders2.to_excel('FailedOrders_scenario2.xlsx', index=False)
        BestMatches2.to_excel('BestMatches_scenario2.xlsx', index=False)
        PairFinalTable2.to_excel('PairFinalTable_scenario2.xlsx', index=False)
        PairUtilizationTable2.to_excel('PairUtilizationTable_scenario2.xlsx', index=False)
        MaterialInformation_updated2.to_excel('MaterialInformation_updated_scenario2.xlsx', index=False)
        print("场景2测试完成")
    except FileNotFoundError:
        print("场景2测试文件未找到，跳过该场景")

    print("所有测试场景执行完毕")