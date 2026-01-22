import pandas as pd


def DirectMatching(MaterialInformation, Orders):
    DirectFinalTable = pd.DataFrame()  # 套料数据
    DirectUtilizationTable = pd.DataFrame()  # 材料利用率数据

    # 找到原材料中的钢卷
    SteelRollData = MaterialInformation[MaterialInformation['Material'] == '钢卷']
    SteelWidths = SteelRollData['Width'].unique()  # 所用钢卷的唯一宽度

    Rows = []  # 储存匹配成功的订单序号
    Identifiers = []  # 储存对应的钢卷号
    for i in Orders.index:  # 使用索引遍历
        OrderProcess = Orders.loc[i, 'ProcessOrder']  # 读取订单工艺

        # 处理可能的NaN值（将NaN转为空字符串）
        if pd.isna(OrderProcess):
            OrderProcess = ""
        else:
            OrderProcess = str(OrderProcess)  # 强制转为字符串

        # 判断是否存在拉丝工艺，若存在长宽不可调换
        if 'Brushed' in OrderProcess:
            OrderWidth = Orders.loc[i, 'Width']  # 单个宽度
            OrderLength = Orders.loc[i, 'Length'] * Orders.loc[i, 'Quantity']  # 订单总长度
            match = OrderWidth in SteelWidths  # 判断订单宽度是否与钢卷宽度一直
            if match:  # 如果一直则储存订单序号
                SelectedSteelRoll = SteelRollData[SteelRollData['Width'] == OrderWidth]
                found = False  # 标志变量，是否找到合适钢卷
                for idx, row in SelectedSteelRoll.iterrows():
                    if row['Length'] >= OrderLength:
                        # print(SteelRollData.loc[row.name, 'Length'])
                        # 记录Identifier
                        SteelRollIdentifier = row['Identifier']
                        # 更新MaterialInformation中对应钢卷的Length，注意要找到原始SteelRollData中的那一行更新
                        MaterialInformation.loc[row.name, 'Length'] -= OrderLength
                        # print(SteelRollData.loc[row.name, 'Length'])
                        found = True
                        break  # 找到就退出
                if found:
                    Rows.append(i)
                    Identifiers.append(SteelRollIdentifier)
        else:  # 不存在拉丝工艺，进行长宽调换
            OrderWidth1 = Orders.loc[i, 'Width']
            OrderWidth2 = Orders.loc[i, 'Length']
            logic1 = OrderWidth1 in SteelWidths
            logic2 = OrderWidth2 in SteelWidths
            if logic1 or logic2:
                if logic1:
                    OrderWidth = OrderWidth1  # 不交换长宽
                    SelectedSteelRoll = SteelRollData[SteelRollData['Width'] == OrderWidth]
                    OrderLength = Orders.loc[i, 'Length'] * Orders.loc[i, 'Quantity']  # 订单总长度
                    found = False  # 标志变量，是否找到合适钢卷
                    for idx, row in SelectedSteelRoll.iterrows():
                        if row['Length'] >= OrderLength:
                            # print(SteelRollData.loc[row.name, 'Length'])
                            # 记录Identifier
                            SteelRollIdentifier = row['Identifier']
                            # 更新MaterialInformation中对应钢卷的Length，注意要找到原始SteelRollData中的那一行更新
                            MaterialInformation.loc[row.name, 'Length'] -= OrderLength
                            # print(SteelRollData.loc[row.name, 'Length'])
                            found = True
                            break  # 找到就退出
                    if found:
                        Rows.append(i)
                        Identifiers.append(SteelRollIdentifier)
                elif logic2:
                    OrderWidth = OrderWidth2 # 交换长宽
                    # 交换 Width 和 Length
                    temp = Orders.loc[i, 'Width']
                    Orders.loc[i, 'Width'] = Orders.loc[i, 'Length']
                    Orders.loc[i, 'Length'] = temp
                    SelectedSteelRoll = SteelRollData[SteelRollData['Width'] == OrderWidth]
                    OrderLength = Orders.loc[i, 'Width'] * Orders.loc[i, 'Quantity']  # 订单总长度
                    found = False  # 标志变量，是否找到合适钢卷
                    for idx, row in SelectedSteelRoll.iterrows():
                        if row['Length'] >= OrderLength:
                            # print(SteelRollData.loc[row.name, 'Length'])
                            # 记录Identifier
                            SteelRollIdentifier = row['Identifier']
                            # 更新MaterialInformation中对应钢卷的Length，注意要找到原始SteelRollData中的那一行更新
                            MaterialInformation.loc[row.name, 'Length'] -= OrderLength
                            # print(SteelRollData.loc[row.name, 'Length'])
                            found = True
                            break  # 找到就退出
                    if found:
                        Rows.append(i)
                        Identifiers.append(SteelRollIdentifier)

    RightOrders = Orders.loc[Rows].copy()  # 直接匹配成功的订单
    RightOrders['SteelRollIdentifier'] = Identifiers
    RemainOrders = Orders.drop(Rows).reset_index(drop=True)  # 剩余待分类订单

    # 构建FinalTable
    if not RightOrders.empty:
        # DirectFinalTable = RightOrders[['Width', 'NO', 'Quantity', 'Width', 'Length', 'ProcessOrder']].copy()
        # DirectFinalTable['UsedLength'] = DirectFinalTable['Length'] * DirectFinalTable['Quantity']
        # DirectFinalTable.columns = ['SteelWidth', 'Sequence', 'UsedQuantity', 'Width', 'Length', 'Process',
        #                             'UsedLength']
        # DirectFinalTable = DirectFinalTable[
        #     ['SteelWidth', 'Sequence', 'UsedQuantity', 'Width', 'Length', 'UsedLength', 'Process']]
        # 新输出格式
        DirectFinalTable = RightOrders[['SteelRollIdentifier', 'NO', 'docDate', 'Quantity', 'deliveryDate', 'materialCode',
                                   'ProcessOrder', 
                                   'Width', 'Length', 'Width', 'Thickness']].copy() # 从RightOrders这个DataFrame中，按指定的列顺序取出需要的字段组成新的表DirectFinalTable
        DirectFinalTable['UsedLength'] = DirectFinalTable['Length'] * DirectFinalTable['Quantity'] # 新增一列UsedLength
        DirectFinalTable['MatchMultiplier'] = 1 # 匹配倍数标识
        """
        FinalTable最终格式
        """
        DirectFinalTable.columns = ['SteelRollIdentifier', 'docNo', 'docDate', 'UsedQuantity', 'deliveryDate', 'materialCode',
                               'surfaceDescCombination', 
                               'SteelWidth', 'Length', 'Width', 'Thickness', 'UsedLength', 'MatchMultiplier'] # 重命名DirectFinalTable的全部列名
        DirectFinalTable['dimensionsDesc'] = (
                DirectFinalTable['Thickness'].astype(str) + '*' +
                DirectFinalTable['Length'].astype(str) + '*' +
                DirectFinalTable['SteelWidth'].astype(str)
        )
    # 构建 UtilizationTable
    if not RightOrders.empty:
        DirectUtilizationTable = RightOrders[['Width', 'NO']].copy()
        DirectUtilizationTable['UsedLength'] = RightOrders['Length'] * RightOrders['Quantity']
        DirectUtilizationTable['UsedWidth'] = DirectUtilizationTable['Width']
        DirectUtilizationTable['MaterialUtilization'] = 100.0
        """
        UtilizationTable最终格式
        """
        DirectUtilizationTable.columns = ['SteelWidth', 'OrderSequence', 'UsedLength', 'UsedWidth',
                                          'MaterialUtilization']

    return RemainOrders, DirectFinalTable, DirectUtilizationTable, MaterialInformation


if __name__ == "__main__":
    Orders = pd.read_excel('订单.xlsx', sheet_name='订单')  # 订单数据
    MaterialInformation = pd.read_excel('库存.xlsx', sheet_name='原材料情况')  # 原材料数据
    SelfOrders, DirectFinalTable, DirectUtilizationTable, ChangedMaterialInformation = DirectMatching(
        MaterialInformation,
        Orders)

    ChangedMaterialInformation.to_excel('ChangedMaterialInformation.xlsx', index=False)
    DirectFinalTable.to_excel('DirectFinalTable.xlsx', index=False)
    DirectUtilizationTable.to_excel('DirectUtilizationTable.xlsx', index=False)
    SelfOrders.to_excel('SelfOrders.xlsx', index=False)
