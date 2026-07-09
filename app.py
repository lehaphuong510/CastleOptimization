import streamlit as st
import pandas as pd

# Cấu hình trang cơ bản để app mở full màn hình và có icon tab
st.set_page_config(page_title="Tối Ưu Nạp", page_icon="🎮", layout="wide")

# CSS cho Tiêu đề: Ánh vàng gold kim loại, in hoa, ép 1 dòng không rớt chữ
# CSS fix lỗi giao diện trên điện thoại
# CSS fix giao diện trên điện thoại và chỉnh màu sắc
st.markdown("""
    <style>
    /* 1. Xử lý Tiêu đề chính: Màu vàng gold, ép 1 dòng, co giãn theo tỷ lệ màn hình */
    .title-gold {
        background: linear-gradient(to right, #BF953F, #FCF6BA, #B38728, #FBF5B7, #AA771C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        white-space: nowrap;
        font-size: min(6.5vw, 35px);
        font-weight: 900;
        text-align: center;
        padding-bottom: 20px;
        width: 100%;
    }

    /* 2. Đổi màu thẻ h2 (Part 1, 2, 3) thành gradient hồng đậm đổ qua tím */
    h2 {
        background: linear-gradient(to right, #D81B60, #8E24AA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }

    /* 3. Chống rớt chữ cho thẻ h2 trên màn hình điện thoại (max-width: 768px) */
    @media (max-width: 768px) {
        h2 {
            font-size: min(5.5vw, 24px) !important; 
            white-space: nowrap !important;
        }
    }
    </style>
    <h1 class="title-gold">CASTLE OPTIMIZATION</h1>
    """, unsafe_allow_html=True)

# M điền MÃ_ID_CỦA_SHEET của m vào đây
SHEET_ID = "1BoaL94VL1olNHyz_ZOQRcnkRCeUG4Q_vNmxmnNkDFpw"

@st.cache_data(ttl=600) # Tự refresh dữ liệu mỗi 10 phút
def load_data():
    # URL đọc trực tiếp từ Sheets
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=GemCard"
    df_gemcard = pd.read_csv(url)
    
    # URL cho các sheet còn lại (Gold, Combo)
    url_gold = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Gold"
    df_gold = pd.read_csv(url_gold)
    
    url_combo = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Combo"
    df_combo = pd.read_csv(url_combo)
    
    # Xử lý dọn dẹp số liệu
    df_gemcard['Value'] = df_gemcard['Value'].astype(str).str.replace('.', '', regex=False).str.replace(' đ', '', regex=False).str.strip().astype(int)
    
    df_gem = df_gemcard[df_gemcard['Pack'].str.startswith('Gem')].copy()
    df_card = df_gemcard[df_gemcard['Pack'].str.startswith('Card')].copy()
    
    return df_gem, df_card, df_gold, df_combo

# ==========================================
# KHỞI TẠO DỮ LIỆU (ĐÂY LÀ DÒNG CHỐNG SẬP APP)
# ==========================================
df_gem, df_card, df_gold, df_combo = load_data()

# ==========================================
# 2. TÍNH TỶ GIÁ GỐC DỰA TRÊN GÓI RẺ NHẤT
# ==========================================
gem_base_rate = (df_gem['Value'] / df_gem['Qnt']).min()  # VND / 1 Ngọc
card_base_rate = (df_card['Value'] / df_card['Qnt']).min() # VND / 1 Thẻ
gold_base_rate = (df_gold['Gem2trade'] / df_gold['Qnt']).min() * gem_base_rate # VND / 1 Vàng

# ==========================================
# 3. THUẬT TOÁN TỐI ƯU HÓA (UNBOUNDED KNAPSACK)
# ==========================================
def optimize_knapsack(budget, df, name_col, weight_col, value_col, scale=1):
    budget_scaled = int(budget / scale)
    items = []
    for _, row in df.iterrows():
        items.append({
            'name': row[name_col],
            'weight': int(row[weight_col] / scale),
            'value': float(row[value_col])
        })

    dp = [0.0] * (budget_scaled + 1)
    choice = [-1] * (budget_scaled + 1)

    for w in range(1, budget_scaled + 1):
        for i, item in enumerate(items):
            if item['weight'] <= w:
                if dp[w - item['weight']] + item['value'] > dp[w]:
                    dp[w] = dp[w - item['weight']] + item['value']
                    choice[w] = i

    res = {}
    curr = budget_scaled
    while curr > 0 and choice[curr] != -1:
        idx = choice[curr]
        name = items[idx]['name']
        res[name] = res.get(name, 0) + 1
        curr -= items[idx]['weight']

    remaining_budget = curr * scale
    return res, dp[budget_scaled], remaining_budget


# ==========================================
# GIAO DIỆN NGƯỜI DÙNG (UI)
# ==========================================
col1, col2 = st.columns(2)

# --- PART 1: TỪ TIỀN SANG NGỌC/THẺ ---
with col1:
    st.header("💸 PART 1: MONEY OPTIMIZATION")
    budget_input = st.number_input("1. Bạn có bao nhiêu tiền (VND)?", min_value=0, step=10000, value=500000)
    target_1 = st.radio("2. Bạn muốn mua gì?", ["Ngọc (Gems)", "Thẻ (Cards)"], horizontal=True)

    if st.button("Tối ưu Nạp", type="primary"):
        if target_1 == "Ngọc (Gems)":
            res, max_val, rem = optimize_knapsack(budget_input, df_gem, 'Pack', 'Value', 'Qnt', scale=1000)
            target_name = "Ngọc"
        else:
            res, max_val, rem = optimize_knapsack(budget_input, df_card, 'Pack', 'Value', 'Qnt', scale=1000)
            target_name = "Thẻ"

        st.success("✅ **KẾT QUẢ TỐI ƯU:**")
        st.write(f"- **Tổng {target_name} nhận được:** {int(max_val):,} 💎")
        st.write(f"- **Tiền thật còn thừa:** {int(rem):,} VND")
        st.write("- **Các gói cần mua:**")
        for k, v in res.items():
            st.write(f"  📦 Mua **{v}x** gói `{k}`")

        if target_1 == "Ngọc (Gems)":
            st.session_state['current_gems'] = int(max_val)

# --- PART 2: TỪ NGỌC ĐỔI SANG TÀI NGUYÊN ---
with col2:
    st.header("💎 PART 2: GEM OPTIMIZATION")
    default_gems = st.session_state.get('current_gems', 1000)
    gem_input = st.number_input("1. Bạn có bao nhiêu Ngọc?", min_value=0, step=100, value=default_gems)

    target_2 = st.selectbox("2. Bạn muốn đổi từ Ngọc sang gì?", ["Vàng (Gold)", "Combo (Vàng + Thẻ)"])
    goal_options = ["Tối đa số lượng Vàng", "ROI lớn nhất (Giá trị VND thực tế lớn nhất)"]
    goal_2 = st.selectbox("3. Mục tiêu của bạn là gì?", goal_options)

    st.write("4. Bạn có điều kiện gì về Ngọc không? (Optional)")
    cond_col1, cond_col2 = st.columns([1, 2])
    operator = cond_col1.selectbox("Điều kiện", ["Không", "Giữ lại ít nhất (>=)"])
    min_gems_left = cond_col2.number_input("Số Ngọc", min_value=0, step=50, value=300)

    if st.button("Tối ưu Quy Đổi", type="primary"):
        usable_gems = gem_input
        if operator == "Giữ lại ít nhất (>=)":
            usable_gems = gem_input - min_gems_left

        if usable_gems < 0:
            st.error("❌ Số Ngọc của bạn không đủ để đáp ứng điều kiện giữ lại!")
        else:
            if target_2 == "Vàng (Gold)":
                df_target = df_gold.copy()
                if goal_2 == "Tối đa số lượng Vàng":
                    df_target['Optimize_Value'] = df_target['Qnt']
                else: 
                    df_target['Optimize_Value'] = df_target['Qnt'] * gold_base_rate

                res, max_val, rem = optimize_knapsack(usable_gems, df_target, 'Goldpack', 'Gem2trade', 'Optimize_Value')

                total_gold = sum([v * df_target[df_target['Goldpack']==k]['Qnt'].values[0] for k, v in res.items()])
                total_card = 0

            else: # Combo
                df_target = df_combo.copy()
                if goal_2 == "Tối đa số lượng Vàng":
                    df_target['Optimize_Value'] = df_target['Gold.Qnt']
                else: 
                    df_target['Optimize_Value'] = (df_target['Gold.Qnt'] * gold_base_rate) + (df_target['Card.Qnt'] * card_base_rate)

                res, max_val, rem = optimize_knapsack(usable_gems, df_target, 'Combo', 'Gem2trade', 'Optimize_Value')

                total_gold = sum([v * df_target[df_target['Combo']==k]['Gold.Qnt'].values[0] for k, v in res.items()])
                total_card = sum([v * df_target[df_target['Combo']==k]['Card.Qnt'].values[0] for k, v in res.items()])

            st.success("✅ **KẾT QUẢ TỐI ƯU:**")
            st.write(f"- **Vàng thu được:** {int(total_gold):,} 🪙")
            if target_2 == "Combo (Vàng + Thẻ)":
                st.write(f"- **Thẻ thu được:** {int(total_card):,} 🃏")
                if goal_2 == "ROI lớn nhất (Giá trị VND thực tế lớn nhất)":
                    st.write(f"- **Giá trị thực tế (VND):** {int(max_val):,} đ *(Mức sinh lời tối đa)*")

            st.write(f"- **Số Ngọc còn dư:** {int(rem + (gem_input - usable_gems)):,} 💎")
            st.write("- **Chiến lược đổi gói:**")
            if res:
                for k, v in res.items():
                    st.write(f"  🛒 Đổi **{v}x** `{k}`")
            else:
                st.write("  ⚠️ *Không đủ Ngọc để đổi bất kỳ gói nào!*")

# --- PART 3: ĐÁNH GIÁ MỨC HẤP DẪN CỦA SEASONAL PACKAGE ---
st.divider() 
st.header("🎁 Part 3: SEASONAL PACKAGE")

buy_method = st.radio("1. Package này mua bằng tiền hay trade bằng Ngọc?", ("Tiền", "Ngọc"))

if buy_method == "Tiền":
    cost_vnd = st.number_input("Giá tiền mua (VNĐ)", min_value=0, step=1000)
    cost_gem = 0
else:
    cost_gem = st.number_input("Số ngọc đem trade", min_value=0, step=100)
    cost_vnd = 0

st.markdown("**2. Trong Package có những gì? (Chỉ điền món có trong gói, không có cứ để số 0)**")
col1_s, col2_s, col3_s = st.columns(3)
with col1_s:
    pack_gem = st.number_input("Số Ngọc có", min_value=0, step=100)
with col2_s:
    pack_gold = st.number_input("Số Vàng có", min_value=0, step=1000)
with col3_s:
    pack_card = st.number_input("Số Thẻ có", min_value=0, step=1)

if st.button("ROI OF SEASONAL PACKAGE", type="primary"):
    try:
        # BƯỚC A: QUY TOÀN BỘ GIÁ TRỊ GÓI RA VNĐ (Sử dụng tỷ giá gốc cực chuẩn ở phần 2)
        val_from_gem = pack_gem * gem_base_rate
        val_from_gold = pack_gold * gold_base_rate
        val_from_card = pack_card * card_base_rate
        
        total_pack_value_vnd = val_from_gem + val_from_gold + val_from_card

        # BƯỚC B: QUY CHI PHÍ GỐC RA VNĐ
        if buy_method == "Tiền":
            cost_in_vnd = cost_vnd
            cost_display = f"{cost_vnd:,.0f} VNĐ"
        else:
            cost_in_vnd = cost_gem * gem_base_rate
            cost_display = f"{cost_gem:,.0f} Ngọc"

        # BƯỚC C: TÍNH ROI
        if cost_in_vnd > 0:
            roi = ((total_pack_value_vnd - cost_in_vnd) / cost_in_vnd) * 100
        else:
            roi = 0

        # HIỂN THỊ KẾT QUẢ
        st.markdown("### 📊 KẾT QUẢ ĐÁNH GIÁ:")
        
        if roi > 0:
            st.success(f"**🔥 ROI của Package là: +{roi:,.1f}% (LỜI)**")
        elif roi < 0:
            st.error(f"**❄️ ROI của Package là: {roi:,.1f}% (LỖ)**")
        else:
            st.info(f"**⚖️ ROI của Package là: {roi:,.1f}% (HUỀ VỐN)**")

        # Phân bổ ngân sách để xem bình thường số tiền đó mua được bao nhiêu
        if total_pack_value_vnd > 0:
            ratio_gem = val_from_gem / total_pack_value_vnd
            ratio_gold = val_from_gold / total_pack_value_vnd
            ratio_card = val_from_card / total_pack_value_vnd
        else:
            ratio_gem = ratio_gold = ratio_card = 0

        std_gem_bought = (cost_in_vnd * ratio_gem) / gem_base_rate if gem_base_rate > 0 else 0
        std_gold_bought = (cost_in_vnd * ratio_gold) / gold_base_rate if gold_base_rate > 0 else 0
        std_card_bought = (cost_in_vnd * ratio_card) / card_base_rate if card_base_rate > 0 else 0

        st.markdown(f"**Theo thông thường, với {cost_display} m chỉ mua được lượng quy đổi tương đương là:**")
        
        if pack_gem > 0:
            st.write(f"- 💎 **{std_gem_bought:,.0f} Ngọc** *(Mức m đang được nhận: {pack_gem:,.0f})*")
        if pack_gold > 0:
            st.write(f"- 🪙 **{std_gold_bought:,.0f} Vàng** *(Mức m đang được nhận: {pack_gold:,.0f})*")
        if pack_card > 0:
            st.write(f"- 🃏 **{std_card_bought:,.0f} Thẻ** *(Mức m đang được nhận: {pack_card:,.0f})*")

    except Exception as e:
        st.error(f"Có lỗi hệ thống: {e}")
