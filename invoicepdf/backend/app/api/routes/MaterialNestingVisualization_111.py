import pandas as pd
import numpy as np

# 在一个 Excel 文件里每个钢卷对应一个工作表


def MaterialNestingVisualization(SortedFinaltable, MaterialInformation):
    """
    计算每个钢卷上的订单坐标信息（简化版本）
    
    参数:
        SortedFinaltable: 排序后的最终套料表
        MaterialInformation: 材料信息表
        
    返回:
        all_coordinates: 所有钢卷的坐标信息列表，每个元素包含钢卷标识和坐标记录
    """
    # 获取唯一钢卷标识 - 检查列名是否存在
    if 'SteelIdentifier' in SortedFinaltable.columns:
        steel_identifier_col = 'SteelIdentifier'
    elif 'SteelRollIdentifier' in SortedFinaltable.columns:
        steel_identifier_col = 'SteelRollIdentifier'
    else:
        print(f"警告: 未找到钢卷标识列，可用列名: {list(SortedFinaltable.columns)}")
        return []
    
    material_ids = SortedFinaltable[steel_identifier_col].unique()
    print(f"找到 {len(material_ids)} 个唯一钢卷标识")
    
    # 用于存储所有钢卷的坐标信息
    all_coordinates = []

    for material in material_ids:
        print(f"\n处理钢卷: {material}")
        
        # 筛选当前钢卷订单（保持原始顺序）
        order = SortedFinaltable[SortedFinaltable[steel_identifier_col] == material].copy()
        
        # 如果订单为空则跳过
        if order.empty:
            print(f"  钢卷 {material} 没有订单，跳过")
            continue
        
        # 获取钢卷信息 - 检测MaterialInformation的标识列名
        identifier_col_material = None
        for col_name in ['Identifier', 'MaterialLotId', 'steelIdentifier', 'LotNo']:
            if col_name in MaterialInformation.columns:
                identifier_col_material = col_name
                break
        
        if identifier_col_material:
            material_info = MaterialInformation[MaterialInformation[identifier_col_material] == material]
            steel_length = material_info['Length'].values[0] if len(material_info) > 0 else 0
            steel_width = material_info['Width'].values[0] if len(material_info) > 0 else 0
        else:
            print(f"  警告: MaterialInformation 中没有找到标识列，可用列: {list(MaterialInformation.columns)}")
            steel_length = 0
            steel_width = 0
        
        # 计算使用长度
        used_length = order['UsedLength'].sum() if 'UsedLength' in order.columns else 0
        
        xOffset = 0
        yOffset = 0
        max_y_in_current_x = 0  # 记录当前x位置下的最大y值
        
        # 用于存储当前钢卷的坐标记录
        coordinate_records = []
        
        # 直接按订单原始顺序处理
        for _, row in order.iterrows():
            m = int(row['UsedQuantity'])
            current_x = xOffset
            current_y = yOffset
            
            # 绘制当前订单的所有数量
            for n in range(m):
                # 检查是否超出钢卷宽度，需要换行
                if current_y + row['Width'] > steel_width:
                    current_y = 0
                    xOffset += row['Length']
                    current_x = xOffset
                
                # 记录坐标信息
                coordinate_records.append({
                    'docNo': row['docNo'],
                    'quantity': row['UsedQuantity'],
                    'itemSeq': n + 1,  # 从1开始递增
                    'x': current_x,
                    'y': current_y,
                    'length': row['Length'],
                    'width': row['Width'],
                    'steelIdentifier': material
                })
                
                current_y += row['Width']
                max_y_in_current_x = max(max_y_in_current_x, current_y)
            
            # 移动到下一个x位置
            xOffset += row['Length']
            yOffset = 0
            max_y_in_current_x = 0
        
        # 保存当前钢卷的所有信息
        steel_coordinate_data = {
            'steelIdentifier': material,
            'steelLength': steel_length,
            'steelWidth': steel_width,
            'usedLength': used_length,
            'coordinates': coordinate_records
        }
        
        all_coordinates.append(steel_coordinate_data)
        
        print(f"  钢卷长度: {steel_length}mm, 宽度: {steel_width}mm")
        print(f"  使用长度: {used_length}mm")
        print(f"  订单坐标数量: {len(coordinate_records)}")

    return all_coordinates