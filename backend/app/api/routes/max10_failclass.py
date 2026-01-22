import pandas as pd
import numpy as np
from openpyxl import Workbook


def MAX10Failclass(inputFile, NUMCLASS):
    """
    Failclass - 分类函数（新增：保留Thickness列，按Thickness优先分类）
    输入:
        inputFile - 输入的 Excel 文件名（如 'r_orders.xlsx'）
        NUMCLASS  - 分组数参数，0 表示正常分组，每次加一后分组减半，直到组类为1
    输出:
        导出分类结果到 '分类数据.xlsx'，包含Thickness列，且按Thickness优先分类
    """
    # --------------------- 输入参数验证 ---------------------
    if not isinstance(inputFile, str):
        raise ValueError("输入文件名必须为字符串类型。")
    if not isinstance(NUMCLASS, int) or NUMCLASS < 0:
        raise ValueError("NUMCLASS 必须为非负整数。")

    # --------------------- 读取数据（新增：检查并读取Thickness列） ---------------------
    try:
        TT = pd.read_excel(inputFile, sheet_name='Sheet1')
    except Exception as e:
        print(f"无法读取文件: {inputFile}。错误信息: {str(e)}")
        return

    # 检查表格是否为空
    if TT.empty:
        print("Excel 文件为空，函数终止。")
        return

    # 移除第一列中包含 NaN 的行
    first_column_name = TT.columns[0]
    TT = TT.dropna(subset=[first_column_name])
    print(f"移除包含 NaN 的行后，表格剩余行数: {len(TT)}")
    if TT.empty:
        print("移除 NaN 后，Excel 文件为空，函数终止。")
        return

    # 新增：检查Thickness列是否存在
    if 'Thickness' not in TT.columns:
        print("警告：Excel表中缺少Thickness列，将跳过Thickness分类逻辑")
        TT['Thickness'] = np.nan  # 填充NaN，避免后续报错
    else:
        # 处理Thickness列的缺失值（视为独立类别）
        TT['Thickness'] = TT['Thickness'].fillna('NaN')

    # 提取ProcessOrder列（原有逻辑）
    if 'ProcessOrder' not in TT.columns:
        print("Excel 表中缺少 ProcessOrder 列，函数终止。")
        return
    C = TT['ProcessOrder'].astype(str)

    # --------------------- 核心修改：按Thickness优先分组 ---------------------
    # 获取所有唯一的Thickness值（作为一级分组键）
    unique_thickness = TT['Thickness'].unique()
    # 存储所有Thickness分组的结果（每个元素是该Thickness下的分组数据）
    all_thickness_groups = []

    for thickness in unique_thickness:
        # 1. 筛选当前Thickness的所有订单
        thickness_mask = TT['Thickness'] == thickness
        TT_thickness = TT[thickness_mask].copy()
        C_thickness = C[thickness_mask].copy()  # 当前Thickness对应的ProcessOrder
        if len(TT_thickness) == 0:
            continue

        # 2. 对当前Thickness组内应用原有的ProcessOrder分类逻辑
        split_C = C_thickness.str.split('|')

        # 收集所有唯一的子字符串
        all_tokens = [token for sublist in split_C for token in sublist]
        unique_tokens = sorted(set(all_tokens))
        num_tokens = len(unique_tokens)
        num_strings = len(C_thickness)

        # 创建子字符串存在矩阵
        presence_matrix = np.zeros((num_strings, num_tokens), dtype=bool)
        for i, tokens in enumerate(split_C):
            for token in tokens:
                if token in unique_tokens:
                    token_idx = unique_tokens.index(token)
                    presence_matrix[i, token_idx] = True

        # 识别一致的子字符串（全量包含/高占比包含）
        consistent_tokens_all = [unique_tokens[i] for i in range(num_tokens) if presence_matrix[:, i].all()]
        threshold = 0.8 * num_strings
        consistent_tokens_threshold = [unique_tokens[i] for i in range(num_tokens) if
                                       presence_matrix[:, i].sum() >= threshold]

        # 按优先级分组（Brushed > Mirror > AntiFingerprint）
        priority_tokens = ['Brushed', 'Mirror', 'AntiFingerprint']
        main_group_keys = []
        for tokens in split_C:
            prioritized = [token for token in tokens if token in priority_tokens]
            if prioritized:
                main_group_keys.append(prioritized[0])
            else:
                main_group_keys.append('Other')
        unique_main_groups = sorted(set(main_group_keys))

        # 主组内进一步细分
        secondary_group_keys = []
        for tokens, main_group in zip(split_C, main_group_keys):
            if main_group == 'Other':
                remaining_tokens = tokens
            else:
                remaining_tokens = [token for token in tokens if token != main_group]
            sorted_tokens = sorted(remaining_tokens)
            secondary_group_keys.append('-'.join(sorted_tokens))

        # 组合主组+次级组，生成最终组键
        final_group_keys = []
        for main_group, secondary_group in zip(main_group_keys, secondary_group_keys):
            if main_group == 'Other':
                final_group_keys.append(secondary_group)
            else:
                if secondary_group == '':
                    final_group_keys.append(main_group)
                else:
                    final_group_keys.append(f"{main_group}-{secondary_group}")
        unique_final_groups = sorted(set(final_group_keys))

        # 初始化分组结构（存储每组的ProcessOrder和对应行索引）
        grouped_strings = {group: [] for group in unique_final_groups}
        grouped_indices = {group: [] for group in unique_final_groups}
        # 注意：此处索引是相对于TT_thickness的，后续需映射回原TT的索引
        for i, group in enumerate(final_group_keys):
            grouped_strings[group].append(C_thickness.iloc[i])
            grouped_indices[group].append(i)  # i是TT_thickness内的行索引

        # 按组内子字符串数量排序
        unique_string_counts = {group: len(set('-'.join(grouped_strings[group]).split('-'))) for group in
                                unique_final_groups}
        sorted_groups = sorted(unique_final_groups, key=lambda g: unique_string_counts[g], reverse=True)
        grouped_strings = {group: grouped_strings[group] for group in sorted_groups}
        grouped_indices = {group: grouped_indices[group] for group in sorted_groups}
        group_ids = list(range(1, len(sorted_groups) + 1))
        group_counts = [len(grouped_strings[group]) for group in sorted_groups]

        # 限制组内数量不超过10
        max_group_size = 10
        new_grouped_strings = []
        new_grouped_indices = []  # 存储的是TT_thickness内的索引
        new_group_ids = []
        new_group_counts = []
        current_group_id = 1
        for group, count in zip(sorted_groups, group_counts):
            if count <= max_group_size:
                new_grouped_strings.append(grouped_strings[group])
                new_grouped_indices.append(grouped_indices[group])
                new_group_counts.append(count)
                new_group_ids.append(current_group_id)
                current_group_id += 1
            else:
                num_sub_groups = -(-count // max_group_size)
                for j in range(num_sub_groups):
                    start_idx = j * max_group_size
                    end_idx = min((j + 1) * max_group_size, count)
                    new_grouped_strings.append(grouped_strings[group][start_idx:end_idx])
                    new_grouped_indices.append(grouped_indices[group][start_idx:end_idx])
                    new_group_counts.append(len(new_grouped_strings[-1]))
                    new_group_ids.append(current_group_id)
                    current_group_id += 1

        # 转换索引：从TT_thickness内的索引→原TT的索引（用于后续提取数据）
        # TT_thickness的索引是原TT的子集，通过iloc转换
        original_indices = TT_thickness.index  # 原TT中当前Thickness组的索引
        new_grouped_indices_original = []
        for indices in new_grouped_indices:
            # 每个indices是TT_thickness内的行号，转换为原TT的索引
            original_idx = [original_indices[i] for i in indices]
            new_grouped_indices_original.append(original_idx)

        # 存储当前Thickness组的所有分组信息
        all_thickness_groups.append({
            'thickness': thickness,
            'grouped_strings': new_grouped_strings,
            'grouped_indices': new_grouped_indices_original,  # 原TT索引
            'group_ids': new_group_ids,
            'group_counts': new_group_counts
        })

    # --------------------- 生成初始分组结果（新增Thickness列） ---------------------
    classify = []
    process_order = []
    sequence = []  # itemSeq列
    width = []
    length = []
    quantity = []
    docDate = []
    deliveryDate = []
    materialCode = []

    thickness_list = []  # 新增：存储Thickness信息
    unclassify = []
    number = []

    # 遍历所有Thickness组，合并结果
    global_group_id = 1  # 全局组号（跨Thickness唯一）
    for thickness_group in all_thickness_groups:
        thickness = thickness_group['thickness']
        grouped_strings = thickness_group['grouped_strings']
        grouped_indices = thickness_group['grouped_indices']
        group_counts = thickness_group['group_counts']

        # 为当前Thickness组的每个分组分配全局唯一组号
        for i in range(len(grouped_strings)):
            num_entries = len(grouped_strings[i])
            # 使用全局组号（确保不同Thickness组的组号不重复）
            classify.extend([global_group_id] * num_entries)
            process_order.extend(grouped_strings[i])
            # 提取原TT中的数据（使用转换后的原索引）
            indices = grouped_indices[i]
            sequence.extend(TT.loc[indices, 'itemSeq'])
            thickness_list.extend([thickness] * num_entries)  # 新增：添加Thickness
            width.extend(TT.loc[indices, 'Width'] if 'Width' in TT.columns else [np.nan] * num_entries)
            length.extend(TT.loc[indices, 'Length'] if 'Length' in TT.columns else [np.nan] * num_entries)
            quantity.extend(TT.loc[indices, 'Quantity'] if 'Quantity' in TT.columns else [np.nan] * num_entries)
            docDate.extend(TT.loc[indices, 'docDate'] if 'docDate' in TT.columns else [np.nan] * num_entries)
            deliveryDate.extend(TT.loc[indices, 'deliveryDate'] if 'deliveryDate' in TT.columns else [np.nan] * num_entries)
            materialCode.extend(TT.loc[indices, 'materialCode'] if 'materialCode' in TT.columns else [np.nan] * num_entries)
 
            unclassify.append(global_group_id)
            number.append(group_counts[i])
            global_group_id += 1

    # 构建结果表（新增Thickness列）
    T = pd.DataFrame({
        'Classify': classify,
        'itemSeq': sequence,
        'ProcessOrder': process_order,
        'Thickness': thickness_list,  # 新增：Thickness列
        'Width': width,
        'Length': length,
        'Quantity': quantity,
        'docDate': docDate,
        'deliveryDate': deliveryDate,
        'materialCode': materialCode

    })

    TC = pd.DataFrame({
        'unClassify': unclassify,
        'Number': number
    })

    T = T.sort_values(by='Classify')

    # 导出初始结果
    excel_file_name = '分类数据.xlsx'
    sheet_name_result = '分类结果'
    sheet_name_count = '分类数'
    with pd.ExcelWriter(excel_file_name, engine='openpyxl') as writer:
        T.to_excel(writer, sheet_name=sheet_name_result, index=False)
        TC.to_excel(writer, sheet_name=sheet_name_count, index=False)
    print(f"初始分组结果已导出到 Excel 文件: {excel_file_name} 的工作表 {sheet_name_result} 和 {sheet_name_count}")

    # --------------------- 循环分组部分（同步更新Thickness列） ---------------------
    if NUMCLASS > 0:
        # 准备循环分组所需的初始数据（基于全局分组）
        # 这里需要重新整理全局分组的索引和信息，逻辑与初始分组一致但需支持迭代合并
        # 为简化，复用all_thickness_groups并重新生成全局分组列表
        global_groups = []
        for thickness_group in all_thickness_groups:
            for i in range(len(thickness_group['grouped_strings'])):
                global_groups.append({
                    'thickness': thickness_group['thickness'],
                    'indices': thickness_group['grouped_indices'][i],
                    'strings': thickness_group['grouped_strings'][i]
                })

        iteration = 0
        current_global_groups = global_groups.copy()

        # 循环逻辑：每次分组减半
        while len(current_global_groups) > 1 and iteration < NUMCLASS:
            iteration += 1
            print(f"\n开始循环迭代 i = {iteration}")
            new_group_count = -(-len(current_global_groups) // 2)
            print(f"当前组数: {len(current_global_groups)}，目标组数: {new_group_count}")

            new_global_groups = []
            for j in range(new_group_count):
                # 合并当前组和下一组（若存在）
                merge_indices = [j * 2, j * 2 + 1]
                merge_indices = [idx for idx in merge_indices if idx < len(current_global_groups)]
                merged_indices = []
                merged_strings = []
                merged_thickness = set()  # 记录合并组中的所有Thickness（可能有多个）
                for idx in merge_indices:
                    merged_indices.extend(current_global_groups[idx]['indices'])
                    merged_strings.extend(current_global_groups[idx]['strings'])
                    merged_thickness.add(current_global_groups[idx]['thickness'])
                # 存储合并后的组信息
                new_global_groups.append({
                    'thickness': merged_thickness,  # 可能包含多个Thickness
                    'indices': merged_indices,
                    'strings': merged_strings
                })

            current_global_groups = new_global_groups
            print(f"循环迭代 {iteration} 完成。当前总组数: {len(current_global_groups)}")

        # 生成循环分组结果（包含Thickness列）
        classify_iter = []
        process_order_iter = []
        sequence_iter = []
        thickness_iter = []
        width_iter = []
        length_iter = []
        quantity_iter = []
        docDate_iter = []
        deliveryDate_iter = []
        materialCode_iter = []

        unclassify_iter = []
        number_iter = []

        current_group_id = 1
        for group in current_global_groups:
            num_entries = len(group['indices'])
            classify_iter.extend([current_group_id] * num_entries)
            process_order_iter.extend(group['strings'])
            indices = group['indices']
            sequence_iter.extend(TT.loc[indices, 'itemSeq'])
            # 提取每个订单对应的Thickness（原TT中的值）
            thickness_iter.extend(TT.loc[indices, 'Thickness'])
            width_iter.extend(TT.loc[indices, 'Width'] if 'Width' in TT.columns else [np.nan] * num_entries)
            length_iter.extend(TT.loc[indices, 'Length'] if 'Length' in TT.columns else [np.nan] * num_entries)
            quantity_iter.extend(TT.loc[indices, 'Quantity'] if 'Quantity' in TT.columns else [np.nan] * num_entries)
            docDate_iter.extend(TT.loc[indices, 'docDate'] if 'docDate' in TT.columns else [np.nan] * num_entries)
            deliveryDate_iter.extend(TT.loc[indices, 'deliveryDate'] if 'deliveryDate' in TT.columns else [np.nan] * num_entries)
            materialCode_iter.extend(TT.loc[indices, 'materialCode'] if 'materialCode' in TT.columns else [np.nan] * num_entries)
 
            unclassify_iter.append(current_group_id)
            number_iter.append(num_entries)
            current_group_id += 1

        # 构建循环结果表（包含Thickness列）
        T_iter = pd.DataFrame({
            'Classify': classify_iter,
            'itemSeq': sequence_iter,
            'ProcessOrder': process_order_iter,
            'Thickness': thickness_iter,  # 新增：Thickness列
            'Width': width_iter,
            'Length': length_iter,
            'Quantity': quantity_iter,
            'docDate': docDate_iter,
            'deliveryDate': deliveryDate_iter,
            'materialCode': materialCode_iter
        })

        T_iter = T_iter.sort_values(by='Classify')
        sheet_name_result_iter = '循环分类结果'

        # 追加写入循环结果
        with pd.ExcelWriter(excel_file_name, engine='openpyxl', mode='a') as writer:
            T_iter.to_excel(writer, sheet_name=sheet_name_result_iter, index=False)
        print(f"循环分组结果已导出到 Excel 文件: {excel_file_name} 的工作表 {sheet_name_result_iter}")


# --------------------- 测试调用 ---------------------
if __name__ == "__main__":
    inputFile = 'r_orders.xlsx'  # 确保该文件包含Thickness列
    NUMCLASS = 0  # 0=正常分组，可根据需求调整
    MAX10Failclass(inputFile, NUMCLASS)