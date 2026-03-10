import streamlit as st
import pandas as pd
import io

def p_stars(p):
    """根据 p 值返回学术星号标注: * p<0.05, ** p<0.01, *** p<0.001"""
    if p < 0.001:
        return '***'
    elif p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    else:
        return ''

def app_data_upload_module():
    st.title("模块一: 数据上传与概览 (Data Upload & Overview)")
    
    st.info("💡 **这是什么？** 在这里，你需要上传你在实验中收集到的原始数据（通常是每行代表一个被试，每列代表一个变量）。上传后，系统会自动清洗并尝试推断你的变量类型。")

    uploaded_file = st.file_uploader("📥 上传你的数据文件 (支持 CSV 或 Excel)", type=['csv', 'xlsx', 'xls'])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Store in session state so other modules can use it
            st.session_state['data'] = df
            st.success(f"✅ 成功加载数据！共 {df.shape[0]} 行, {df.shape[1]} 列。")
            
        except Exception as e:
            st.error(f"❌ 读取数据失败: {e}")
            return
    
    if 'data' in st.session_state:
        df = st.session_state['data']
        
        st.subheader("1. 数据预览")
        st.dataframe(df.head(10))

        st.subheader("2. 变量推断")
        col1, col2 = st.columns(2)
        
        continuous_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

        # heuristic: if a numeric column has very few unique values (<10), it might be categorical (e.g., Likert scale or binary indicator)
        likely_categorical = []
        for col in continuous_cols:
            if df[col].nunique() < 10:
                likely_categorical.append(col)
                
        with col1:
            st.write("📊 **连续变量 (数值型)**")
            st.write([c for c in continuous_cols if c not in likely_categorical])
            if likely_categorical:
                st.warning(f"⚠️ 以下数值型变量独立取值较少，可能实际上是分类变量（如量表打分、组别）：\n\n {', '.join(likely_categorical)}")
                
        with col2:
            st.write("🔠 **分类变量 (非数值型)**")
            st.write(categorical_cols)
            
        st.markdown("---")
        st.subheader("3. 🛡️ 数据清洗过滤 (可选)")
        st.info("💡 **学术提示**：你的数据可能包含乱填乱答的“废卷”，在此处根据**答题时长**或**陷阱题**进行排除，以保证数据质量。系统会自动用清洗后的数据进行后续所有分析！")
        
        # Make a copy of the original dataframe
        if 'original_data' not in st.session_state:
            st.session_state['original_data'] = df.copy()
            
        current_df = st.session_state['original_data'].copy()
        initial_rows = current_df.shape[0]
        
        col_clean1, col_clean2 = st.columns(2)
        with col_clean1:
            enable_time_filter = st.checkbox("按数值门槛过滤 (如: 答题时长 < 60s)")
            if enable_time_filter:
                time_col = st.selectbox("选择过滤变量 (连续型):", continuous_cols, key='time_col')
                threshold = st.number_input(f"设定阈值 (将剔除 `{time_col}` < 该值的样本):", value=0.0)
                if st.button("应用数值过滤"):
                    current_df = current_df[current_df[time_col] >= threshold]
                    
        with col_clean2:
            enable_trap_filter = st.checkbox("按指定答案过滤 (如: 陷阱题不等于 X)")
            if enable_trap_filter:
                trap_col = st.selectbox("选择过滤变量 (支持分类/数值):", df.columns.tolist(), key='trap_col')
                expected_val = st.text_input(f"设定预期标准答案 (将剔除 `{trap_col}` 不等于该值的样本):", value="")
                
                if st.button("应用陷阱题过滤"):
                    # Type casting for comparison
                    if pd.api.types.is_numeric_dtype(current_df[trap_col]):
                        try:
                            val = float(expected_val)
                            current_df = current_df[current_df[trap_col] == val]
                        except:
                            st.error("输入值与该列类型(数值)不匹配。")
                    else:
                        current_df = current_df[current_df[trap_col].astype(str) == expected_val]
                        
        if st.button("🧹 确认使用当前清洗规则保存数据"):
            st.session_state['data'] = current_df
            final_rows = current_df.shape[0]
            dropped = initial_rows - final_rows
            st.success(f"✅ 清洗完成！\n\n**原始样本量**: {initial_rows} 人 ➡️ **清洗后**: {final_rows} 人。共剔除了 **{dropped}** 份无效问卷。")

def descriptive_statistics_module():
    st.title("模块二: 描述性统计 (Descriptive Statistics)")
    
    st.info("💡 **这是什么？为什么做这个？** \n\n描述性统计用于展示你样本的基准情况（如男女比例、平均年龄）。这通常是你论文中的第一个表格，用于向读者证明你的样本具有代表性。")
    
    if 'data' not in st.session_state:
        st.warning("⚠️ 请先在【数据上传】页面加载数据！")
        return
        
    df = st.session_state['data']
    
    st.subheader("1. 连续变量汇总 (集中趋势与离散程度)")
    numeric_df = df.select_dtypes(include=['float64', 'int64'])
    
    if not numeric_df.empty:
        desc_df = numeric_df.describe().T
        # Add median which is not always clearly visible in describe depending on config
        desc_df['median'] = numeric_df.median()
        desc_df = desc_df[['count', 'mean', 'std', 'min', 'median', '25%', '75%', 'max']]
        st.dataframe(desc_df)
        
        st.write("🩺 **数据健康度体检 (Data Health Diagnostics)**")
        try:
            norm_res = pg.normality(numeric_df)
            skew_res = numeric_df.skew()
            
            health_df = pd.DataFrame({
                '偏度 (Skewness)': skew_res.round(3),
                '正态性 p 值 (Shapiro-Wilk)': norm_res['pval'].round(4),
                '是否大致正态 (Normal)': norm_res['normal']
            })
            st.dataframe(health_df)
            
            skewed_vars = health_df[health_df['偏度 (Skewness)'].abs() > 1].index.tolist()
            if skewed_vars:
                st.warning(f"⚠️ **【小白体检报告】注意！** 以下变量的分布存在严重偏斜（偏度绝对值 > 1）：`{', '.join(skewed_vars)}`。\n\n这意味着大家的分数不是均匀的钟形分布，而是严重挤在某一端（比如大多数人都是低分）。如果后续用它们做 T检验 或 方差分析，传统的 p 值可能不太准。如果审稿人要求严格，你可能要在论文里报告它们采用了“非参数检验”(Non-parametric tests) 或者进行了数据转换。")
            else:
                st.success("✅ **【小白体检报告】完美！** 所有连续变量的偏度都在可接受范围内，数据形态比较健康，后续可以放心大胆地使用主流的 T检验、ANOVA 和 回归分析！")
        except Exception as e:
            st.write("数据量太大或其他原因导致无法完成正态性体检。")
    else:
        st.write("当前数据没有可计算的连续型(数值型)变量。")

    st.subheader("2. 分类变量分布 (频率分析)")
    categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    
    # allow users to force some numeric columns as categorical for counting
    all_cols = df.columns.tolist()
    cat_sel = st.multiselect("选择你要查看分布的变量 (默认已选中非数值变量):", all_cols, default=categorical_cols)
    
    if cat_sel:
        for col in cat_sel:
            st.write(f"**{col}** 频次分布:")
            counts = df[col].value_counts()
            percs = df[col].value_counts(normalize=True).mul(100).round(2).astype(str) + '%'
            dist_df = pd.DataFrame({'频次 (Count)': counts, '占比 (Percentage)': percs})
            st.dataframe(dist_df)
            
            # Simple bar chart plotting
            st.bar_chart(counts)
            st.markdown("---")

import pingouin as pg
import matplotlib.pyplot as plt
import seaborn as sns
from factor_analyzer import FactorAnalyzer, calculate_kmo, calculate_bartlett_sphericity
from sklearn.decomposition import PCA
import semopy
import numpy as np

def reliability_validity_module():
    st.title("模块三: 信效度分析 (Reliability & Validity)")
    
    with st.expander("💡 什么是信效度？为什么要做？我该怎么填？", expanded=True):
        st.markdown('''
        - **什么是信度 (Reliability)？** 衡量你的问卷题目是否**稳定、一致**。比如你用3个题目测“购买意愿”，如果大家在这3题上的打分总是同高同低，说明大家没有乱填，信度好（Cronbach's $\\alpha$ 通常要求 > 0.7）。
        - **什么是效度 (Validity)？** 衡量你的题目是否**真的测到了你想测的东西**。通过 KMO 检验（要求 > 0.6）和 Bartlett 球形度检验（要求 p < 0.05）来判断这些零散的题目是否适合合并算平均分。
        - **我该怎么填？** 选出你要测量的**同一个概念**下的所有题目（建议至少挑2题以上，如 Q1, Q2, Q3）。
        ''')

    if 'data' not in st.session_state:
        st.warning("⚠️ 请先在【数据上传】页面加载数据！")
        return
        
    df = st.session_state['data']
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    st.write("### 选择量表题项")
    selected_items = st.multiselect("请选择属于同一个潜变量（如同一个维度的量表）的所有题项变量:", numeric_cols)
    
    if st.button("运行信效度分析"):
        if len(selected_items) < 2:
            st.error("❌ 信效度分析至少需要选择 2 个以上的题项！")
            return
            
        clean_df = df[selected_items].dropna()
        if len(clean_df) < 10:
            st.error("❌ 样本量太少，无法进行分析。")
            return
            
        st.markdown("---")
        
        # 1. Reliability (Cronbach's Alpha)
        st.subheader("1. 信度分析 (Cronbach's Alpha)")
        cronbach_res = pg.cronbach_alpha(data=clean_df)
        alpha, ci = cronbach_res
        
        st.write(f"**Cronbach's $\\alpha$ 系数**: `{alpha:.3f}`")
        if alpha >= 0.7:
            st.success(f"🎉 **【信度体检报告】极佳！** $\\alpha$ 系数超过了 0.7 的及格线（{alpha:.3f}），说明这些题目大家回答得非常一致。你的测量工具很靠谱，可以将它们计算平均分合并成一个变量使用。")
        elif alpha >= 0.6:
            st.warning(f"⚠️ **【信度体检报告】勉强及格。** $\\alpha$ 系数为 {alpha:.3f}，在可接受的边缘。如果这是新开发的量表可以接受，但如果是成熟量表则偏低。")
        else:
            st.error(f"📉 **【信度体检报告】信度堪忧！** $\\alpha$ 系数仅为 {alpha:.3f}，远低于 0.7。这意味着这些题目互相打架，大家并没有把它们当成同一个东西在回答。⚠️ 强烈建议找出并剔除那个“捣乱”的题目，或者重新审视问卷设计！")
            
        st.markdown("---")
        
        # 2. Validity (KMO & Bartlett)
        st.subheader("2. 效度预检验 (KMO & Bartlett)")
        try:
            kmo_all, kmo_model = calculate_kmo(clean_df)
            chi_square_value, p_value = calculate_bartlett_sphericity(clean_df)
            
            st.write(f"**KMO (Kaiser-Meyer-Olkin) 测度**: `{kmo_model:.3f}`")
            st.write(f"**Bartlett's 球形度检验 p 值**: `{p_value:.3e}`")
            
            if kmo_model >= 0.6 and p_value < 0.05:
                st.success(f"🎉 **【效度体检报告】合格！** KMO 值（{kmo_model:.3f}）及格且 Bartlett 检验显著，说明这些题目之间存在足够强的相关性。它们非常适合做因子分析，也证明了它们确实在测量某些共同的底层逻辑。")
            else:
                if kmo_model < 0.6:
                    st.error(f"📉 **【效度体检报告】效度堪忧！** KMO 值（{kmo_model:.3f}）低于 0.6 的及格线。说明这些题项各说各话，相关性很弱，不适合把它们强行合并成一个因素！")
                if p_value >= 0.05:
                    st.error("📉 Bartlett's 球形度检验不显著，这些变量可能根本彼此独立，没有潜在的共性因子。")
            # EFA with cumulative variance
            if kmo_model >= 0.6 and p_value < 0.05:
                st.write("#### 探索性因子分析 (EFA) 因子提取")
                try:
                    n_factors = max(1, min(len(selected_items) // 2, 5))
                    fa = FactorAnalyzer(n_factors=n_factors, rotation='varimax')
                    fa.fit(clean_df)
                    ev, v = fa.get_eigenvalues()
                    variance = fa.get_factor_variance()
                    # variance returns (SS Loadings, Proportion Var, Cumulative Var)
                    cum_var = variance[2][-1] * 100  # last cumulative value
                    st.write(f"**提取 {n_factors} 个因子的累计方差解释率**: `{cum_var:.2f}%`")
                    if cum_var >= 60:
                        st.success(f'✅ 累计方差解释率达到 {cum_var:.2f}%（超过60%及格线），说明提取的因子充分地代表了原始题目中的信息。')
                    else:
                        st.warning(f'⚠️ 累计方差解释率仅为 {cum_var:.2f}%（低于60%），说明因子尚未充分捕捉题目间的共同信息，可考虑调整因子数量或审查题项。')
                    
                    loadings_matrix = pd.DataFrame(
                        fa.loadings_,
                        index=selected_items,
                        columns=[f'Factor {i+1}' for i in range(n_factors)]
                    )
                    with st.expander('查看因子载荷矩阵 (Factor Loading Matrix)'):
                        st.dataframe(loadings_matrix.round(3))
                except Exception as efa_e:
                    st.write(f'EFA 因子提取异常: {efa_e}')
        except Exception as e:
            st.write(f"效度计算失败，可能是数据完全不相关或方差为 0。详细错误: {e}")
            
        st.markdown("---")
        
        # 3. CMV (Harman's Single Factor Test)
        st.subheader("3. 🛡️ 共同方法偏差检验 (CMV) - Harman单因子检验")
        st.info("💡 **学术提示**：自填式问卷容易产生共同方法偏差。此处通过提取第一个主成分的方差解释率来诊断。")
        try:
            pca = PCA(n_components=1)
            pca.fit(clean_df)
            variance_ratio = pca.explained_variance_ratio_[0] * 100
            st.write(f"**提取的第一主成分方差解释率**: `{variance_ratio:.2f}%`")
            if variance_ratio > 50:
                st.error(f"📉 **【异常预警】CMV严重！** 第一主成分强行解释了超过 50% ({variance_ratio:.2f}%) 的变异。说明你的数据受到单一方法来源的严重扭曲（受试者可能在乱填或所有题目都朝同一个固定方向作答）。数据质量值得怀疑！")
            else:
                st.success(f"✅ **【合格】未发现严重 CMV。** 第一主成分解释率仅为 {variance_ratio:.2f}% (低于50%警戒线)，说明数据的变异是多维的，不存在严重的共同方法偏差。")
        except Exception as e:
            st.write(f"CMV检验异常: {e}")
            
        st.markdown("---")
        
        # 4. CFA, AVE & CR
        st.subheader("4. 🌟 验证性因子分析 (CFA) 与 结构效度体检")
        st.info("💡 **学术提示**：假设选定的题目共同测量**同一个潜在概念 (单维潜变量)**。系统将在此调用 `semopy` 计算绝对/相对适配度，以及收敛效度 (AVE & CR)。")
        try:
            items = clean_df.columns.tolist()
            latent_name = "Factor"
            formula = f"{latent_name} =~ {' + '.join(items)}"
            
            model = semopy.Model(formula)
            model.fit(clean_df)
            
            stats = semopy.calc_stats(model)
            if not stats.empty:
                def _get(name):
                    return stats[name].values[0] if name in stats else np.nan
                
                cfi = _get('CFI')
                tli = _get('TLI')
                rmsea = _get('RMSEA')
                gfi = _get('GFI')
                agfi = _get('AGFI')
                nfi = _get('NFI')
                dof = _get('DoF') if 'DoF' in stats else 0
                chi2_val = _get('chi2')
                chi2_df = chi2_val / dof if dof > 0 else np.nan
                
                # Model Fit Table — full academic suite
                st.write("#### 模型适配度指标全家桶 (Model Fit Indices)")
                fit_df = pd.DataFrame({
                    '指标': ['X²/df', 'CFI', 'TLI', 'RMSEA', 'GFI', 'AGFI', 'NFI'],
                    '当前值': [chi2_df, cfi, tli, rmsea, gfi, agfi, nfi],
                    '标准推荐值': ['< 3.0 (放宽至5)', '> 0.90', '> 0.90', '< 0.08', '> 0.90', '> 0.80', '> 0.90']
                })
                fit_df['当前值'] = fit_df['当前值'].apply(lambda x: f"{x:.3f}" if pd.notnull(x) else "N/A")
                st.dataframe(fit_df, use_container_width=True)
                
                if (pd.notnull(cfi) and cfi >= 0.9) and (pd.notnull(rmsea) and rmsea <= 0.08):
                     st.success("✅ **适配度极佳**：CFI/TLI 达标且 RMSEA 处于安全范围，模型拟合良好。可直接将上表数据复制到论文的模型适配度报告中。")
                else:
                     st.warning("⚠️ **适配度欠佳或无法计算**：可能说明有些题目并不完全归属于同一个因素。在题项极少（如3题以内）时，DoF为0可能无法算出某些指标，属于正常现象。")
                
            # Convergence Validity (AVE and CR)
            st.write("#### 收敛效度体系 (Convergent Validity: AVE & CR)")
            inspec_std = model.inspect(std_est=True)
            if 'Est. Std' in inspec_std.columns:
                # filter for factor loadings
                loadings_df = inspec_std[(inspec_std['op'] == '~') & (inspec_std['rval'] == latent_name)]
                load_std = loadings_df['Est. Std'].values
                
                if len(load_std) > 0:
                    load_std_sq = load_std ** 2
                    error_vars = 1 - load_std_sq
                    # if standard estimates exceed 1 due to Heywood case, cap them or handle gracefully
                    load_std_sq = np.clip(load_std_sq, 0, 1)
                    error_vars = np.clip(error_vars, 0, 1)
                    
                    ave = np.sum(load_std_sq) / len(load_std)
                    cr = (np.sum(load_std)) ** 2 / ((np.sum(load_std)) ** 2 + np.sum(error_vars))
                    
                    st.write(f"**平均方差提取量 (AVE)**: `{ave:.3f}`")
                    st.write(f"**组合信度 (CR)**: `{cr:.3f}`")
                    
                    if ave >= 0.5 and cr >= 0.7:
                        st.success(f"🎉 **【极具学术感的通关文案】**:\n\n当前量表的 AVE = {ave:.3f} (>0.5)，且 CR = {cr:.3f} (>0.7)。这不仅说明你的题项内部一致性极高，而且确确实实测到了你想测的核心概念！你的结果完美契合顶级理论模型期刊对收敛效度 (Convergent Validity) 的审查标准，可以直接放入正文表格，极其无懈可击！")
                    else:
                        st.warning("⚠️ AVE 或 CR 未达到严格的标杆标准 (AVE>0.5, CR>0.7)。在一些探索性研究中也可被接受，但如果不被发回修改，建议查阅标准化因子载荷表格，剔除载荷特别低 (<0.6) 的个别题项后重新运行。")
                    
                    with st.expander("查看所有题目的标准化因子载荷 (Standardized Loadings)"):
                        st.dataframe(loadings_df[['lval', 'Est. Std', 'p-value']])
                else:
                    st.error("未能成功提取标准化载荷。")
            else:
                st.error("模型未能产出标准化参数。")
                
        except Exception as e:
            st.write(f"CFA计算异常，可能是变量数量太少、模型不收敛或存在完全共线: {e}")

def manipulation_checks_module():
    st.title("模块四: 操作检验 (Manipulation Checks)")
    
    with st.expander("💡 什么是操作检验？为什么要做？我该怎么填？", expanded=True):
        st.markdown('''
        - **什么是操作检验？** 操作检验是用来确认你的实验刺激（或干预）是否按照你的预期在参与者身上起作用了。
        - **为什么要做？** 比如你研究“悲伤情绪对购物的影响”，你让实验组看悲伤电影，控制组看纪录片。你需要证明*实验组看完后确实比控制组更悲伤*。如果他们没有更悲伤，你的整个实验干预就失败了。
        - **我该怎么填？** 
            - **自变量 (分组变量)**: 选择代表你实验分组的列（例如 `Ad_Type_IV`）。
            - **检验变量 (因变量)**: 选择你用来衡量该刺激是否起效的打分列（例如 `Visual_Appeal_ManCheck`）。
        ''')

    if 'data' not in st.session_state:
        st.warning("⚠️ 请先在【数据上传】页面加载数据！")
        return
        
    df = st.session_state['data']
    
    col1, col2 = st.columns(2)
    with col1:
        group_var = st.selectbox("1. 选择自变量 (分组变量，如：实验组别)", df.columns)
    with col2:
        test_var = st.selectbox("2. 选择检验变量 (连续型，如：受试者的主观打分)", df.columns)
        
    if st.button("运行操作检验"):
        # Drop NAs
        clean_df = df[[group_var, test_var]].dropna()
        n_groups = clean_df[group_var].nunique()
        
        if n_groups < 2:
            st.error("分组变量至少需要包含 2 个不同的组！")
            return
            
        st.markdown("---")
        st.subheader("分析结果")
        
        # Plotting
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x=group_var, y=test_var, data=clean_df, capsize=.1, errorbar='se', ax=ax)
        ax.set_title(f"{test_var} 的组间均值对比 (带标准误误差棒)")
        plt.tight_layout()
        st.pyplot(fig)
        
        # Testing
        if n_groups == 2:
            st.write("检测到 2 个分组，执行 **独立样本 t 检验 (Independent T-test)**:")
            groups = clean_df[group_var].unique()
            g1 = clean_df[clean_df[group_var] == groups[0]][test_var]
            g2 = clean_df[clean_df[group_var] == groups[1]][test_var]
            
            res = pg.ttest(g1, g2)
            st.dataframe(res)
            
            p_val = res['p-val'].values[0]
            if p_val < 0.05:
                st.success(f"🎉 **结论 (Plain Language Interpretation)**: \n\n检验结果达到统计学显著 (p < 0.05)。两组之间在 `{test_var}` 上存在真实差异，说明你的实验操纵**成功/有效**！")
            else:
                st.error(f"📉 **结论 (Plain Language Interpretation)**: \n\n检验结果未达到显著水平 (p >= 0.05)。两组之间的差异可能只是随机误差，代表你的实验操纵**可能失败了**，建议检查干预材料。")
                # Diagnostic
                cohen_d = res['cohen-d'].values[0]
                if abs(cohen_d) < 0.2:
                    st.info(f"🩺 **【小白深度诊断】为什么不显著？**\n\n当前效应量 (Cohen's d = {cohen_d:.2f}) 非常小。这意味着实验组和控制组的真实感知差异**微乎其微**。建议重新设计更强烈的实验刺激材料（比如换个更具冲击力的视频），目前的材料确实没有力量改变被试的感受。")
                else:
                    st.info(f"🩺 **【小白深度诊断】为什么不显著？**\n\n当前效应量 (Cohen's d = {cohen_d:.2f}) 其实不算太小！这说明实验刺激**可能是有用的**，但之所以 p 值没显著，大概率是因为**样本量太少** (Statistical Power 不足) 或者被试的**内部个体差异太大** (组内噪音太大)。建议增加被试人数后再试一次！")
                
        else:
            st.write(f"检测到 {n_groups} 个分组，执行 **单因素方差分析 (One-way ANOVA)**:")
            res = pg.anova(data=clean_df, dv=test_var, between=group_var)
            st.dataframe(res)
            
            p_val = res['p-unc'].values[0]
            if p_val < 0.05:
                st.success(f"🎉 **结论 (Plain Language Interpretation)**: \n\n主效应达到统计学显著 (p < 0.05)。各组之间在 `{test_var}` 上存在真实差异，说明你的实验操纵在至少两个组之间是**成功/有效**的。")
                
                # Post-hoc
                if st.checkbox("查看事后两两比较 (Post-hoc Tests)"):
                    posthoc = pg.pairwise_tests(data=clean_df, dv=test_var, between=group_var, padjust='bonf')
                    st.write("Bonferroni 校正后的两两组间比较:")
                    st.dataframe(posthoc)
            else:
                st.error(f"📉 **结论 (Plain Language Interpretation)**: \n\n主效应未达到显著水平 (p >= 0.05)。各组在 `{test_var}` 上没有显著差异，操纵**可能失败**。")
                # Diagnostic
                eta_sq = res['np2'].values[0]
                if eta_sq < 0.01:
                    st.info(f"🩺 **【小白深度诊断】为什么不显著？**\n\n当前效应量 (η² = {eta_sq:.3f}) 极小。说明这几种干预方式对改变被试感受**毫无作用**。建议更换更强有力的实验材料。")
                else:
                    st.info(f"🩺 **【小白深度诊断】为什么不显著？**\n\n当前效应量 (η² = {eta_sq:.3f}) 其实还可以！这意味着不同干预方式之间**可能有真实差异**，只是目前的**样本量太少**，或者被试打分太过参差不齐掩盖了这一效应。建议招募更多被试扩充样本量！")

def inferential_statistics_module():
    st.title("模块五: 推断性统计 (Inferential Statistics)")
    
    with st.expander("💡 什么是推断统计？为什么要做？我该怎么填？", expanded=True):
        st.markdown('''
        - **什么是推断统计？** 这是你研究的**核心结果**。通过差异检验（T检验/ANOVA）或者回归分析，来证明你的自变量（IV）确实对你的因变量（DV）产生了影响。
        - **为什么要做？** 证明因果关系或相关关系。如果 p < 0.05，说明你的研究假设很可能成立。
        - **什么是协变量？** 协变量是那些*可能影响结果，但你并不关心的变量*（如参与者原本的心情）。把它放进模型里，可以“剔除”它的干扰，让你的主效应更纯净（ANCOVA）。
        ''')

    if 'data' not in st.session_state:
        st.warning("⚠️ 请先在【数据上传】页面加载数据！")
        return
        
    df = st.session_state['data']
    cols = df.columns.tolist()
    
    st.write("### 差异检验 (T-test / ANOVA / ANCOVA)")
    col1, col2, col3 = st.columns(3)
    with col1:
        iv = st.selectbox("1. 选择自变量 (IV/分组):", cols, key='inf_iv')
    with col2:
        dv = st.selectbox("2. 选择因变量 (DV/结果):", cols, key='inf_dv')
    with col3:
        covars = st.multiselect("3. 选择协变量 (Covariates, 可选):", cols, key='inf_cov')
        
    if st.button("运行差异检验"):
        clean_cols = [iv, dv] + covars
        clean_df = df[clean_cols].dropna()
        n_groups = clean_df[iv].nunique()
        
        st.markdown("---")
        st.subheader("分析结果")
        
        if n_groups < 2:
            st.error("自变量包含的组数不够，无法比较。")
        else:
            if not covars:
                # No covariates -> T-test or ANOVA
                if n_groups == 2:
                    st.write(f"执行 **独立样本 t 检验**: `{iv}` 对 `{dv}` 的影响")
                    groups = clean_df[iv].unique()
                    res = pg.ttest(clean_df[clean_df[iv] == groups[0]][dv], 
                                   clean_df[clean_df[iv] == groups[1]][dv])
                    st.dataframe(res)
                    
                    p_val = res['p-val'].values[0]
                    if p_val < 0.05:
                        st.success(f"🎉 **结论 (Plain Language Interpretation)**: \n\n检验显著(p < 0.05)。说明 `{iv}` 对 `{dv}` 确实有显著影响，你的假设成立。")
                    else:
                        st.error(f"📉 **结论 (Plain Language Interpretation)**: \n\n未达到显著水平(p >= 0.05)。说明 `{iv}` 对 `{dv}` 没有显著影响。")
                        # Diagnostic
                        cohen_d = res['cohen-d'].values[0]
                        if abs(cohen_d) < 0.2:
                            st.info(f"🩺 **【小白深度诊断】为什么不显著？**\n\n当前主效应的效应量 (Cohen's d = {cohen_d:.2f}) 非常小。这几乎可以断定这两个自变量条件对因变量**真的没有影响**。不用怀疑你的数据，这个假设本身就是不成立的。")
                        else:
                            st.info(f"🩺 **【小白深度诊断】为什么不显著？**\n\n当前效应量 (Cohen's d = {cohen_d:.2f}) 其实是存在的！之所以没得到 p < 0.05 的“绿灯”，很可能是因为你的**样本量不够大**，不足以把这个细微的效应抓取出来。如果你能再收集几十个被试的数据，结果很可能就会变显著！")
                        
                else:
                    st.write(f"执行 **单因素方差分析 (One-way ANOVA)**:")
                    
                    # ⚙️ Automatic correction (Variance Homogeneity)
                    levene_res = pg.homoscedasticity(data=clean_df, dv=dv, group=iv)
                    is_equal_var = levene_res['pval'].values[0] >= 0.05
                    
                    if not is_equal_var:
                        st.warning(f"⚠️ **【系统自动纠偏】方差不齐！** 各组之间的个体差异(方差)极其肉眼可见的不公平（大组方差是大，小组方差小）。因此传统的 ANOVA 容易犯错。系统已自动为你切换为更稳健的 **Welch ANOVA** 方法进行分析！")
                        res = pg.welch_anova(data=clean_df, dv=dv, between=iv)
                        st.dataframe(res)
                        p_val = res['p-unc'].values[0]
                        eta_sq = res['np2'].values[0] # Welch in pingouin returns np2
                    else:
                        st.success("✅ 万幸！系统检测到各组的方差十分整齐（满足方差齐性），我们可以放心采用标准的 ANOVA！")
                        res = pg.anova(data=clean_df, dv=dv, between=iv)
                        st.dataframe(res)
                        p_val = res['p-unc'].values[0]
                        eta_sq = res['np2'].values[0]
                    
                    if p_val < 0.05:
                        st.success(f"🎉 **结论 (Plain Language Interpretation)**: \n\n主效应显著(p < 0.05)！说明不同的 `{iv}` 组别在 `{dv}` 上表现出显著差异。")
                    else:
                        st.error(f"📉 **结论 (Plain Language Interpretation)**: \n\n主效应不显著。组别间的差异可能是随机误差导致。")
                        if eta_sq < 0.01:
                            st.info(f"🩺 **【小白深度诊断】为什么不显著？**\n\n当前效应量 (η² = {eta_sq:.3f}) 极小。说明这几种自变量分组对因变量**几乎起不到实质性的影响**。")
                        else:
                            st.info(f"🩺 **【小白深度诊断】为什么不显著？**\n\n当前效应量 (η² = {eta_sq:.3f}) 其实是可以接受的水平！未能显著的罪魁祸首大概率是**样本量太小** (Statistical Power 不足) 或者是被试内部分数太散导致**噪声太大**。扩大样本量有望翻盘！")
            else:
                # ANCOVA
                st.write(f"执行 **协方差分析 (ANCOVA)**: 控制了协变量 `{', '.join(covars)}`")
                # pingouin's ancova currently supports 1 covariate well, if multi, we may use statsmodels. 
                # For simplicity in pingouin, we take the first covariate if multiple are selected, or use statsmodels for multi.
                if len(covars) == 1:
                    res = pg.ancova(data=clean_df, dv=dv, between=iv, covar=covars[0])
                    st.dataframe(res)
                    # Check IV p-value (which is usually the first row or indicated by the index/Source)
                    iv_row = res[res['Source'] == iv]
                    if not iv_row.empty:
                        p_val = iv_row['p-unc'].values[0]
                        if p_val < 0.05:
                            st.success(f"🎉 **结论 (Plain Language Interpretation)**: \n\n在排除了 `{covars[0]}` 的干扰后，`{iv}` 的主效应依然 **显著** (p < 0.05)。这证明了你的核心效应是非常稳健的！")
                        else:
                            st.error(f"📉 **结论 (Plain Language Interpretation)**: \n\n在加入协变量后，`{iv}` 的主效应 **不显著** (p >= 0.05)。这可能说明原本看到的组间差异，实际上是由你的协变量导致的。")
                else:
                    st.warning("⚠️ 平谷音(pingouin)标准包的 ANCOVA 接口倾向于单协变量。对于多协变量建议使用回归分析模块。这里我们将展示第一个协变量的 ANCOVA 结果：")
                    res = pg.ancova(data=clean_df, dv=dv, between=iv, covar=covars[0])
                    st.dataframe(res)
        
        # Simple plot
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.boxplot(x=iv, y=dv, data=clean_df, ax=ax, palette="Set2")
        sns.swarmplot(x=iv, y=dv, data=clean_df, color=".25", alpha=0.5, ax=ax)
        ax.set_title(f"{dv} by {iv}")
        plt.tight_layout()
        st.pyplot(fig)

    # ━━━━━━━━━━ Multi-group Regression Analysis ━━━━━━━━━━
    st.markdown("---")
    st.write("### 🌟 分组回归分析 (Multi-group Regression)")
    st.info('💡 **学术提示**：允许你按某个分类变量（如「高卷入度」VS「低卷入度」）将人群一分为二，然后在两组上分别跑**同一个回归模型**，直接对比回归系数 (β) 差异。这是社会学论文中经典的「断层分析」手法。')

    col_mg1, col_mg2, col_mg3 = st.columns(3)
    with col_mg1:
        mg_group = st.selectbox("分组变量 (类别型, 如高/低卷入度):", cols, key='mg_group')
    with col_mg2:
        mg_iv = st.selectbox("自变量 (IV, 数值型):", df.select_dtypes(include=['float64', 'int64']).columns.tolist(), key='mg_iv')
    with col_mg3:
        mg_dv = st.selectbox("因变量 (DV, 数值型):", df.select_dtypes(include=['float64', 'int64']).columns.tolist(), key='mg_dv')

    mg_extra_ivs = st.multiselect("附加自变量 (可选, 数值型):", df.select_dtypes(include=['float64', 'int64']).columns.tolist(), key='mg_extra')

    if st.button("运行分组回归", key='btn_mg'):
        import statsmodels.api as sm_mg
        import numpy as np_mg

        clean_cols_mg = [mg_group, mg_iv, mg_dv] + mg_extra_ivs
        clean_mg = df[clean_cols_mg].dropna()
        groups = clean_mg[mg_group].unique()

        if len(groups) < 2:
            st.error("分组变量至少需要 2 个不同类别！")
        else:
            st.markdown("---")
            results_list = []
            for g in groups:
                sub = clean_mg[clean_mg[mg_group] == g]
                iv_cols = [mg_iv] + mg_extra_ivs
                X = sm_mg.add_constant(sub[iv_cols])
                y = sub[mg_dv]
                model = sm_mg.OLS(y, X).fit()
                for var in iv_cols:
                    pv = model.pvalues[var]
                    results_list.append({
                        '分组': str(g),
                        '预测变量': var,
                        'β (系数)': f"{model.params[var]:.3f}{p_stars(pv)}",
                        'SE': f"{model.bse[var]:.3f}",
                        't值': f"{model.tvalues[var]:.3f}",
                        'p值': f"{pv:.4f}",
                        '显著性': p_stars(pv) if p_stars(pv) else "n.s.",
                    })
                results_list.append({
                    '分组': str(g),
                    '预测变量': '--- R² ---',
                    'β (系数)': f"{model.rsquared:.3f}",
                    'SE': '', 't值': '', 'p值': '', '显著性': ''
                })

            import pandas as pd_mg
            res_df = pd_mg.DataFrame(results_list)
            st.subheader("分组回归系数对比表")
            st.dataframe(res_df, use_container_width=True)

            # Summary interpretation
            st.info(f'📐 **白话解读**: 上表将 `{mg_group}` 的 {len(groups)} 个子群拆开，分别拟合了同一个回归模型。你可以直接对比每个组下自变量 `{mg_iv}` 的 β 系数大小和显著性。如果某一组显著而另一组不显著，说明该效应**仅对特定人群有效**——这正是论文中「断层效应」的核心证据。')

import statsmodels.api as sm
import statsmodels.formula.api as smf

def advanced_effects_module():
    st.title("模块六: 高级效应 (Mediation & Moderation)")
    
    with st.expander("💡 什么是中介与调节？为什么要做？我该怎么填？", expanded=True):
        st.markdown('''
        - **什么是中介效应 (Mediation)？** 解释的是**“为什么”起作用**。比如：看悲伤电影(IV) -> 导致心情变差(中介M) -> 导致购物欲下降(DV)。
        - **什么是调节效应 (Moderation)？** 解释的是**“什么时候”/对“谁”起作用**。比如：悲伤电影(IV)导致购物欲下降(DV)，但这个效应只在“低收入人群”(调节变量Mod)中存在。
        - **控制变量与层次回归**: 你可以额外加入“控制变量”。系统会为你输出标准的学术级层次回归三步走表格 (Hierarchical Regression) 和 $\\Delta R^2$。
        - **虚拟变量智能转换**: 系统允许你选用文本分类变量（如“高/低组”）作为自变量，它会在后台全自动转换为 0/1 虚拟变量 (Dummy Variables)。
        ''')

    if 'data' not in st.session_state:
        st.warning("⚠️ 请先在【数据上传】页面加载数据！")
        return
        
    df = st.session_state['data']
    cols = df.columns.tolist()
    
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    tab1, tab2 = st.tabs(["中介效应检验 (Model 4)", "调节效应检验 (Model 1)"])
    
    with tab1:
        st.subheader("中介效应分析 (Hayes Process Model 4 映射)")
        col1, col2, col3 = st.columns(3)
        with col1:
            m_iv = st.selectbox("自变量 (IV, 支持分类/数值):", cols, key='m_iv')
        with col2:
            m_med = st.selectbox("中介变量 (Mediator, 需数值):", numeric_cols, key='m_med')
        with col3:
            m_dv = st.selectbox("因变量 (DV, 需数值):", numeric_cols, key='m_dv')
            
        m_covars = st.multiselect("控制变量 (可选, 需数值):", numeric_cols, key='m_covars')
            
        if st.button("运行中介效应检验", key='btn_med'):
            clean_cols = [m_iv, m_med, m_dv] + m_covars
            clean_df = df[clean_cols].dropna().copy()
            
            # Dummy Conversion
            m_iv_eval = m_iv
            if not pd.api.types.is_numeric_dtype(clean_df[m_iv]):
                base_group = clean_df[m_iv].unique()[0]
                st.info(f"💡 **系统保护 (虚拟化转换)**: 检测到 `{m_iv}` 为分类变量，已自动以 `{base_group}` 为基准组 (Base Group) 转化为虚拟变量。")
                clean_df = pd.get_dummies(clean_df, columns=[m_iv], drop_first=True, dtype=float)
                dummy_cols = [c for c in clean_df.columns if c.startswith(f"{m_iv}_")]
                m_iv_eval = dummy_cols[0]
                if len(dummy_cols) > 1:
                    st.warning("自变量超过 2 个类别，本分析仅展示对第一个虚拟变量的中介检验。")
            
            st.markdown("---")
            X_cov = clean_df[m_covars] if m_covars else None
            
            # Step 1: IV -> DV (c path)
            st.write("### 步骤 1: 自变量预测因变量 (路径 c)")
            cols_1 = [m_iv_eval] + m_covars if m_covars else [m_iv_eval]
            X1 = sm.add_constant(clean_df[cols_1])
            model1 = sm.OLS(clean_df[m_dv], X1).fit()
            st.dataframe(pd.read_html(model1.summary().tables[1].as_html(), header=0, index_col=0)[0])
            c_p = model1.pvalues[m_iv_eval]
            
            # Step 2: IV -> Mediator (a path)
            st.write("### 步骤 2: 自变量预测中介变量 (路径 a)")
            model2 = sm.OLS(clean_df[m_med], X1).fit()
            st.dataframe(pd.read_html(model2.summary().tables[1].as_html(), header=0, index_col=0)[0])
            a_p = model2.pvalues[m_iv_eval]
            
            # Step 3: IV + Mediator -> DV (c' and b paths)
            st.write("### 步骤 3: 加入中介变量同测因变量 (路径 c' 和 b)")
            cols_3 = [m_iv_eval, m_med] + m_covars if m_covars else [m_iv_eval, m_med]
            X3 = sm.add_constant(clean_df[cols_3])
            model3 = sm.OLS(clean_df[m_dv], X3).fit()
            st.dataframe(pd.read_html(model3.summary().tables[1].as_html(), header=0, index_col=0)[0])
            cp_p = model3.pvalues[m_iv_eval]
            b_p = model3.pvalues[m_med]
            
            st.subheader("中介检验结论推断")
            if a_p < 0.05 and b_p < 0.05:
                # Calculate mediation proportion
                a_coeff = model2.params[m_iv_eval]
                b_coeff = model3.params[m_med]
                indirect_effect = a_coeff * b_coeff
                c_coeff = model1.params[m_iv_eval]
                
                if c_coeff != 0:
                    med_ratio = (indirect_effect / c_coeff) * 100
                else:
                    med_ratio = 0
                    
                med_ratio_str = f"约 **{abs(med_ratio):.1f}%**" if 0 < abs(med_ratio) <= 100 else "一部分"
                
                if cp_p >= 0.05:
                    st.success(f"🎉 **结论 (Plain Language Interpretation)**: \n\n路径 a 和 b 均显著，且加入中介后，自变量的主效应 (路径 c') 变得**不显著** ({cp_p:.3f})。这证明了存在 **完全中介效应**。也就是说，`{m_iv}` 对 `{m_dv}` 的影响，{med_ratio_str} 是通过 `{m_med}` 来传递实现的。")
                else:
                    st.success(f"🎉 **结论 (Plain Language Interpretation)**: \n\n路径 a 和 b 均显著，且加入中介后，自变量的主效应 (路径 c') 虽然下降但**依然显著** ({cp_p:.3f})。这证明了存在 **部分中介效应**。也就是说，`{m_iv}` 既直接影响了 `{m_dv}`，也有 {med_ratio_str} 的影响力是通过 `{m_med}` 间接传递给 `{m_dv}` 的。")
            else:
                st.error("📉 **结论 (Plain Language Interpretation)**: \n\n路径 a 或 路径 b 不显著。这说明中介效应**不成立**。")

    
    with tab2:
        st.subheader("调节效应分析 (Hayes Process Model 1 映射)")
        st.info("系统会对选入的数值型自变量和调节变量自动进行 **均值中心化 (Mean Centering)** 处理，极大降低带入乘积项时的多重共线性风险。")
        col1, col2, col3 = st.columns(3)
        with col1:
            mod_iv = st.selectbox("自变量 (IV, 支持分类/数值):", cols, key='mod_iv')
        with col2:
            mod_mod = st.selectbox("调节变量 (Moderator, 需数值):", numeric_cols, key='mod_mod')
        with col3:
            mod_dv = st.selectbox("因变量 (DV, 需数值):", numeric_cols, key='mod_dv')
            
        mod_covars = st.multiselect("控制变量 (可选, 需数值):", numeric_cols, key='mod_covars')
            
        if st.button("运行调节效应检验", key='btn_mod'):
            clean_cols = [mod_iv, mod_mod, mod_dv] + mod_covars
            clean_df = df[clean_cols].dropna().copy()
            
            # Dummy Conversion for IV
            mod_iv_eval = mod_iv
            if not pd.api.types.is_numeric_dtype(clean_df[mod_iv]):
                base_group = clean_df[mod_iv].unique()[0]
                st.info(f"💡 **系统保护 (虚拟化转换)**: 检测到 `{mod_iv}` 为分类变量，已自动以 `{base_group}` 为基准组转化为虚拟变量。")
                clean_df = pd.get_dummies(clean_df, columns=[mod_iv], drop_first=True, dtype=float)
                dummy_cols = [c for c in clean_df.columns if c.startswith(f"{mod_iv}_")]
                mod_iv_eval = dummy_cols[0]
                # for categorical IV, centering is usually not needed/meaningful as it's 0 or 1
            else:
                # Mean centering for continuous IV
                clean_df[f'{mod_iv}_center'] = clean_df[mod_iv] - clean_df[mod_iv].mean()
                mod_iv_eval = f'{mod_iv}_center'
                
            # Mean centering for continuous Mod
            clean_df[f'{mod_mod}_center'] = clean_df[mod_mod] - clean_df[mod_mod].mean()
            mod_mod_eval = f'{mod_mod}_center'
            
            # Interaction term
            clean_df['Interaction'] = clean_df[mod_iv_eval] * clean_df[mod_mod_eval]
            
            st.markdown("---")
            st.subheader("层次回归分析结果 (Hierarchical Regression)")
            
            # Model 1: Covariates only
            if mod_covars:
                X1 = sm.add_constant(clean_df[mod_covars])
            else:
                # If no covariates, just intercept model
                X1 = np.ones((len(clean_df), 1))
            model1 = sm.OLS(clean_df[mod_dv], X1).fit()
            
            # Model 2: Covariates + Main Effects
            X2_cols = mod_covars + [mod_iv_eval, mod_mod_eval] if mod_covars else [mod_iv_eval, mod_mod_eval]
            X2 = sm.add_constant(clean_df[X2_cols])
            model2 = sm.OLS(clean_df[mod_dv], X2).fit()
            
            # Model 3: Covariates + Main Effects + Interaction
            X3_cols = X2_cols + ['Interaction']
            X3 = sm.add_constant(clean_df[X3_cols])
            model3 = sm.OLS(clean_df[mod_dv], X3).fit()
            
            # Hierarchical R-squared summary
            rsq_df = pd.DataFrame({
                'Model 1 (仅控制)': [f"R² = {model1.rsquared:.3f}" if mod_covars else "N/A (无控制)"],
                'Model 2 (+主效应)': [f"R² = {model2.rsquared:.3f} | ΔR² = {max(0, model2.rsquared - model1.rsquared):.3f}"],
                'Model 3 (+交互项)': [f"R² = {model3.rsquared:.3f} | ΔR² = {max(0, model3.rsquared - model2.rsquared):.3f}"]
            }, index=['模型解释力']).T
            
            col_r1, col_r2 = st.columns([1, 2])
            with col_r1:
                st.write("**阶层 R² 变化总览**:")
                st.dataframe(rsq_df)
            
            with col_r2:
                st.write("**最终模型 (Model 3) 系数详情**:")
                st.dataframe(pd.read_html(model3.summary().tables[1].as_html(), header=0, index_col=0)[0])
            
            p_interaction = model3.pvalues['Interaction']
            if p_interaction < 0.05:
                st.success(f"🎉 **结论 (Plain Language Interpretation)**: \n\n乘积项 (Interaction) 达到显著水平 (p = {p_interaction:.4f} < 0.05)。说明 `{mod_mod}` 确实起到了显著的调节作用！这意味着 `{mod_iv}` 对 `{mod_dv}` 的影响，会随着 `{mod_mod}` 的不同而发生改变。")
                st.info("📐 **作图规范引导**: 你可以直接带入上述 Model 3 的系数去绘制简单斜率图 (Simple Slopes)。建议遵循顶级期刊标准：取调节变量的【均值 + 1个标准差】作为高分组，【均值 - 1个标准差】作为低分组来绘制基准线。")
            else:
                st.error(f"📉 **结论 (Plain Language Interpretation)**: \n\n乘积项未达到显著水平 (p = {p_interaction:.4f} >= 0.05)。说明调节效应不成立。`{mod_iv}` 对 `{mod_dv}` 的效应量并没有随着 `{mod_mod}` 的变化而显著改变。")


def main():
    st.sidebar.title("🧪 社会学实验分析台")
    st.sidebar.write("导航与配置：")
    
    tabs = ["数据上传与概览", "描述性统计", "信效度分析", "操作检验", "推断性统计", "高级效应"]
    choice = st.sidebar.radio("选择分析模块:", tabs)
    
    if choice == "数据上传与概览":
        app_data_upload_module()
    elif choice == "描述性统计":
        descriptive_statistics_module()
    elif choice == "信效度分析":
        reliability_validity_module()
    elif choice == "操作检验":
        manipulation_checks_module()
    elif choice == "推断性统计":
        inferential_statistics_module()
    elif choice == "高级效应":
        advanced_effects_module()

if __name__ == "__main__":
    main()
