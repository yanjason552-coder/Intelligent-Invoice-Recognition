import pandas as pd
import numpy as np
import math


def self_matching(MaterialInformation, RemainOrders):
    # 套料数据初始化为空DataFrame
    SelfFinalTable = pd.DataFrame()
    # 用列表逐步收集利用率数据（每条订单一行）
    utilization_data = []

    # 找到原材料中的钢卷
    SteelRollData = MaterialInformation[MaterialInformation['Material'] == '钢卷']
    SteelWidths = SteelRollData['Width'].unique()

    # 用于逐步收集匹配订单信息，每个元素存一条订单的完整数据
    matched_orders_data = []
    for i in RemainOrders.index:
        OrderProcess = RemainOrders.loc[i, 'ProcessOrder']

        # 处理工艺信息的 NaN 值
        if pd.isna(OrderProcess):
            OrderProcess = ""
        else:
            OrderProcess = str(OrderProcess)

        # 判断是否存在拉丝工艺，若存在长宽不可调换
        if 'Brushed' in OrderProcess:
            order_w = RemainOrders.loc[i, 'Width']
            order_len = RemainOrders.loc[i, 'Length'] * RemainOrders.loc[i, 'Quantity']

            best_steel_roll = None
            best_k = 0
            for idx, row in SteelRollData.iterrows():
                max_possible_k = int(row['Width'] / order_w)
                for k in range(1, max_possible_k + 1):
                    ratio = k * order_w / row['Width']
                    if 0.95 < ratio < 1:
                        if row['Length'] >= order_len and k > best_k:
                            best_steel_roll = row
                            best_k = k
                            break

            if best_steel_roll is not None:
                # 先计算利用率相关参数
                used_length = math.ceil(RemainOrders.loc[i, 'Quantity'] / best_k) * RemainOrders.loc[i, 'Length']
                order_width = RemainOrders.loc[i, 'Width']
                order_length = RemainOrders.loc[i, 'Length']
                used_quantity = RemainOrders.loc[i, 'Quantity']
                steel_width = best_steel_roll['Width']

                # 实时计算利用率
                used_width = order_width * best_k
                real_area = order_length * order_width * used_quantity
                used_area = steel_width * used_length
                material_utilization = 100.0 * real_area / used_area

                # 判断利用率是否达标
                if material_utilization > 95:
                    # 达标则收集该订单匹配信息并添加到数据列表
                    matched_order = {
                        'SteelRollIdentifier': best_steel_roll['Identifier'],
                        'docNo': RemainOrders.loc[i, 'NO'],
                        'docDate': RemainOrders.loc[i, 'docDate'],
                        'UsedQuantity': used_quantity,
                        'deliveryDate': RemainOrders.loc[i, 'deliveryDate'],
                        'materialCode': RemainOrders.loc[i, 'materialCode'],
                        'surfaceDescCombination': OrderProcess,
                        'SteelWidth': steel_width,
                        'Length': order_length,
                        'Width': order_width,
                        'Thickness': RemainOrders.loc[i, 'Thickness'],
                        'UsedLength': used_length,
                        'MatchMultiplier': best_k
                    }
                    matched_orders_data.append(matched_order)

                    utilization_row = {
                        'SteelWidth': order_width,
                        'OrderSequence': RemainOrders.loc[i, 'NO'],
                        'UsedLength': used_length,
                        'UsedWidth': used_width,
                        'MaterialUtilization': material_utilization
                    }
                    utilization_data.append(utilization_row)
                    # 扣减钢卷长度
                    MaterialInformation.loc[best_steel_roll.name, 'Length'] -= order_len

        else:
            ow1 = RemainOrders.loc[i, 'Width']
            ow2 = RemainOrders.loc[i, 'Length']

            best_option = None
            best_k = 0
            best_orientation = None

            for orientation in ['w', 'l']:
                order_w = ow1 if orientation == 'w' else ow2
                order_l = ow2 if orientation == 'w' else ow1
                order_len = order_l * RemainOrders.loc[i, 'Quantity']

                for idx, row in SteelRollData.iterrows():
                    max_possible_k = int(row['Width'] / order_w)
                    for k in range(1, max_possible_k + 1):
                        ratio = k * order_w / row['Width']
                        if 0.95 < ratio < 1:
                            if row['Length'] >= order_len and k > best_k:
                                best_option = row
                                best_k = k
                                best_orientation = orientation
                                break

            if best_option is not None:
                order_w = ow1 if best_orientation == 'w' else ow2
                order_l = ow2 if best_orientation == 'w' else ow1
                order_len = order_l * RemainOrders.loc[i, 'Quantity']
                used_quantity = RemainOrders.loc[i, 'Quantity']
                steel_width = best_option['Width']
                used_length = math.ceil(used_quantity / best_k) * order_l

                # 实时计算利用率
                used_width = order_w * best_k
                real_area = order_l * order_w * used_quantity
                used_area = steel_width * used_length
                material_utilization = 100.0 * real_area / used_area

                # 判断利用率是否达标
                if material_utilization > 95:
                    # 达标则扣减钢卷长度并收集订单信息
                    MaterialInformation.loc[best_option.name, 'Length'] -= order_len
                    if best_orientation == 'l':
                        # 若调换长宽，更新订单长宽
                        RemainOrders.loc[i, 'Width'], RemainOrders.loc[i, 'Length'] = order_w, order_l

                    matched_order = {
                        'SteelRollIdentifier': best_option['Identifier'],
                        'docNo': RemainOrders.loc[i, 'NO'],
                        'docDate': RemainOrders.loc[i, 'docDate'],
                        'UsedQuantity': used_quantity,
                        'deliveryDate': RemainOrders.loc[i, 'deliveryDate'],
                        'materialCode': RemainOrders.loc[i, 'materialCode'],
                        'surfaceDescCombination': OrderProcess,
                        'SteelWidth': steel_width,
                        'Length': order_l,  # 可能是调换后的值
                        'Width': order_w,  # 可能是调换后的值
                        'Thickness': RemainOrders.loc[i, 'Thickness'],
                        'UsedLength': used_length,
                        'MatchMultiplier': best_k
                    }
                    matched_orders_data.append(matched_order)

                    utilization_row = {
                        'SteelWidth': order_w,
                        'OrderSequence': RemainOrders.loc[i, 'NO'],
                        'UsedLength': used_length,
                        'UsedWidth': used_width,
                        'MaterialUtilization': material_utilization
                    }
                    utilization_data.append(utilization_row)

    # 将收集的匹配订单数据转成 DataFrame
    SelfOrders = pd.DataFrame(matched_orders_data)
    matched_ids = SelfOrders['docNo'].unique()  # 提取已匹配订单的编号
    r_orders = RemainOrders[~RemainOrders['NO'].isin(matched_ids)].reset_index(drop=True)

    # 构建 FinalTable
    if not SelfOrders.empty:
        SelfFinalTable = SelfOrders.copy()

        SelfFinalTable['dimensionsDesc'] = (
                SelfFinalTable['Thickness'].astype(str) + '*' +
                SelfFinalTable['Length'].astype(str) + '*' +
                SelfFinalTable['SteelWidth'].astype(str)
        )

    # 构建 UtilizationTable（从列表转成DataFrame）
    SelfUtilizationTable = pd.DataFrame(utilization_data)

    return r_orders, SelfFinalTable, SelfUtilizationTable, MaterialInformation


# 调用测试（仅独立运行时执行，作为子函数时不执行）
if __name__ == "__main__":
    RemainOrders = pd.read_excel('SelfOrders.xlsx', sheet_name='Sheet1')
    MaterialInformation = pd.read_excel('ChangedMaterialInformation.xlsx', sheet_name='Sheet1')
    r_orders, SelfFinalTable, SelfUtilizationTable, MaterialInformation = self_matching(MaterialInformation,
                                                                                        RemainOrders)

    MaterialInformation.to_excel('MaterialInformation_self.xlsx', index=False)
    SelfFinalTable.to_excel('SelfFinalTable.xlsx', index=False)
    SelfUtilizationTable.to_excel('SelfUtilizationTable.xlsx', index=False)
    r_orders.to_excel('r_orders.xlsx', index=False)

