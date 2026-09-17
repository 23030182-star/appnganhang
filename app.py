import streamlit as st
from datetime import date, timedelta
from calendar import monthrange

# =========================================================
# CẤU HÌNH
# =========================================================
st.set_page_config(
    page_title="Tính lãi tiền gửi tiết kiệm",
    page_icon="💰",
    layout="wide"
)

st.title("💰 TÍNH LÃI TIỀN GỬI TIẾT KIỆM")
st.caption("Tính theo ngày gửi → trước ngày đến hạn/rút tiền 1 ngày. Rút trước hạn áp dụng lãi suất không kỳ hạn.")

# =========================================================
# HÀM HỖ TRỢ
# =========================================================
def add_months(d, months):
    """Cộng số tháng, giữ ngày nếu có thể; nếu không lấy ngày cuối tháng."""
    total = d.year * 12 + (d.month - 1) + months
    year = total // 12
    month = total % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def days_between(start, end):
    """Số ngày tính lãi: từ start đến trước end."""
    return max(0, (end - start).days)


def interest_by_days(principal, annual_rate_percent, days):
    """
    Lãi đơn theo số ngày/365.
    Ví dụ: 100 triệu, 6%/năm, 30 ngày
    = 100tr * 6% * 30/365.
    """
    return principal * (annual_rate_percent / 100) * days / 365


def calculate_maturity(principal, term_months, start_date):
    return add_months(start_date, term_months)


def calculate_full_cycles(
    principal,
    start_date,
    withdrawal_date,
    term_months,
    term_rate,
    non_term_rate
):
    """
    Tính theo từng kỳ hạn.

    Nếu khách hàng không rút khi đến hạn:
    - Tự động gia hạn đúng kỳ hạn.
    - Phần gốc sau mỗi kỳ được cộng thêm lãi nếu nhận lãi cuối kỳ.

    Với nhận lãi trước / hàng kỳ, phần lãi đã trả không nhập vào gốc.
    Hàm này dùng cho trường hợp nhận lãi cuối kỳ.
    """
    current_start = start_date
    current_principal = principal
    cycles = []

    while True:
        maturity = calculate_maturity(current_start, term_months, current_start)
        period_end = min(maturity, withdrawal_date)

        # Tính lãi đến trước ngày maturity/withdrawal
        days = days_between(current_start, period_end)

        if withdrawal_date < maturity:
            # Rút trước hạn: lãi không kỳ hạn
            interest = interest_by_days(
                current_principal, non_term_rate, days
            )
            cycles.append({
                "start": current_start,
                "end": withdrawal_date,
                "maturity": maturity,
                "days": days,
                "principal": current_principal,
                "rate": non_term_rate,
                "interest": interest,
                "early": True
            })
            break

        # Đến hạn
        interest = interest_by_days(
            current_principal, term_rate, days
        )

        cycles.append({
            "start": current_start,
            "end": maturity,
            "maturity": maturity,
            "days": days,
            "principal": current_principal,
            "rate": term_rate,
            "interest": interest,
            "early": False
        })

        # Nếu ngày rút đúng ngày đáo hạn, kết thúc.
        if withdrawal_date == maturity:
            break

        # Không rút -> tự động gia hạn.
        current_principal += interest
        current_start = maturity

    return cycles


def calculate_periods(principal, start_date, withdrawal_date, term_months):
    """
    Chia toàn bộ thời gian thành các kỳ hạn.
    Dùng cho nhận lãi trước và nhận lãi hàng kỳ.
    """
    periods = []
    current_start = start_date

    while current_start < withdrawal_date:
        maturity = calculate_maturity(current_start, term_months, current_start)
        period_end = min(maturity, withdrawal_date)
        days = days_between(current_start, period_end)

        periods.append({
            "start": current_start,
            "end": period_end,
            "maturity": maturity,
            "days": days,
            "is_full_term": withdrawal_date >= maturity
        })

        if withdrawal_date <= maturity:
            break

        current_start = maturity

    return periods


# =========================================================
# NHẬP THÔNG TIN
# =========================================================
st.subheader("1. Thông tin khoản tiền gửi")

col1, col2 = st.columns(2)

with col1:
    principal = st.number_input(
        "Số tiền khách hàng gửi (VNĐ)",
        min_value=0,
        value=100_000_000,
        step=1_000_000,
        format="%d"
    )

    term_rate = st.number_input(
        "Lãi suất có kỳ hạn (%/năm)",
        min_value=0.0,
        value=6.0,
        step=0.01,
        format="%.2f"
    )

    non_term_rate = st.number_input(
        "Lãi suất không kỳ hạn (%/năm)",
        min_value=0.0,
        value=0.1,
        step=0.01,
        format="%.2f"
    )

with col2:
    deposit_date = st.date_input(
        "Ngày gửi tiền",
        value=date.today()
    )

    withdrawal_date = st.date_input(
        "Ngày khách hàng rút tiền",
        value=date.today()
    )

    term_months = st.selectbox(
        "Kỳ hạn gửi tiền",
        options=[1, 2, 3, 6, 9, 12, 18, 24, 36],
        index=5,
        format_func=lambda x: f"{x} tháng"
    )

st.subheader("2. Cách nhận tiền lãi")

interest_method = st.radio(
    "Chọn phương thức nhận lãi",
    options=[
        "Nhận lãi trước",
        "Nhận lãi hàng kỳ (hàng tháng)",
        "Nhận lãi cuối kỳ"
    ],
    horizontal=True
)

st.info(
    "Quy ước: 1 năm = 365 ngày. Lãi được tính theo công thức "
    "Tiền lãi = Tiền gốc × Lãi suất năm × Số ngày / 365. "
    "Ngày rút tiền/đáo hạn không tính lãi."
)

# =========================================================
# TÍNH TOÁN
# =========================================================
if st.button("🧮 TÍNH TOÁN", type="primary", use_container_width=True):

    if principal <= 0:
        st.error("Vui lòng nhập số tiền gửi lớn hơn 0.")
        st.stop()

    if withdrawal_date <= deposit_date:
        st.error("Ngày rút tiền phải sau ngày gửi tiền.")
        st.stop()

    # -----------------------------------------------------
    # PHƯƠNG ÁN 1: NHẬN LÃI TRƯỚC
    # -----------------------------------------------------
    if interest_method == "Nhận lãi trước":

        maturity_date = calculate_maturity(
            deposit_date, term_months, deposit_date
        )

        # Nếu rút trước hạn
        if withdrawal_date < maturity_date:
            days = days_between(deposit_date, withdrawal_date)
            interest = interest_by_days(
                principal, non_term_rate, days
            )

            total_received = principal + interest

            st.subheader("📊 KẾT QUẢ")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tiền gốc", f"{principal:,.0f} VNĐ")
            c2.metric("Tiền lãi", f"{interest:,.0f} VNĐ")
            c3.metric("Tổng nhận", f"{total_received:,.0f} VNĐ")
            c4.metric("Số ngày tính lãi", f"{days} ngày")

            st.warning(
                "Khách hàng rút trước hạn nên toàn bộ thời gian thực tế "
                "được áp dụng lãi suất không kỳ hạn."
            )

        else:
            # Lãi trước cho từng kỳ hạn.
            # Lãi kỳ tiếp theo được tính trên GỐC ban đầu.
            periods = calculate_periods(
                principal,
                deposit_date,
                withdrawal_date,
                term_months
            )

            total_interest_paid = 0
            total_principal_received = 0
            current_principal = principal
            detail = []

            for p in periods:
                if p["is_full_term"]:
                    rate = term_rate
                else:
                    rate = non_term_rate

                interest = interest_by_days(
                    current_principal,
                    rate,
                    p["days"]
                )

                # Nếu là kỳ đầy đủ và nhận lãi trước,
                # lãi được trả ngay đầu kỳ.
                # Nếu kỳ cuối rút trước hạn, tính theo không kỳ hạn.
                total_interest_paid += interest

                detail.append({
                    "Từ ngày": p["start"].strftime("%d/%m/%Y"),
                    "Đến trước ngày": p["end"].strftime("%d/%m/%Y"),
                    "Số ngày": p["days"],
                    "Lãi suất (%/năm)": rate,
                    "Tiền gốc": current_principal,
                    "Tiền lãi": interest,
                    "Loại": "Đủ kỳ hạn" if p["is_full_term"] else "Rút trước hạn"
                })

            # Khi nhận lãi trước, tiền gốc khi rút vẫn là gốc ban đầu.
            total_principal_received = principal
            total_received = total_principal_received

            st.subheader("📊 KẾT QUẢ")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tiền gốc nhận", f"{total_principal_received:,.0f} VNĐ")
            c2.metric("Tổng lãi đã nhận", f"{total_interest_paid:,.0f} VNĐ")
            c3.metric("Gốc + lãi", f"{total_principal_received + total_interest_paid:,.0f} VNĐ")
            c4.metric("Số kỳ", f"{len(periods)}")

            st.write(
                "💡 Với phương thức **nhận lãi trước**, tiền lãi được trả trước "
                "theo từng kỳ. Khi khách hàng rút tiền, tiền gốc nhận lại "
                "là số tiền gốc ban đầu."
            )

            st.dataframe(detail, use_container_width=True)

    # -----------------------------------------------------
    # PHƯƠNG ÁN 2: NHẬN LÃI HÀNG THÁNG
    # -----------------------------------------------------
    elif interest_method == "Nhận lãi hàng kỳ (hàng tháng)":

        # Nếu rút trước kỳ hạn đầu tiên -> áp dụng không kỳ hạn.
        first_maturity = calculate_maturity(
            deposit_date, term_months, deposit_date
        )

        if withdrawal_date < first_maturity:
            days = days_between(deposit_date, withdrawal_date)
            interest = interest_by_days(
                principal, non_term_rate, days
            )

            total_received = principal + interest

            st.subheader("📊 KẾT QUẢ")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tiền gốc", f"{principal:,.0f} VNĐ")
            c2.metric("Tiền lãi", f"{interest:,.0f} VNĐ")
            c3.metric("Tổng nhận", f"{total_received:,.0f} VNĐ")
            c4.metric("Số ngày", f"{days} ngày")

            st.warning(
                "Rút trước kỳ hạn nên áp dụng lãi suất không kỳ hạn."
            )

        else:
            # Tính từng tháng từ ngày gửi.
            # Lãi hàng tháng được trả ra, KHÔNG nhập vào gốc.
            periods = calculate_periods(
                principal,
                deposit_date,
                withdrawal_date,
                term_months
            )

            total_interest = 0
            detail = []

            for p in periods:
                if p["is_full_term"]:
                    rate = term_rate
                else:
                    rate = non_term_rate

                interest = interest_by_days(
                    principal,
                    rate,
                    p["days"]
                )

                total_interest += interest

                detail.append({
                    "Từ ngày": p["start"].strftime("%d/%m/%Y"),
                    "Đến trước ngày": p["end"].strftime("%d/%m/%Y"),
                    "Số ngày": p["days"],
                    "Lãi suất (%/năm)": rate,
                    "Tiền gốc": principal,
                    "Tiền lãi kỳ này": interest,
                    "Trạng thái": "Đủ kỳ hạn" if p["is_full_term"] else "Rút trước hạn"
                })

            total_received = principal + total_interest

            st.subheader("📊 KẾT QUẢ")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tiền gốc nhận", f"{principal:,.0f} VNĐ")
            c2.metric("Tổng tiền lãi", f"{total_interest:,.0f} VNĐ")
            c3.metric("Tổng nhận", f"{total_received:,.0f} VNĐ")
            c4.metric("Số kỳ", f"{len(periods)}")

            st.write(
                "💡 Với phương thức **nhận lãi hàng kỳ**, tiền lãi của mỗi kỳ "
                "được trả riêng và không cộng vào tiền gốc."
            )

            st.dataframe(detail, use_container_width=True)

    # -----------------------------------------------------
    # PHƯƠNG ÁN 3: NHẬN LÃI CUỐI KỲ
    # -----------------------------------------------------
    else:

        cycles = calculate_full_cycles(
            principal=principal,
            start_date=deposit_date,
            withdrawal_date=withdrawal_date,
            term_months=term_months,
            term_rate=term_rate,
            non_term_rate=non_term_rate
        )

        total_interest = sum(c["interest"] for c in cycles)

        # Nhận lãi cuối kỳ:
        # - Đến hạn không rút -> gốc + lãi nhập vào gốc cho kỳ mới.
        # - Khi cuối cùng rút tiền -> nhận toàn bộ gốc tích lũy + lãi kỳ cuối.
        final_cycle = cycles[-1]

        # Tính giá trị cuối cùng chính xác theo quá trình nhập lãi.
        final_amount = final_cycle["principal"] + final_cycle["interest"]

        # Nếu có nhiều kỳ, final_amount đã bao gồm lãi các kỳ trước
        # vì principal của mỗi kỳ đã được cộng lãi kỳ trước.
        original_principal = principal
        accumulated_interest = final_amount - original_principal

        st.subheader("📊 KẾT QUẢ")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tiền gốc ban đầu", f"{original_principal:,.0f} VNĐ")
        c2.metric("Tổng tiền lãi", f"{accumulated_interest:,.0f} VNĐ")
        c3.metric("TỔNG KHÁCH HÀNG NHẬN", f"{final_amount:,.0f} VNĐ")
        c4.metric("Số kỳ", f"{len(cycles)}")

        if final_cycle["early"]:
            st.warning(
                "Khách hàng rút trước hạn ở kỳ cuối. Phần thời gian từ "
                f"{final_cycle['start'].strftime('%d/%m/%Y')} đến trước "
                f"{withdrawal_date.strftime('%d/%m/%Y')} được hưởng "
                "lãi suất không kỳ hạn."
            )
        else:
            st.success(
                "Nếu đến hạn khách hàng không rút tiền, khoản tiền được "
                "tự động gia hạn đúng kỳ hạn và lãi được nhập vào gốc "
                "cho kỳ tiếp theo."
            )

        detail = []

        for i, c in enumerate(cycles, start=1):
            detail.append({
                "Kỳ": i,
                "Từ ngày": c["start"].strftime("%d/%m/%Y"),
                "Đến trước ngày": c["end"].strftime("%d/%m/%Y"),
                "Số ngày": c["days"],
                "Tiền gốc đầu kỳ": c["principal"],
                "Lãi suất (%/năm)": c["rate"],
                "Tiền lãi kỳ này": c["interest"],
                "Trạng thái": (
                    "Rút trước hạn"
                    if c["early"]
                    else "Đến hạn - tự động gia hạn"
                    if i < len(cycles)
                    else "Đến hạn"
                )
            })

        st.dataframe(detail, use_container_width=True)

        st.write(
            f"**Công thức kỳ cuối:** "
            f"{final_cycle['principal']:,.0f} × "
            f"{final_cycle['rate']:.2f}% × "
            f"{final_cycle['days']} / 365 = "
            f"{final_cycle['interest']:,.0f} VNĐ tiền lãi."
        )

# =========================================================
# GHI CHÚ
# =========================================================
st.divider()
st.caption(
    "Lưu ý nghiệp vụ: Đây là công cụ mô phỏng. Công thức thực tế của ngân hàng "
    "có thể khác về quy ước ngày tính lãi, số ngày trong năm, cách xử lý ngày "
    "đáo hạn, lãi suất rút trước hạn, thuế/phí và quy định từng sản phẩm tiền gửi."
)
