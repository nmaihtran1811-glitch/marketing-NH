from datetime import date, datetime
from io import BytesIO
import os
import sqlite3
import pandas as pd
import streamlit as st

# =========================================================
# 1. CẤU HÌNH TRANG STREAMLIT
# =========================================================

st.set_page_config(
    page_title="ACB Lead Manager - Nhóm 5",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. GIAO DIỆN (ACB BRANDING: BLUE & TEAL THEME)
# =========================================================

st.markdown(
    """
<style>
/* Background tổng thể */
.main {
    background-color: #f0f4f8;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

/* Thanh Menu bên trái (ACB Blue Gradient) */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #003B7A 0%, #00224A 100%);
}

[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* Header chính phong cách ACB */
.acb-header {
    background: linear-gradient(135deg, #004B93 0%, #0088CC 100%);
    padding: 24px 30px;
    border-radius: 16px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 10px 20px rgba(0, 75, 147, 0.15);
}

.acb-header h1 {
    margin: 0;
    font-size: 30px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.acb-header p {
    margin-top: 6px;
    opacity: 0.9;
    font-size: 15px;
}

/* Thiết kế Thẻ Khách Hàng (Custom Cards) */
.acb-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid #e1e8ed;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    transition: all 0.2s ease-in-out;
}

.acb-card:hover {
    box-shadow: 0 6px 16px rgba(0, 75, 147, 0.1);
    border-color: #0088CC;
}

/* Thẻ ưu tiên phân loại */
.border-hot { border-left: 6px solid #e63946 !important; }
.border-warm { border-left: 6px solid #f4a261 !important; }
.border-cold { border-left: 6px solid #457b9d !important; }

/* Nhãn Trạng Thái (Badges) */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
}
.badge-hot { background-color: #ffe5e5; color: #d62828; }
.badge-warm { background-color: #fff3e0; color: #e65100; }
.badge-cold { background-color: #e1f5fe; color: #0288d1; }

/* Chỉ số Thống kê Metric Box */
.stat-box {
    background: white;
    padding: 18px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #e2e8f0;
}
.stat-number {
    font-size: 26px;
    font-weight: 800;
    color: #004B93;
}
.stat-label {
    font-size: 13px;
    color: #64748b;
    margin-bottom: 4px;
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# 3. KẾT NỐI CƠ SỞ DỮ LIỆU SQLITE (ACB CRM DB)
# =========================================================

DB_NAME = "acb_crm.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acb_customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_code TEXT,
            created_at TEXT,
            name TEXT,
            phone TEXT,
            email TEXT,
            gender TEXT,
            age INTEGER,
            occupation TEXT,
            income REAL,
            area TEXT,
            product TEXT,
            expected_amount REAL,
            need_time TEXT,
            score INTEGER,
            classification TEXT,
            status TEXT,
            employee TEXT,
            note TEXT
        )
    """)

    conn.commit()
    conn.close()


init_database()


# =========================================================
# 4. HÀM BỔ TRỢ XỬ LÝ & TRUY XUẤT DỮ LIỆU
# =========================================================


def format_currency_vnd(amount):
    """Quy đổi tự động đơn vị tiền tệ chuẩn VNĐ"""
    if pd.isna(amount) or amount is None:
        return "0 VNĐ"

    try:
        val = float(amount)
        if val < 1000000:
            val = val * 1_000_000
        return f"{int(val):,}".replace(",", ".") + " VNĐ"
    except ValueError:
        return "0 VNĐ"


def load_customers():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM acb_customers ORDER BY id DESC", conn
    )
    conn.close()
    return df


def add_customer(data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO acb_customers (
            customer_code, created_at, name, phone, email, gender, age, occupation,
            income, area, product, expected_amount, need_time, score, classification,
            status, employee, note
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        tuple(data.values()),
    )

    conn.commit()
    conn.close()


def update_status(customer_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE acb_customers SET status = ? WHERE id = ?",
        (new_status, customer_id),
    )
    conn.commit()
    conn.close()


def delete_customer(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM acb_customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()


# =========================================================
# 5. CHẤM ĐIỂM TIỀM NĂNG LEAD SCORING (CHUẨN ACB)
# =========================================================


def calculate_acb_score(income, product, amount, need_time):
    score = 0

    # 1. Thu nhập hàng tháng (Triệu VNĐ)
    if income >= 60:
        score += 30
    elif income >= 35:
        score += 25
    elif income >= 18:
        score += 18
    else:
        score += 10

    # 2. Sản phẩm chiến lược ACB
    if product in ["Vay mua nhà đất", "Vay sản xuất kinh doanh"]:
        score += 25
    elif product in ["Vay mua ô tô", "Thẻ tín dụng ACB"]:
        score += 20
    elif product == "Tiền gửi tiết kiệm":
        score += 18
    else:
        score += 10

    # 3. Nhu cầu vốn/gửi (Triệu VNĐ)
    if amount >= 2000:
        score += 25
    elif amount >= 1000:
        score += 20
    elif amount >= 500:
        score += 15
    else:
        score += 8

    # 4. Thời gian giải ngân dự kiến
    if need_time == "Ngay lập tức (Dưới 15 ngày)":
        score += 20
    elif need_time == "Trong 1 tháng":
        score += 15
    elif need_time == "1 - 3 tháng":
        score += 10
    else:
        score += 5

    score = min(score, 100)

    if score >= 80:
        classification = "HOT"
    elif score >= 50:
        classification = "WARM"
    else:
        classification = "COLD"

    return score, classification


# =========================================================
# 6. KHỞI TẠO DỮ LIỆU CHÍNH
# =========================================================

df = load_customers()


# =========================================================
# 7. THANH MENU SIDEBAR (ACB LOGO & BRANDING)
# =========================================================

with st.sidebar:
    ACB_LOGO_PATH = "acb_logo.jpg"

    if os.path.exists(ACB_LOGO_PATH):
        st.image(ACB_LOGO_PATH, use_container_width=True)
    else:
        st.markdown(
            """
            <div style="text-align:center; padding: 10px 0px;">
                <h1 style="color:#ffffff; margin:0; font-size:28px; font-weight:800; letter-spacing:1px;">ACB</h1>
                <p style="color:#0088CC; margin:0; font-size:13px; font-weight:600;">Á CHÂU COMMERCIAL BANK</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="text-align:center; margin-top:5px; margin-bottom:15px;">
            <p style="opacity:0.8; font-size:13px; margin:0;">Hệ thống Lead Management</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    menu = st.radio(
        "📂 MENU QUẢN LÝ",
        [
            "📌 Bảng điều khiển",
            "📋 Danh sách Leads",
            "➕ Thêm Lead mới",
            "🔄 Tiến độ xử lý",
            "📈 Báo cáo chỉ số",
        ],
    )

    st.divider()
    st.caption("ACB Lead Manager - Nhóm 5 v3.0\nPhát triển cho Khối KHCN ACB")


# =========================================================
# 8. HEADER CHÍNH
# =========================================================

st.markdown(
    """
    <div class="acb-header">
        <h1>🏦 ACB LEAD MANAGER - NHÓM 5</h1>
        <p>Hệ thống Quản lý & Phân loại Khách hàng Tiềm năng (Personal Banking Leads)</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 9. GIAO DIỆN CÁC MỤC CHỨC NĂNG
# =========================================================

# --- A. BẢNG ĐIỀU KHIỂN (DASHBOARD TỔNG QUAN) ---
if menu == "📌 Bảng điều khiển":
    total = len(df)
    hot = len(df[df["classification"] == "HOT"]) if total else 0
    warm = len(df[df["classification"] == "WARM"]) if total else 0
    cold = len(df[df["classification"] == "COLD"]) if total else 0

    st.subheader("📊 Thống kê lượng Lead hiện tại")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="stat-box"><div class="stat-label">👥 TỔNG KHÁCH HÀNG</div><div class="stat-number">{total}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat-box"><div class="stat-label">🔥 KHÁCH HOT</div><div class="stat-number" style="color:#d62828;">{hot}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat-box"><div class="stat-label">⚡ KHÁCH WARM</div><div class="stat-number" style="color:#e65100;">{warm}</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="stat-box"><div class="stat-label">❄️ KHÁCH COLD</div><div class="stat-number" style="color:#0288d1;">{cold}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.divider()

    # DANH SÁCH KHÁCH HÀNG HOT CẦN XỬ LÝ GẤP
    st.subheader("🔥 Danh sách Lead Ưu tiên (HOT - Điểm cao nhất)")

    if total == 0:
        st.info("Chưa có dữ liệu khách hàng trong hệ thống.")
    else:
        hot_df = (
            df[df["classification"] == "HOT"]
            .sort_values("score", ascending=False)
            .head(4)
        )
        if hot_df.empty:
            st.info("Hiện không có khách hàng thuộc nhóm HOT.")
        else:
            for _, row in hot_df.iterrows():
                st.markdown(
                    f"""
                    <div class="acb-card border-hot">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="margin:0; color:#003B7A;">👤 {row['name']}</h3>
                            <span class="badge badge-hot">HOT LEAD ({row['score']}/100)</span>
                        </div>
                        <p style="margin:8px 0; font-size:14px; color:#475569;">
                            📱 <b>{row['phone']}</b> | 💳 Nhu cầu: <b>{row['product']}</b> ({format_currency_vnd(row['expected_amount'])})
                        </p>
                        <div style="font-size:13px; color:#64748b;">
                            📌 Trạng thái hiện tại: <b>{row['status']}</b> | 👨‍💼 RM phụ trách: <b>{row['employee'] or 'Chưa phân công'}</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# --- B. THÊM KHÁCH HÀNG MỚI ---
elif menu == "➕ Thêm Lead mới":
    st.subheader("➕ Tiếp nhận & Đánh giá Hồ sơ Khách hàng Mới")
    st.caption(
        "Nhập đầy đủ thông tin bên dưới để thuật toán tự động xếp hạng Lead theo tiêu chuẩn ACB."
    )

    with st.form("add_acb_lead_form"):
        st.markdown("##### 👤 1. Thông tin cá nhân")
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("👤 Họ và Tên khách hàng *")
            phone = st.text_input("📱 Số điện thoại *")
        with c2:
            gender = st.selectbox("🚻 Giới tính", ["Nam", "Nữ", "Khác"])
            age = st.number_input("🎂 Độ tuổi", min_value=18, max_value=80, value=30)
        with c3:
            email = st.text_input("📧 Email liên hệ")
            area = st.text_input("📍 Khu vực / Địa chỉ (VD: Quận 1, TP.HCM)")

        st.markdown("##### 💵 2. Thông tin Tài chính & Nhu cầu Sản phẩm")
        c4, c5, c6 = st.columns(3)
        with c4:
            occupation = st.text_input(
                "💼 Nghề nghiệp / Lĩnh vực", value="Kinh doanh tự do"
            )
            income = st.number_input(
                "💰 Thu nhập hàng tháng (Triệu VNĐ)", min_value=0.0, value=25.0
            )
        with c5:
            product = st.selectbox(
                "💳 Sản phẩm ACB quan tâm",
                [
                    "Vay mua nhà đất",
                    "Vay sản xuất kinh doanh",
                    "Vay mua ô tô",
                    "Thẻ tín dụng ACB",
                    "Tiền gửi tiết kiệm",
                    "Tài khoản thanh toán ACB Digi",
                ],
            )
            amount = st.number_input(
                "💵 Nhu cầu vốn / Tiền gửi (Triệu VNĐ)",
                min_value=0.0,
                value=800.0,
                step=50.0,
            )
        with c6:
            need_time = st.selectbox(
                "⏱️ Thời gian dự kiến giải ngân",
                [
                    "Ngay lập tức (Dưới 15 ngày)",
                    "Trong 1 tháng",
                    "1 - 3 tháng",
                    "Trên 3 tháng",
                ],
            )
            employee = st.text_input("👨‍💼 Chuyên viên RM tiếp nhận")

        note = st.text_area("📝 Ghi chú chi tiết thêm")

        submitted = st.form_submit_button(
            "🚀 LƯU VÀ PHÂN LOẠI TỰ ĐỘNG", use_container_width=True
        )

    if submitted:
        if not name.strip():
            st.error("⚠️ Bắt buộc nhập Họ và Tên khách hàng!")
        elif not phone.strip():
            st.error("⚠️ Bắt buộc nhập Số điện thoại!")
        else:
            score, classification = calculate_acb_score(
                income, product, amount, need_time
            )
            code = "ACB" + datetime.now().strftime("%y%m%d%H%M%S")
            created = datetime.now().strftime("%Y-%m-%d %H:%M")

            data = {
                "customer_code": code,
                "created_at": created,
                "name": name,
                "phone": phone,
                "email": email,
                "gender": gender,
                "age": age,
                "occupation": occupation,
                "income": income,
                "area": area,
                "product": product,
                "expected_amount": amount,
                "need_time": need_time,
                "score": score,
                "classification": classification,
                "status": "Mới tiếp nhận",
                "employee": employee,
                "note": note,
            }

            add_customer(data)
            st.success(f"🎉 Đã lưu thành công khách hàng: {name} (Mã: {code})")
            st.info(
                f"📊 Kết quả đánh giá: **{classification}** — Điểm ưu tiên: **{score}/100**"
            )


# --- C. QUẢN LÝ DANH SÁCH LEADS ---
elif menu == "📋 Danh sách Leads":
    st.subheader("📋 Quản lý & Tra cứu Hồ sơ Khách hàng")

    df = load_customers()

    if df.empty:
        st.info("Chưa có dữ liệu.")
    else:
        # Bộ lọc
        f1, f2 = st.columns(2)
        with f1:
            kw = st.text_input(
                "🔍 Tìm kiếm nhanh", placeholder="Nhập Tên hoặc Số điện thoại..."
            )
        with f2:
            cls_f = st.selectbox(
                "🏷️ Lọc theo Phân loại Lead", ["Tất cả", "HOT", "WARM", "COLD"]
            )

        filtered = df.copy()
        if kw:
            filtered = filtered[
                filtered["name"].str.contains(kw, case=False, na=False)
                | filtered["phone"].str.contains(kw, case=False, na=False)
            ]
        if cls_f != "Tất cả":
            filtered = filtered[filtered["classification"] == cls_f]

        st.write(f"Tìm thấy **{len(filtered)}** hồ sơ phù hợp:")

        # Bảng dữ liệu chuẩn
        view_df = filtered[
            [
                "customer_code",
                "name",
                "phone",
                "product",
                "expected_amount",
                "score",
                "classification",
                "status",
                "employee",
            ]
        ].copy()

        view_df["expected_amount"] = view_df["expected_amount"].apply(
            format_currency_vnd
        )
        view_df.columns = [
            "Mã Hồ Sơ",
            "Khách Hàng",
            "Điện Thoại",
            "Sản Phẩm",
            "Nhu Cầu",
            "Điểm",
            "Phân Loại",
            "Trạng Thái",
            "RM Phụ Trách",
        ]

        st.dataframe(view_df, use_container_width=True, hide_index=True)

        st.divider()

        # Thao tác cập nhật trạng thái
        st.markdown("##### 🛠️ Cập nhật tiến độ hồ sơ")
        selected_code = st.selectbox(
            "📌 Chọn Mã hồ sơ cần thao tác:", filtered["customer_code"].tolist()
        )

        if selected_code:
            row_data = filtered[
                filtered["customer_code"] == selected_code
            ].iloc[0]

            c_a, c_b = st.columns([2, 1])
            with c_a:
                st.write(f"👤 **Tên KH:** {row_data['name']} | 📱 **SĐT:** {row_data['phone']}")
                st.write(
                    f"💰 **Thu nhập:** {format_currency_vnd(row_data['income'])}/tháng | 📍 **Địa chỉ:** {row_data['area']}"
                )
                st.write(f"📝 **Ghi chú:** {row_data['note']}")

            with c_b:
                current_st = row_data["status"]
                new_st = st.selectbox(
                    "🔄 Đổi trạng thái mới:",
                    [
                        "Mới tiếp nhận",
                        "Đã liên hệ",
                        "Đang tư vấn",
                        "Trình hồ sơ",
                        "Đã giải ngân/Đóng deal",
                    ],
                    index=[
                        "Mới tiếp nhận",
                        "Đã liên hệ",
                        "Đang tư vấn",
                        "Trình hồ sơ",
                        "Đã giải ngân/Đóng deal",
                    ].index(current_st)
                    if current_st
                    in [
                        "Mới tiếp nhận",
                        "Đã liên hệ",
                        "Đang tư vấn",
                        "Trình hồ sơ",
                        "Đã giải ngân/Đóng deal",
                    ]
                    else 0,
                )

                if st.button("💾 Cập nhật ngay", use_container_width=True):
                    update_status(int(row_data["id"]), new_st)
                    st.success("Đã cập nhật trạng thái thành công!")
                    st.rerun()


# --- D. TIẾN ĐỘ XỬ LÝ (KANBAN PIPELINE) ---
elif menu == "🔄 Tiến độ xử lý":
    st.subheader("🔄 Pipeline Chuyển Đổi Hồ Sơ")

    df = load_customers()

    if df.empty:
        st.info("Chưa có dữ liệu.")
    else:
        stages = [
            "Mới tiếp nhận",
            "Đã liên hệ",
            "Đang tư vấn",
            "Trình hồ sơ",
            "Đã giải ngân/Đóng deal",
        ]
        cols = st.columns(5)

        for col, stage in zip(cols, stages):
            stage_df = df[df["status"] == stage]
            with col:
                st.markdown(
                    f"""
                    <div style="background:#e2e8f0; padding:10px; border-radius:8px; text-align:center; font-weight:700; color:#003B7A; font-size:13px;">
                        {stage}<br><span style="font-size:18px; color:#0088CC;">({len(stage_df)})</span>
                    </div>
                    <br>
                    """,
                    unsafe_allow_html=True,
                )

                for _, r in stage_df.head(8).iterrows():
                    border_cls = (
                        "border-hot"
                        if r["classification"] == "HOT"
                        else (
                            "border-warm"
                            if r["classification"] == "WARM"
                            else "border-cold"
                        )
                    )
                    st.markdown(
                        f"""
                        <div class="acb-card {border_cls}" style="padding:12px; margin-bottom:10px;">
                            <b style="font-size:14px; color:#003B7A;">👤 {r['name']}</b><br>
                            <span style="font-size:12px; color:#64748b;">💳 {r['product']}</span><br>
                            <b style="font-size:12px; color:#0088CC;">💵 {format_currency_vnd(r['expected_amount'])}</b>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# --- E. BÁO CÁO CHỈ SỐ (ANALYTICS) ---
elif menu == "📈 Báo cáo chỉ số":
    st.subheader("📈 Phân Tích Dữ Liệu Lead ACB")

    df = load_customers()

    if df.empty:
        st.info("Chưa có dữ liệu để thực hiện báo cáo.")
    else:
        col_x, col_y = st.columns(2)

        with col_x:
            st.markdown("##### 🎯 Cơ cấu Phân loại Leads")
            st.bar_chart(df["classification"].value_counts())

        with col_y:
            st.markdown("##### 💳 Nhu cầu Sản phẩm ACB")
            st.bar_chart(df["product"].value_counts())

        st.divider()

        avg_score = df["score"].mean()
        total_val = sum(
            [
                float(x) * 1_000_000 if float(x) < 1000000 else float(x)
                for x in df["expected_amount"]
                if pd.notna(x)
            ]
        )

        m1, m2 = st.columns(2)
        m1.metric("⭐ Điểm tiềm năng trung bình", f"{avg_score:.1f} / 100")
        m2.metric("💰 Tổng quy mô nhu cầu vốn", format_currency_vnd(total_val))


# =========================================================
# 10. XUẤT BÁO CÁO EXCEL TRÊN SIDEBAR
# =========================================================

st.sidebar.divider()
df_export = load_customers()

if not df_export.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="ACB_Leads")

    st.sidebar.download_button(
        "📥 Xuất Báo Cáo Excel (ACB)",
        data=output.getvalue(),
        file_name="ACB_Lead_Report_Nhom5.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
