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

st.title("💼 HR Payroll (PAYE) Calculator")

# Sidebar settings
st.sidebar.header("⚙️ Settings")

pension_rate = st.sidebar.number_input("Pension Rate (%)", value=8.0) / 100
nhf_rate = st.sidebar.number_input("NHF Rate (%)", value=2.5) / 100

st.sidebar.markdown("### Tax Bands")

band1_limit = st.sidebar.number_input("Band 1 Limit", value=800000.0)
band1_rate = st.sidebar.number_input("Band 1 Rate (%)", value=0.0) / 100

band2_limit = st.sidebar.number_input("Band 2 Limit", value=2200000.0)
band2_rate = st.sidebar.number_input("Band 2 Rate (%)", value=15.0) / 100

band3_rate = st.sidebar.number_input("Band 3 Rate (%)", value=18.0) / 100


# PAYE Calculation
def calculate_paye(monthly_salary):
    annual_salary = monthly_salary * 12
    pension = annual_salary * pension_rate
    nhf = annual_salary * nhf_rate
    taxable_income = annual_salary - (pension + nhf)

    layer1 = min(band1_limit, taxable_income) * band1_rate
    layer2 = min(band2_limit, max(0, taxable_income - band1_limit)) * band2_rate
    layer3 = max(0, taxable_income - (band1_limit + band2_limit)) * band3_rate

    total_tax = layer1 + layer2 + layer3
    monthly_tax = total_tax / 12

    return {
        "Annual Salary": annual_salary,
        "Pension": pension,
        "NHF": nhf,
        "Taxable Income": taxable_income,
        "Annual Tax": total_tax,
        "Monthly Tax": monthly_tax
    }


# ✅ FIXED PDF GENERATOR
def generate_pdf(name, result, logo.png):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    # ✅ LOGO HANDLING (SAFE)
    logo = None

    # Priority 1: local logo.png
    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=120, height=60)

    # Add logo if available
    if logo:
        elements.append(logo)
        elements.append(Spacer(1, 10))

    # Title
    elements.append(Paragraph("Employee Payslip", styles["Title"]))
    elements.append(Spacer(1, 15))

    # Employee name
    elements.append(Paragraph(f"<b>Employee Name:</b> {name}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    # ✅ TABULAR PAYSLIP
    data = [
        ["Description", "Amount (₦)"],
        ["Annual Salary", f"{result['Annual Salary']:,.2f}"],
        ["Pension", f"{result['Pension']:,.2f}"],
        ["NHF", f"{result['NHF']:,.2f}"],
        ["Taxable Income", f"{result['Taxable Income']:,.2f}"],
        ["Annual Tax", f"{result['Annual Tax']:,.2f}"],
        ["Monthly PAYE", f"{result['Monthly Tax']:,.2f}"],
    ]

    table = Table(data, colWidths=[260, 180])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

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
            result = calculate_paye(monthly_salary)

            if not name:
                name = "Employee"

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Name:** {name}")
                st.write(f"Annual Salary: ₦{result['Annual Salary']:,.2f}")
                st.write(f"Pension: ₦{result['Pension']:,.2f}")
                st.write(f"NHF: ₦{result['NHF']:,.2f}")

            with col2:
                st.write(f"Taxable Income: ₦{result['Taxable Income']:,.2f}")
                st.success(f"Annual Tax: ₦{result['Annual Tax']:,.2f}")
                st.success(f"Monthly PAYE: ₦{result['Monthly Tax']:,.2f}")

            pdf = generate_pdf(name, result, logo_file)

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
    st.markdown("Upload a CSV with columns: **Name, MonthlySalary**")

    file = st.file_uploader("Upload CSV", type=["csv"])

    if file:
        df = pd.read_csv(file)

        if "MonthlySalary" not in df.columns:
            st.error("CSV must contain 'MonthlySalary' column")
        else:
            results = []

            for i, row in df.iterrows():
                res = calculate_paye(row["MonthlySalary"])

                results.append({
                    "Name": row.get("Name", ""),
                    "Monthly Salary": row["MonthlySalary"],
                    "Annual Salary": res["Annual Salary"],
                    "Pension": res["Pension"],
                    "NHF": res["NHF"],
                    "Taxable Income": res["Taxable Income"],
                    "Annual Tax": res["Annual Tax"],
                    "Monthly PAYE": res["Monthly Tax"]
                })

            result_df = pd.DataFrame(results)

            st.markdown("## 📊 Payroll Results")
            st.dataframe(result_df, use_container_width=True)

            csv = result_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="⬇️ Download Results",
                data=csv,
                file_name="payroll_results.csv",
                mime="text/csv",
                key="download_csv"
    )
