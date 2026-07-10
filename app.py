import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tối Ưu Nạp", page_icon="🎮", layout="wide")

st.markdown("""
    <style>
    .title-gold {
        background: linear-gradient(to right, #BF953F, #FCF6BA, #B38728, #FBF5B7, #AA771C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        white-space: nowrap;
        font-weight: 900;
        text-align: left;
        padding-bottom: 20px;
        width: 100%;
        font-size: 40px;
    }
    h2 {
        background: linear-gradient(to right, #D81B60, #8E24AA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    @media (max-width: 768px) {
        .title-gold { font-size: 8vw !important; }
        h2 { font-size: 5.5vw !important; white-space: nowrap !important; }
    }
    </style>
    <h1 class="title-gold">CASTLE OPTIMIZATION</h1>
    """, unsafe_allow_html=True)

SHEET_ID = "1BoaL94VL1olNHyz_ZOQRcnkRCeUG4Q_vNmxmnNkDFpw"

@st.cache_data(ttl=600)
def load_data():
    url_base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    df_gemcard = pd.read_csv(url_base + "GemCard")
    df_gold = pd.read_csv(url_base + "Gold")
    df_combo = pd.read_csv(url_base + "Combo")
    df_wood = pd.read_csv(url_base + "Wood") # Thêm Wood
    
    df_gemcard['Value'] = df_gemcard['Value'].astype(str).str.replace('.', '', regex=False).str.replace(' đ', '', regex=False).str.strip().astype(int)
    df_gem = df_gemcard[df_gemcard['Pack'].str.startswith('Gem')].copy()
    df_card = df_gemcard[df_gemcard['Pack'].str.startswith('Card')].copy()
    
    return df_gem, df_card, df_gold, df_combo, df_wood

df_gem, df_card, df_gold, df_combo, df_wood = load_data()

gem_base_rate = (df_gem['Value'] / df_gem['Qnt']).min()
card_base_rate = (df_card['Value'] / df_card['Qnt']).min()
gold_base_rate = (df_gold['Gem2trade'] / df_gold['Qnt']).min() * gem_base_rate
wood_base_rate = (df_wood['Gem2trade'] / df_wood['Qnt']).min() * gem_base_rate # Tỷ giá Gỗ

def optimize_knapsack(budget, df, name_col, weight_col, value_col, scale=1):
    budget_scaled = int(budget / scale)
    items = [{'name': row[name_col], 'weight': int(row[weight_col]/scale), 'value': float(row[value_col])} for _, row in df.iterrows()]
    dp = [0.0] * (budget_scaled + 1)
    choice = [-1] * (budget_scaled + 1)
    for w in range(1, budget_scaled + 1):
        for i, item in enumerate(items):
            if item['weight'] <= w and dp[w - item['weight']] + item['value'] > dp[w]:
                dp[w] = dp[w - item['weight']] + item['value']
                choice[w] = i
    res, curr = {}, budget_scaled
    while curr > 0 and choice[curr] != -1:
        idx = choice[curr]
        res[items[idx]['name']] = res.get(items[idx]['name'], 0) + 1
        curr -= items[idx]['weight']
    return res, dp[budget_scaled], curr * scale

col1, col2 = st.columns(2)

with col1:
    st.header("💸 PART 1: MONEY OPTIMIZATION")
    budget_input = st.number_input("1. Bạn có bao nhiêu tiền (VND)?", min_value=0, step=10000, value=500000)
    target_1 = st.radio("2. Bạn muốn mua gì?", ["Ngọc (Gems)", "Thẻ (Cards)"], horizontal=True)
    if st.button("Tối ưu Nạp", type="primary"):
        df_use = df_gem if target_1 == "Ngọc (Gems)" else df_card
        res, max_val, rem = optimize_knapsack(budget_input, df_use, 'Pack', 'Value', 'Qnt', scale=1000)
        st.success("✅ **KẾT QUẢ TỐI ƯU:**")
        st.write(f"- **Tổng {target_1.split(' ')[0]} nhận được:** {int(max_val):,} 💎/🃏")
        for k, v in res.items(): st.write(f"  📦 Mua **{v}x** gói `{k}`")
        if target_1 == "Ngọc (Gems)": st.session_state['current_gems'] = int(max_val)

with col2:
    st.header("💎 PART 2: GEM OPTIMIZATION")
    gem_input = st.number_input("1. Bạn có bao nhiêu Ngọc?", min_value=0, step=100, value=st.session_state.get('current_gems', 1000))
    target_2 = st.selectbox("2. Bạn muốn đổi từ Ngọc sang gì?", ["Vàng (Gold)", "Gỗ (Wood)", "Combo (Vàng + Thẻ)"])
    goal_2 = st.selectbox("3. Mục tiêu của bạn là gì?", ["Tối đa số lượng", "ROI lớn nhất"])

    if st.button("Tối ưu Quy Đổi", type="primary"):
        df_target = df_gold if target_2 == "Vàng (Gold)" else (df_wood if target_2 == "Gỗ (Wood)" else df_combo)
        col_weight = 'Gem2trade'
        col_val = 'Qnt' if goal_2 == "Tối đa số lượng" else ('Optimize_Value')
        
        if goal_2 != "Tối đa số lượng":
            if target_2 == "Vàng (Gold)": df_target['Optimize_Value'] = df_target['Qnt'] * gold_base_rate
            elif target_2 == "Gỗ (Wood)": df_target['Optimize_Value'] = df_target['Qnt'] * wood_base_rate
            else: df_target['Optimize_Value'] = (df_target['Gold.Qnt'] * gold_base_rate) + (df_target['Card.Qnt'] * card_base_rate)
            
        res, max_val, rem = optimize_knapsack(gem_input, df_target, df_target.columns[0], col_weight, col_val)
        st.success("✅ **KẾT QUẢ TỐI ƯU:**")
        for k, v in res.items(): st.write(f"  🛒 Đổi **{v}x** `{k}`")

st.divider()
st.header("🎁 Part 3: SEASONAL PACKAGE")
buy_method = st.radio("1. Mua bằng Tiền hay Ngọc?", ("Tiền", "Ngọc"))
cost = st.number_input("Giá tiền/Ngọc:", min_value=0)
c1, c2, c3, c4 = st.columns(4)
pack_gem = c1.number_input("Ngọc", 0); pack_gold = c2.number_input("Vàng", 0)
pack_card = c3.number_input("Thẻ", 0); pack_wood = c4.number_input("Gỗ", 0)

if st.button("ROI OF SEASONAL PACKAGE", type="primary"):
    total_val = (pack_gem * gem_base_rate) + (pack_gold * gold_base_rate) + (pack_card * card_base_rate) + (pack_wood * wood_base_rate)
    cost_vnd = cost if buy_method == "Tiền" else cost * gem_base_rate
    roi = ((total_val - cost_vnd) / cost_vnd * 100) if cost_vnd > 0 else 0
    st.markdown(f"### 📊 ROI: {roi:,.1f}%")
