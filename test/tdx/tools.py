def raw_data_to_dataframe_complete(raw_data):
    """
    通用转换函数：将原始字典数据转换为标准的 DataFrame
    """
    if not raw_data:
        return pd.DataFrame()

    fields = list(raw_data.keys())
    # 取第一个字段获取股票列表和日期索引
    first_field = fields[0]
    first_df = raw_data[first_field]

    # 确保原始数据是DataFrame格式
    if isinstance(first_df, pd.DataFrame) and hasattr(first_df, 'columns'):
        stock_codes = first_df.columns.tolist()
        df_list = []

        # 遍历每一只股票
        for stock_code in stock_codes:
            stock_data = {}

            # 遍历每一个字段，提取该股票的数据
            for field in fields:
                field_data = raw_data[field]

                # 安全获取数据
                if isinstance(field_data, pd.DataFrame) and stock_code in field_data.columns:
                    stock_data[field] = field_data[stock_code].values
                else:
                    stock_data[field] = np.nan

            # 构建该股票的临时DataFrame
            stock_df = pd.DataFrame(stock_data)
            stock_df['股票代码'] = stock_code

            # 补充日期索引
            if hasattr(first_df, 'index'):
                stock_df['日期'] = first_df.index

            df_list.append(stock_df)

        # 合并所有股票数据
        if df_list:
            final_df = pd.concat(df_list, ignore_index=True)
            # 调整列顺序：代码、日期、指标...
            col_order = ['股票代码', '日期'] + fields
            return final_df[col_order]

    return pd.DataFrame()