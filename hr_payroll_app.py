import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# Page config
st.set_page_config(page_title="HR Payroll Tool", layout="wide")

st.title("💼 HR Payroll (PAYE) Calculator")

# Sidebar (Settings)
st.sidebar.header("⚙️ Settings")

pension_rate = st.sidebar.number_input("Pension Rate (%)", value=8.0) / 100
nhf_rate = st.sidebar.number_input("NHF Rate (%)", value=2.5) / 100

st.sidebar.markdown("### Tax Bands")

band1_limit = st.sidebar.number_input("Band 1 Limit", value=800000.0)
band1_rate = st.sidebar.number_input("Band 1 Rate (%)", value=0.0) / 100

band2_limit = st.sidebar.number_input("Band 2 Limit", value=2200000.0)
band2_rate = st.sidebar.number_input("Band 2 Rate (%)", value=15.0) / 100

band3_rate = st.sidebar.number_input("Band 3 Rate (%)", value=18.0) / 100

# Tax Calculation Function
def calculate_paye(monthly_salary):
    annual_salary = monthly_salary * 12

    pension = annual_salary * pension_rate
    nhf = annual_salary * nhf_rate

    taxable_income = annual_salary - (pension + nhf)

    # Tax bands
    layer1 = min(band1_limit, taxable_income) * band1_rate

    layer2 = min(
        band2_limit,
        max(0, taxable_income - band1_limit)
    ) * band2_rate

    layer3 = max(
        0,
        taxable_income - (band1_limit + band2_limit)
    ) * band3_rate

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

# Tabs
tab1, tab2 = st.tabs(["👤 Single Employee", "📂 Bulk Upload"])

# Single Employee
with tab1:
    st.subheader("Employee Input")

    name = st.text_input("Employee Name")
    monthly_salary = st.number_input("Monthly Salary (₦)", min_value=0.0, step=1000.0)

    if st.button("Calculate"):

        if monthly_salary <= 0:
            st.warning("Enter a valid salary")
        else:
            result = calculate_paye(monthly_salary)

            st.markdown("## 📊 Results")

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

        # ✅ ADD PDF CODE RIGHT HERE
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()

        content = []

        content.append(Paragraph(f"Payslip for {name}", styles["Title"]))
        content.append(Paragraph(f"Monthly Salary: ₦{monthly_salary:,.2f}", styles["Normal"]))
        content.append(Paragraph(f"Pension: ₦{result['Pension']:,.2f}", styles["Normal"]))
        content.append(Paragraph(f"NHF: ₦{result['NHF']:,.2f}", styles["Normal"]))
        content.append(Paragraph(f"Annual Tax: ₦{result['Annual Tax']:,.2f}", styles["Normal"]))
        content.append(Paragraph(f"Monthly PAYE: ₦{result['Monthly Tax']:,.2f}", styles["Normal"]))

        doc.build(content)

        pdf = buffer.getvalue()

        st.download_button(
            label="⬇️ Download Payslip (PDF)",
            data=pdf,
            file_name=f"{name}_payslip.pdf",
            mime="application/pdf"
        )
# Bulk Upload
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

            for _, row in df.iterrows():
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

            # Download button
            csv = result_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="⬇️ Download Results",
                data=csv,
                file_name="payroll_results.csv",
                mime="text/csv"
  )

