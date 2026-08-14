import streamlit as st
import pandas as pd
from io import BytesIO


# ==========================================
# CẤU HÌNH
# ==========================================

st.set_page_config(
    page_title="Quản lý khách hàng",
    page_icon="👤",
    layout="wide"
)


# ==========================================
# KHỞI TẠO DANH SÁCH KHÁCH HÀNG
# ==========================================

if "customers" not in st.session_state:
    st.session_state.customers = []


# ==========================================
# HÀM XUẤT EXCEL
# ==========================================

def export_excel():

    df = pd.DataFrame(
        st.session_state.customers
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Khách hàng"
        )

    return output.getvalue()


# ==========================================
# MENU
# ==========================================

st.sidebar.title("📋 MENU")

page = st.sidebar.radio(
    "Chọn trang",
    [
        "👤 Nhập khách hàng",
        "🔐 Admin"
    ]
)


# ==========================================
# TRANG NHẬP KHÁCH HÀNG
# ==========================================

if page == "👤 Nhập khách hàng":

    st.title("👤 THÔNG TIN KHÁCH HÀNG")

    st.write(
        "Vui lòng nhập thông tin khách hàng."
    )

    st.divider()


    # --------------------------------------
    # NHẬP THÔNG TIN
    # --------------------------------------

    phone = st.text_input(
        "📱 Số điện thoại",
        placeholder="Nhập số điện thoại"
    )

    name = st.text_input(
        "👤 Tên khách hàng",
        placeholder="Nhập tên khách hàng"
    )

    address = st.text_input(
        "📍 Địa chỉ",
        placeholder="Nhập địa chỉ"
    )

    note = st.text_area(
        "📝 Ghi chú",
        placeholder="Nhập ghi chú"
    )


    st.divider()


    # --------------------------------------
    # NÚT LƯU
    # --------------------------------------

    if st.button(
        "💾 LƯU THÔNG TIN",
        type="primary",
        use_container_width=True
    ):

        if phone.strip() == "":

            st.error(
                "❌ Vui lòng nhập số điện thoại."
            )

        elif name.strip() == "":

            st.error(
                "❌ Vui lòng nhập tên khách hàng."
            )

        else:

            # Tạo khách hàng mới

            customer = {
                "Số điện thoại": phone.strip(),
                "Tên khách hàng": name.strip(),
                "Địa chỉ": address.strip(),
                "Ghi chú": note.strip()
            }


            # Lưu vào session

            st.session_state.customers.append(
                customer
            )


            st.success(
                "✅ Đã lưu thông tin khách hàng!"
          )


# ==========================================
# TRANG ADMIN
# ==========================================

elif page == "🔐 Admin":

    st.title("🔐 ADMIN")

    st.divider()


    # ======================================
    # ĐĂNG NHẬP
    # ======================================

    if "admin_logged_in" not in st.session_state:

        st.session_state.admin_logged_in = False


    if not st.session_state.admin_logged_in:

        password = st.text_input(
            "🔑 Mật khẩu",
            type="password"
        )


        if st.button(
            "ĐĂNG NHẬP",
            type="primary"
        ):

            if password == "123456":

                st.session_state.admin_logged_in = True

                st.rerun()

            else:

                st.error(
                    "❌ Sai mật khẩu."
                )


    # ======================================
    # ADMIN ĐÃ ĐĂNG NHẬP
    # ======================================

    else:

        col1, col2 = st.columns(
            [5, 1]
        )


        with col1:

            st.subheader(
                "📊 DANH SÁCH KHÁCH HÀNG"
            )


        with col2:

            if st.button("🚪 Đăng xuất"):

                st.session_state.admin_logged_in = False

                st.rerun()


        st.divider()


        # ==================================
        # KIỂM TRA DỮ LIỆU
        # ==================================

        if len(st.session_state.customers) == 0:

            st.info(
                "📭 Chưa có khách hàng."
            )


        else:

            # ==============================
            # CHUYỂN SANG DATAFRAME
            # ==============================

            df = pd.DataFrame(
                st.session_state.customers
            )


            # ==============================
            # TỔNG KHÁCH HÀNG
            # ==============================

            st.metric(
                "👥 Tổng số khách hàng",
                len(df)
            )


            st.divider()


            # ==============================
            # HIỂN THỊ DANH SÁCH
            # ==============================

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )


            st.divider()


            # ==============================
            # XUẤT EXCEL
            # ==============================

            excel_file = export_excel()


            st.download_button(
                label="📥 XUẤT FILE EXCEL",
                data=excel_file,
                file_name="danh_sach_khach_hang.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True
            )
