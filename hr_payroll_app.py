import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO
import os

# Page config
st.set_page_config(page_title="HR Payroll Tool", layout="wide")

st.title("💼 HR Payroll Calculator")

# Sidebar settings
st.sidebar.header("⚙️ Statutory Rates")

paye_rate = st.sidebar.number_input("PAYE (%)", value=10.0) / 100
nhia_rate = st.sidebar.number_input("NHIA (%)", value=5.0) / 100
itf_rate = st.sidebar.number_input("ITF (%)", value=1.0) / 100
nsitf_rate = st.sidebar.number_input("NSITF (%)", value=1.0) / 100
pension_rate = st.sidebar.number_input("Pension (%)", value=8.0) / 100
nhf_rate = st.sidebar.number_input("NHF (%)", value=2.5) / 100


# PAYROLL CALCULATION
def calculate_payroll(monthly_salary):
    annual_salary = monthly_salary * 12

    pension = annual_salary * pension_rate
    nhf = annual_salary * nhf_rate
    nhia = annual_salary * nhia_rate
    itf = annual_salary * itf_rate
    nsitf = annual_salary * nsitf_rate

    paye = annual_salary * paye_rate

    total_deductions = pension + nhf + nhia + itf + nsitf + paye
    net_annual = annual_salary - total_deductions
    net_monthly = net_annual / 12

    return {
        "Annual Salary": annual_salary,
        "Pension": pension,
        "NHF": nhf,
        "NHIA": nhia,
        "ITF": itf,
        "NSITF": nsitf,
        "PAYE": paye,
        "Total Deductions": total_deductions,
        "Net Annual Salary": net_annual,
        "Net Monthly Salary": net_monthly
    }


# PDF GENERATOR
def generate_pdf(name, result):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    # Logo
    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=60, height=60)
        elements.append(logo)
        elements.append(Spacer(1, 10))

    elements.append(Paragraph("Employee Payslip", styles["Title"]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph(f"<b>Employee Name:</b> {name}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    # Table
    data = [
        ["Description", "Amount (₦)"],
        ["Annual Salary", f"{result['Annual Salary']:,.2f}"],
        ["Pension", f"{result['Pension']:,.2f}"],
        ["NHF", f"{result['NHF']:,.2f}"],
        ["NHIA", f"{result['NHIA']:,.2f}"],
        ["ITF", f"{result['ITF']:,.2f}"],
        ["NSITF", f"{result['NSITF']:,.2f}"],
        ["PAYE", f"{result['PAYE']:,.2f}"],
        ["Total Deductions", f"{result['Total Deductions']:,.2f}"],
        ["Net Annual Salary", f"{result['Net Annual Salary']:,.2f}"],
        ["Net Monthly Salary", f"{result['Net Monthly Salary']:,.2f}"],
    ]

    table = Table(data, colWidths=[260, 180])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# Tabs
tab1, tab2 = st.tabs(["👤 Single Employee", "📂 Bulk Upload"])


# SINGLE EMPLOYEE
with tab1:
    st.subheader("Employee Input")

    name = st.text_input("Employee Name")
    monthly_salary = st.number_input("Monthly Salary (₦)", min_value=0.0, step=1000.0)

    if st.button("Calculate", key="calc_single"):
        if monthly_salary <= 0:
            st.warning("Enter a valid salary")
        else:
            result = calculate_payroll(monthly_salary)

            if not name:
                name = "Employee"

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Name:** {name}")
                st.write(f"Annual Salary: ₦{result['Annual Salary']:,.2f}")
                st.write(f"Pension: ₦{result['Pension']:,.2f}")
                st.write(f"NHF: ₦{result['NHF']:,.2f}")
                st.write(f"NHIA: ₦{result['NHIA']:,.2f}")

            with col2:
                st.write(f"ITF: ₦{result['ITF']:,.2f}")
                st.write(f"NSITF: ₦{result['NSITF']:,.2f}")
                st.write(f"PAYE: ₦{result['PAYE']:,.2f}")
                st.error(f"Total Deductions: ₦{result['Total Deductions']:,.2f}")
                st.success(f"Net Monthly Salary: ₦{result['Net Monthly Salary']:,.2f}")

            pdf = generate_pdf(name, result)

            st.download_button(
                label="⬇️ Download Payslip (PDF)",
                data=pdf,
                file_name=f"{name}_payslip.pdf",
                mime="application/pdf",
                key="download_pdf"
            )


# BULK UPLOAD
with tab2:
    st.subheader("Upload Employee Data")
    st.markdown("Upload CSV with columns: **Name, MonthlySalary**")

    file = st.file_uploader("Upload CSV", type=["csv"])

    if file:
        df = pd.read_csv(file)

        if "MonthlySalary" not in df.columns:
            st.error("CSV must contain 'MonthlySalary'")
        else:
            results = []

            for _, row in df.iterrows():
                res = calculate_payroll(row["MonthlySalary"])

                results.append({
                    "Name": row.get("Name", ""),
                    "Monthly Salary": row["MonthlySalary"],
                    "Net Monthly Salary": res["Net Monthly Salary"],
                    "Total Deductions": res["Total Deductions"]
                })

            result_df = pd.DataFrame(results)

            st.dataframe(result_df, use_container_width=True)

            csv = result_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="⬇️ Download Results",
                data=csv,
                file_name="payroll_results.csv",
                mime="text/csv",
                key="download_csv"
        )
