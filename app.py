from datetime import datetime
from io import BytesIO
import os
import sqlite3
import pandas as pd
import streamlit as st

# =========================================================
# 1. CẤU HÌNH TRANG & BẢNG MÀU ACB (NAVY & GOLD)
# =========================================================

st.set_page_config(
    page_title="ACB Smart Lead & Sales Hub",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tên file ảnh logo đuôi JPG trong thư mục dự án
LOGO_FILE_PATH = "acb_logo.jpg"

# Custom CSS: ACB Branding - Dark Blue & Gold Accents
st.markdown(
    """
<style>
    /* Tổng thể ứng dụng */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Sidebar thiết kế phẳng hiện đại */
    [data-testid="stSidebar"] {
        background-color: #0d2c54 !important;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Header chính phong cách Ngân hàng ACB */
    .acb-banner {
        background: linear-gradient(120deg, #0d2c54 0%, #1e50a2 60%, #00a8e8 100%);
        padding: 24px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        border-bottom: 4px solid #f39c12;
        box-shadow: 0 4px 12px rgba(13, 44, 84, 0.15);
    }
    .acb-banner h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .acb-banner p {
        margin: 6px 0 0 0;
        font-size: 14px;
        opacity: 0.9;
    }

    /* Thẻ hiển thị chỉ số (KPI Metric Cards) */
    .kpi-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        text-align: center;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #0d2c54;
    }
    .kpi-label {
        font-size: 13px;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 600;
        margin-top: 4px;
    }

    /* Thẻ hồ sơ khách hàng phân cấp */
    .lead-box {
        background: white;
        padding: 16px 20px;
        border-radius: 10px;
        border-left: 6px solid #cbd5e1;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 12px;
    }
    .lead-priority-p1 { border-left-color: #ef4444; background: #fff5f5; }
    .lead-priority-p2 { border-left-color: #f59e0b; background: #fffbeb; }
    .lead-priority-p3 { border-left-color: #10b981; background: #f0fdf4; }

    .tag-tier {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .tier-p1 { background: #fee2e2; color: #991b1b; }
    .tier-p2 { background: #fef3c7; color: #92400e; }
    .tier-p3 { background: #d1fae5; color: #065f46; }
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# 2. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE
# =========================================================

DB_FILE = "acb_sales_db.sqlite"


def connect_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def setup_database():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS acb_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_code TEXT,
            created_date TEXT,
            full_name TEXT,
            phone_num TEXT,
            email_addr TEXT,
            segment TEXT,
            monthly_income REAL,
            credit_score_cis INTEGER,
            main_demand TEXT,
            target_amount REAL,
            urgency_level TEXT,
            scoring_points INTEGER,
            priority_tier TEXT,
            sales_stage TEXT,
            assigned_officer TEXT,
            last_interaction TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()


setup_database()


# =========================================================
# 3. THUẬT TOÁN ĐÁNH GIÁ VÀ GỢI Ý SẢN PHẨM
# =========================================================


def evaluate_acb_lead(segment, income, cis_score, demand, amount, urgency):
    score = 0

    if segment == "Khách hàng Ưu tiên (ACB Privilege)":
        score += 35
    elif segment == "Khách hàng Doanh nghiệp SME":
        score += 30
    elif segment == "Khách hàng Cá nhân Lương Qua Thẻ":
        score += 25
    else:
        score += 15

    if income >= 80:
        score += 25
    elif income >= 40:
        score += 20
    elif income >= 20:
        score += 15
    else:
        score += 10

    if cis_score >= 700:
        score += 20
    elif cis_score >= 600:
        score += 15
    else:
        score += 5

    if urgency == "Gấp (Trong 7 ngày)":
        score += 20
    elif urgency == "Trong tháng này":
        score += 12
    else:
        score += 5

    score = min(score, 100)

    if score >= 80:
        tier = "P1 - CẤP THIẾT"
    elif score >= 55:
        tier = "P2 - TIỀM NĂNG"
    else:
        tier = "P3 - NỀN TẢNG"

    return score, tier


def recommend_acb_products(demand, income, amount):
    recs = []
    if demand == "Vay thế chấp mua BĐS":
        recs.append("🏠 Gói vay mua nhà ACB - Lãi suất ưu đãi từ 6.5%/năm")
    elif demand == "Vay sản xuất kinh doanh":
        recs.append("💼 Vay kinh doanh ACB Green Finance - Hạn mức tới 10 tỷ")
    elif demand == "Vay tín chấp tiêu dùng":
        if income >= 20:
            recs.append("💳 Vay tín chấp theo lương ACB - Cấp vốn nhanh 48h")
        recs.append("💳 Thẻ tín dụng ACB Visa Signature / JCB Ultimate")
    elif demand == "Gửi tiết kiệm & Đầu tư":
        if amount >= 500:
            recs.append("💎 Tiết kiệm ACB Măng Non / Tích Lũy Tương Lai")
            recs.append("📈 Chứng chỉ tiền gửi ACB ngắn/dài hạn")
        else:
            recs.append("💰 Tiết kiệm Trực tuyến ACB ONE - Lãi suất cộng thêm 0.3%")
    return recs


def format_currency_vnd(val):
    if pd.isna(val) or val is None:
        return "0 VNĐ"
    val = float(val)
    if val < 1000000:
        val = val * 1000000
    return f"{int(val):,}".replace(",", ".") + " VNĐ"


# =========================================================
# 4. HÀM TƯƠNG TÁC DATABASE
# =========================================================


def fetch_all_leads():
    conn = connect_db()
    df = pd.read_sql_query("SELECT * FROM acb_leads ORDER BY id DESC", conn)
    conn.close()
    return df


def insert_lead(record):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO acb_leads (
            lead_code, created_date, full_name, phone_num, email_addr, segment,
            monthly_income, credit_score_cis, main_demand, target_amount, urgency_level,
            scoring_points, priority_tier, sales_stage, assigned_officer, last_interaction, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        tuple(record.values()),
    )
    conn.commit()
    conn.close()


def update_lead_stage(lead_id, new_stage):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE acb_leads SET sales_stage = ? WHERE id = ?", (new_stage, lead_id)
    )
    conn.commit()
    conn.close()


def remove_lead(lead_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM acb_leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()


# =========================================================
# 5. THANH ĐIỀU HƯỚNG SIDEBAR
# =========================================================

with st.sidebar:
    if os.path.exists(LOGO_FILE_PATH):
        # Đã cập nhật tương thích các bản Streamlit
        try:
            st.image(LOGO_FILE_PATH, use_container_width=True)
        except TypeError:
            st.image(LOGO_FILE_PATH, use_column_width=True)
    else:
        st.markdown(
            """
            <div style="text-align: center; padding: 10px 0;">
                <h1 style="color: #ffffff; font-size: 26px; margin: 0; font-weight: 800;">ACB BANK</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="text-align: center; margin-top: 5px; margin-bottom: 10px;">
            <p style="color: #00a8e8; font-size: 13px; font-weight: 600; margin: 0;">Smart Sales & Lead Portal</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    nav_choice = st.radio(
        "ĐIỀU HÀNH HỆ THỐNG",
        [
            "⚡ Bảng điều khiển Sales",
            "📥 Tiếp nhận Lead mới",
            "📂 Quản lý danh sách KH",
            "🔀 Tiến trình xử lý (Kanban)",
            "🧮 Công cụ tính nhanh Khoản vay",
            "📊 Báo cáo tăng trưởng",
        ],
    )

    st.divider()
    st.caption("Ngân hàng TMCP Á Châu (ACB)\nTrung tâm Phát triển Kinh doanh")

# Banner Tiêu đề Trang
st.markdown(
    """
    <div class="acb-banner">
        <h1>💙 ACB SMART LEAD & SALES HUB</h1>
        <p>Hệ thống Quản trị Khách hàng Tiềm năng & Hỗ trợ Tư vấn Kinh doanh - Ngân hàng Á Châu</p>
    </div>
    """,
    unsafe_allow_html=True,
)

df_data = fetch_all_leads()

# =========================================================
# 6. GIAO DIỆN CÁC MỤC CHỨC NĂNG
# =========================================================

# --- MỤC 1: BẢNG ĐIỀU KHIỂN SALES ---
if nav_choice == "⚡ Bảng điều khiển Sales":
    st.markdown("### 📈 Chỉ số kinh doanh tổng quan")

    total_leads = len(df_data)
    p1_count = (
        len(df_data[df_data["priority_tier"] == "P1 - CẤP THIẾT"])
        if total_leads
        else 0
    )
    p2_count = (
        len(df_data[df_data["priority_tier"] == "P2 - TIỀM NĂNG"])
        if total_leads
        else 0
    )
    p3_count = (
        len(df_data[df_data["priority_tier"] == "P3 - NỀN TẢNG"])
        if total_leads
        else 0
    )

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-value">{total_leads}</div><div class="kpi-label">Tổng Lead Tiếp Nhận</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-value" style="color:#ef4444;">{p1_count}</div><div class="kpi-label">P1 - Cần Xử Lý Ngay</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-value" style="color:#f59e0b;">{p2_count}</div><div class="kpi-label">P2 - Khách Tiềm Năng</div></div>',
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-value" style="color:#10b981;">{p3_count}</div><div class="kpi-label">P3 - Đang Nuôi Dưỡng</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown("### 🔥 Khách hàng cấp thiết cần liên hệ ngay (Top P1 Priority)")

    if total_leads == 0:
        st.info("Chưa có dữ liệu khách hàng. Vui lòng thêm hồ sơ mới.")
    else:
        top_p1 = df_data[df_data["priority_tier"] == "P1 - CẤP THIẾT"].head(4)
        if top_p1.empty:
            st.success("Không có khách hàng tồn đọng ở nhóm P1!")
        else:
            for _, r in top_p1.iterrows():
                recs = recommend_acb_products(
                    r["main_demand"], r["monthly_income"], r["target_amount"]
                )
                rec_text = " | ".join(recs) if recs else "Chưa có gợi ý"
                st.markdown(
                    f"""
                    <div class="lead-box lead-priority-p1">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:18px; font-weight:700; color:#0d2c54;">👤 {r['full_name']}</span>
                            <span class="tag-tier tier-p1">{r['priority_tier']}</span>
                        </div>
                        <div style="margin-top:8px; font-size:14px; color:#334155;">
                            📞 <b>SĐT:</b> {r['phone_num']} &nbsp;|&nbsp; 🏢 <b>Phân hạng:</b> {r['segment']} &nbsp;|&nbsp; 🎯 <b>Nhu cầu:</b> {r['main_demand']} ({format_currency_vnd(r['target_amount'])})
                        </div>
                        <div style="margin-top:6px; font-size:13px; color:#0284c7;">
                            💡 <b>Gợi ý gói ACB:</b> {rec_text}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# --- MỤC 2: TIẾP NHẬN LEAD MỚI ---
elif nav_choice == "📥 Tiếp nhận Lead mới":
    st.markdown("### 📥 Khai báo thông tin Khách hàng Tiềm năng (ACB Lead Entry)")
    st.caption(
        "Nhập dữ liệu khách hàng để hệ thống tự động tính điểm tín nhiệm và phân hạng tư vấn."
    )

    with st.form("form_create_lead", clear_on_submit=True):
        c1, c2 = st.columns(2)

        with c1:
            full_name = st.text_input("Họ và tên khách hàng *")
            phone_num = st.text_input("Số điện thoại liên hệ *")
            email_addr = st.text_input("Địa chỉ Email")
            segment = st.selectbox(
                "Phân hạng khách hàng",
                [
                    "Khách hàng Cá nhân Lợi thế",
                    "Khách hàng Cá nhân Lương Qua Thẻ",
                    "Khách hàng Ưu tiên (ACB Privilege)",
                    "Khách hàng Doanh nghiệp SME",
                ],
            )
            monthly_income = st.number_input(
                "Thu nhập bình quân hàng tháng (Triệu VNĐ)",
                min_value=0.0,
                value=25.0,
                step=5.0,
            )

        with c2:
            cis_score = st.slider(
                "Điểm tín dụng CIS nội bộ/CIC (Dự kiến)", 300, 850, 680
            )
            main_demand = st.selectbox(
                "Nhu cầu tài chính chính",
                [
                    "Vay thế chấp mua BĐS",
                    "Vay sản xuất kinh doanh",
                    "Vay tín chấp tiêu dùng",
                    "Gửi tiết kiệm & Đầu tư",
                    "Mở thẻ tín dụng cao cấp",
                ],
            )
            target_amount = st.number_input(
                "Giá trị nhu cầu (Triệu VNĐ)",
                min_value=0.0,
                value=1000.0,
                step=100.0,
            )
            urgency_level = st.select_slider(
                "Mức độ cấp thiết",
                options=[
                    "Tham khảo",
                    "Trong vòng 3 tháng",
                    "Trong tháng này",
                    "Gấp (Trong 7 ngày)",
                ],
            )
            assigned_officer = st.text_input(
                "Chuyên viên tư vấn (RM/CSR phụ trách)", value="RM. Nguyễn Văn A"
            )

        notes = st.text_area("Ghi chú đặc điểm khách hàng / Lịch hẹn cuộc gọi")

        btn_submit = st.form_submit_button("💾 LƯU HỒ SƠ & TÍNH ĐIỂM TIỀM NĂNG")

    if btn_submit:
        if not full_name.strip() or not phone_num.strip():
            st.error("⚠️ Vui lòng cung cấp tối thiểu Họ tên và Số điện thoại!")
        else:
            score, tier = evaluate_acb_lead(
                segment,
                monthly_income,
                cis_score,
                main_demand,
                target_amount,
                urgency_level,
            )
            code = "ACB" + datetime.now().strftime("%y%m%d%H%M%S")
            c_date = datetime.now().strftime("%Y-%m-%d %H:%M")

            new_record = {
                "lead_code": code,
                "created_date": c_date,
                "full_name": full_name,
                "phone_num": phone_num,
                "email_addr": email_addr,
                "segment": segment,
                "monthly_income": monthly_income,
                "credit_score_cis": cis_score,
                "main_demand": main_demand,
                "target_amount": target_amount,
                "urgency_level": urgency_level,
                "scoring_points": score,
                "priority_tier": tier,
                "sales_stage": "1. Mới ghi nhận",
                "assigned_officer": assigned_officer,
                "last_interaction": c_date,
                "notes": notes,
            }

            insert_lead(new_record)
            st.success(f"✅ Đã lưu hồ sơ thành công cho khách hàng: {full_name}")
            st.info(
                f"📊 Kết quả đánh giá: Điểm **{score}/100** -> Hạng ưu tiên: **{tier}**"
            )

# --- MỤC 3: QUẢN LÝ DANH SÁCH HỒ SƠ ---
elif nav_choice == "📂 Quản lý danh sách KH":
    st.markdown("### 📂 Danh sách Khách hàng & Thao tác Chăm sóc")

    if df_data.empty:
        st.warning("Hiện tại chưa có dữ liệu trong hệ thống database.")
    else:
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            search_kw = st.text_input("🔍 Tìm tên hoặc SĐT")
        with f_col2:
            filter_tier = st.selectbox(
                "Phân hạng ưu tiên",
                ["Tất cả", "P1 - CẤP THIẾT", "P2 - TIỀM NĂNG", "P3 - NỀN TẢNG"],
            )
        with f_col3:
            filter_stage = st.selectbox(
                "Giai đoạn tư vấn",
                [
                    "Tất cả",
                    "1. Mới ghi nhận",
                    "2. Đã liên hệ lần 1",
                    "3. Đang lập hồ sơ",
                    "4. Đang thẩm định",
                    "5. Chốt thành công",
                    "6. Thất bại / Huỷ",
                ],
            )

        df_filtered = df_data.copy()
        if search_kw:
            df_filtered = df_filtered[
                df_filtered["full_name"].str.contains(
                    search_kw, case=False, na=False
                )
                | df_filtered["phone_num"].str.contains(
                    search_kw, case=False, na=False
                )
            ]
        if filter_tier != "Tất cả":
            df_filtered = df_filtered[
                df_filtered["priority_tier"] == filter_tier
            ]
        if filter_stage != "Tất cả":
            df_filtered = df_filtered[
                df_filtered["sales_stage"] == filter_stage
            ]

        view_df = df_filtered[
            [
                "lead_code",
                "full_name",
                "phone_num",
                "segment",
                "main_demand",
                "target_amount",
                "scoring_points",
                "priority_tier",
                "sales_stage",
            ]
        ].copy()
        view_df["target_amount"] = view_df["target_amount"].apply(
            format_currency_vnd
        )
        view_df.columns = [
            "Mã KH",
            "Họ và Tên",
            "SĐT",
            "Phân Hạng",
            "Nhu Cầu Cần Tư Vấn",
            "Giá Trị Dự Kiến",
            "Điểm Số",
            "Ưu Tiên",
            "Trạng Thái",
        ]

        try:
            st.dataframe(view_df, use_container_width=True, hide_index=True)
        except TypeError:
            st.dataframe(view_df)

        st.divider()
        st.markdown("#### 🔄 Cập nhật tiến trình & Thao tác chi tiết")

        selected_names = df_filtered["full_name"].tolist()
        if selected_names:
            target_name = st.selectbox("Chọn khách hàng thao tác", selected_names)
            curr_row = df_filtered[
                df_filtered["full_name"] == target_name
            ].iloc[0]

            col_detail1, col_detail2 = st.columns([2, 1])

            with col_detail1:
                st.write(f"**Mã hồ sơ:** {curr_row['lead_code']}")
                st.write(
                    f"**Thu nhập khai báo:** {format_currency_vnd(curr_row['monthly_income'])} / tháng"
                )
                st.write(
                    f"**Điểm tín dụng CIS:** {curr_row['credit_score_cis']} pt"
                )
                st.write(f"**Chuyên viên phụ trách:** {curr_row['assigned_officer']}")
                st.write(f"**Ghi chú tư vấn:** {curr_row['notes']}")

                recs = recommend_acb_products(
                    curr_row["main_demand"],
                    curr_row["monthly_income"],
                    curr_row["target_amount"],
                )
                st.success(
                    "**💡 Sản phẩm ACB khuyên dùng cho KH này:**\n"
                    + "\n".join([f"- {item}" for item in recs])
                )

            with col_detail2:
                stages_list = [
                    "1. Mới ghi nhận",
                    "2. Đã liên hệ lần 1",
                    "3. Đang lập hồ sơ",
                    "4. Đang thẩm định",
                    "5. Chốt thành công",
                    "6. Thất bại / Huỷ",
                ]
                idx = (
                    stages_list.index(curr_row["sales_stage"])
                    if curr_row["sales_stage"] in stages_list
                    else 0
                )
                new_stg = st.selectbox("Chuyển trạng thái tư vấn", stages_list, index=idx)

                if st.button("💾 Cập nhật Trạng thái"):
                    update_lead_stage(int(curr_row["id"]), new_stg)
                    st.toast("Đã cập nhật giai đoạn tư vấn mới!")
                    st.rerun()

                if st.button("🗑️ Xoá hồ sơ khỏi hệ thống"):
                    remove_lead(int(curr_row["id"]))
                    st.toast("Đã xoá hồ sơ khách hàng.")
                    st.rerun()

# --- MỤC 4: TIẾN TRÌNH XỬ LÝ (KANBAN) ---
elif nav_choice == "🔀 Tiến trình xử lý (Kanban)":
    st.markdown("### 🔀 Bảng Tiến trình Kinh doanh (Sales Pipeline Kanban)")

    if df_data.empty:
        st.info("Chưa có thông tin để hiển thị Kanban.")
    else:
        stages = [
            "1. Mới ghi nhận",
            "2. Đã liên hệ lần 1",
            "3. Đang lập hồ sơ",
            "4. Đang thẩm định",
            "5. Chốt thành công",
        ]
        cols = st.columns(5)

        for col, stg in zip(cols, stages):
            sub_df = df_data[df_data["sales_stage"] == stg]
            with col:
                st.markdown(
                    f"""
                    <div style="background:#e2e8f0; padding:8px; border-radius:6px; text-align:center; font-weight:700; color:#0d2c54; font-size:13px;">
                        {stg}<br><span style="font-size:18px; color:#1e50a2;">({len(sub_df)})</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.write("")
                for _, r in sub_df.iterrows():
                    st.markdown(
                        f"""
                        <div style="background:white; padding:10px; border-radius:6px; border:1px solid #cbd5e1; margin-bottom:8px; font-size:12px;">
                            <b>👤 {r['full_name']}</b><br>
                            🎯 {r['main_demand']}<br>
                            💵 {format_currency_vnd(r['target_amount'])}<br>
                            <span style="color:#0284c7; font-weight:700;">Điểm: {r['scoring_points']}/100</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# --- MỤC 5: CÔNG CỤ TÍNH NHANH KHOẢN VAY ---
elif nav_choice == "🧮 Công cụ tính nhanh Khoản vay":
    st.markdown("### 🧮 Công cụ Tính toán Khoản vay & Tiết kiệm ACB")
    st.caption(
        "Hỗ trợ Chuyên viên Tư vấn (RM) tính toán nhanh số tiền trả hàng tháng cho khách hàng."
    )

    t1, t2 = st.tabs(["📉 Lịch trả nợ khoản vay", "📈 Lợi tức gửi tiết kiệm"])

    with t1:
        c_loan1, c_loan2 = st.columns(2)
        with c_loan1:
            loan_amount = st.number_input(
                "Số tiền vay dự kiến (Triệu VNĐ)",
                value=1000.0,
                step=50.0,
            )
            loan_tenure_months = st.number_input(
                "Thời hạn vay (Tháng)", value=120, step=12
            )
        with c_loan2:
            interest_rate_year = st.number_input(
                "Lãi suất vay (%/năm)", value=7.5, step=0.1
            )
            pay_method = st.selectbox(
                "Phương thức trả nợ",
                ["Dư nợ giảm dần (Gốc đều)", "Dư nợ ban đầu (Cố định)"],
            )

        if st.button("📊 TÍNH LỊCH TRẢ NỢ"):
            principal_val = loan_amount * 1_000_000
            monthly_rate = (interest_rate_year / 100) / 12

            if pay_method == "Dư nợ giảm dần (Gốc đều)":
                monthly_principal = principal_val / loan_tenure_months
                first_month_interest = principal_val * monthly_rate
                total_first_month = monthly_principal + first_month_interest

                st.success(
                    f"👉 **Tháng đầu tiên trả:** ~ **{int(total_first_month):,} VNĐ** "
                    f"(Gốc: {int(monthly_principal):,} VNĐ + Lãi: {int(first_month_interest):,} VNĐ)"
                )
                st.info(
                    "📉 Các tháng tiếp theo tiền lãi sẽ giảm dần theo dư nợ thực tế."
                )
            else:
                monthly_interest = principal_val * monthly_rate
                monthly_principal = principal_val / loan_tenure_months
                fixed_pay = monthly_principal + monthly_interest
                st.success(
                    f"👉 **Số tiền cố định trả hàng tháng:** ~ **{int(fixed_pay):,} VNĐ**"
                )

    with t2:
        c_sav1, c_sav2 = st.columns(2)
        with c_sav1:
            sav_amount = st.number_input(
                "Số tiền gửi (Triệu VNĐ)", value=500.0, step=50.0
            )
            sav_months = st.number_input(
                "Kỳ hạn gửi (Tháng)", value=12, step=1
            )
        with c_sav2:
            sav_rate = st.number_input(
                "Lãi suất tiết kiệm (%/năm)", value=5.2, step=0.1
            )

        if st.button("💰 TÍNH LÃI DỰ KIẾN"):
            sav_val = sav_amount * 1_000_000
            total_sav_interest = sav_val * (sav_rate / 100) * (sav_months / 12)
            st.success(
                f"🎉 **Tổng tiền lãi nhận được cuối kỳ:** ~ **{int(total_sav_interest):,} VNĐ**"
            )

# --- MỤC 6: BÁO CÁO TĂNG TRƯỞNG ---
elif nav_choice == "📊 Báo cáo tăng trưởng":
    st.markdown("### 📊 Phân tích & Báo cáo Tăng trưởng Lead ACB")

    if df_data.empty:
        st.info("Chưa có dữ liệu phân tích.")
    else:
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("#### 🎯 Cơ cấu Phân hạng Ưu tiên")
            tier_counts = df_data["priority_tier"].value_counts()
            st.bar_chart(tier_counts)

        with col_g2:
            st.markdown("#### 💳 Cơ cấu Nhu cầu Sản phẩm")
            demand_counts = df_data["main_demand"].value_counts()
            st.bar_chart(demand_counts)

        st.divider()

        sum_value = 0.0
        for val in df_data["target_amount"]:
            if pd.notna(val) and val is not None:
                v = float(val)
                sum_value += v * 1_000_000 if v < 1000000 else v

        st.metric(
            "💰 Tổng giá trị nhu cầu đang quản lý",
            f"{int(sum_value):,}".replace(",", ".") + " VNĐ",
        )

# =========================================================
# 7. XUẤT BÁO CÁO EXCEL (SIDEBAR)
# =========================================================

st.sidebar.divider()
if not df_data.empty:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_data.to_excel(writer, index=False, sheet_name="ACB_Leads_Report")

    st.sidebar.download_button(
        label="📥 Xuất Báo cáo Excel ACB",
        data=buffer.getvalue(),
        file_name="ACB_Smart_Leads_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
