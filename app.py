import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# تعريف الروابط الأصلية المطلوبة لعمليات الكتابة والتحديث (Submit)
URL_LAB_SYSTEM = "https://docs.google.com/spreadsheets/d/1S4lxWzPz7e-DmjaLxQ1MYX01PIYPzfaZOU7au1x7gu4/edit?usp=sharing"
URL_NANO_SYSTEM = "https://docs.google.com/spreadsheets/d/17yfyJFXQZ7aw9uMSRO1oYbIIl_LQMHGYDHrf2Eqnho8/edit?usp=sharing"

# تعريف الاتصال المخصص للكتابة والتحديث
conn = st.connection("gsheets", type=GSheetsConnection)
@st.cache_data(ttl=600)
def load_data():
    try:
        # ضع هنا روابط "النشر على الويب بصيغة CSV" لكل تبويب على حدة
        df_wh = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vRa0Zxuw3C1fv_PVi0dV7nwaO2Zz22hXqTDRC4VM1PzPTW3SZVoXdhv1P5TvIZK7V-yDsh-gVDIFE-v/pub?gid=1870539181&single=true&output=csv")
        df_lab = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vRa0Zxuw3C1fv_PVi0dV7nwaO2Zz22hXqTDRC4VM1PzPTW3SZVoXdhv1P5TvIZK7V-yDsh-gVDIFE-v/pub?gid=2041709056&single=true&output=csv")
        df_usage = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vRa0Zxuw3C1fv_PVi0dV7nwaO2Zz22hXqTDRC4VM1PzPTW3SZVoXdhv1P5TvIZK7V-yDsh-gVDIFE-v/pub?gid=795100404&single=true&output=csv")
        df_restock = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vRa0Zxuw3C1fv_PVi0dV7nwaO2Zz22hXqTDRC4VM1PzPTW3SZVoXdhv1P5TvIZK7V-yDsh-gVDIFE-v/pub?gid=1837567229&single=true&output=csv")
        
        df_nano = None
        try:
            df_nano = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vRT6pysdV8p1MU8ZVPHE4-_zKu1kCXo65ZICzHfX_fU4rZSEELwYDOZMIcAZtAO7cshvEwx_dhmSpEK/pub?gid=1177993820&single=true&output=csv")
        except Exception:
            pass
            
        return df_wh, df_lab, df_usage, df_restock, df_nano
    except Exception as e:
        st.error(f"Error loading Google Sheets: {e}")
        return None, None, None, None, None

st.title("🧪 Advanced Lab, Nanomaterials & Warehouse Management System")
st.markdown("---")

df_wh, df_lab, df_usage, df_restock, df_nano = load_data()

if df_lab is not None:
    # Clean column names
    df_lab.columns = df_lab.columns.astype(str).str.strip()
    df_wh.columns = df_wh.columns.astype(str).str.strip()
    df_usage.columns = df_usage.columns.astype(str).str.strip()
    df_restock.columns = df_restock.columns.astype(str).str.strip()
    if df_nano is not None:
        df_nano.columns = df_nano.columns.astype(str).str.strip()

    # --- Calculations for Lab Chemicals ---
    restock_sum = df_restock.groupby('Chemical Name')['Restocked Weight Added (g/ml)'].sum().reset_index() if not df_restock.empty and 'Restocked Weight Added (g/ml)' in df_restock.columns else pd.DataFrame(columns=['Chemical Name', 'Restocked Weight Added (g/ml)'])
    usage_sum = df_usage.groupby('Chemical Name')['Quantity Used (g/ml)'].sum().reset_index() if not df_usage.empty and 'Quantity Used (g/ml)' in df_usage.columns else pd.DataFrame(columns=['Chemical Name', 'Quantity Used (g/ml)'])

    df_lab = df_lab.merge(restock_sum, on='Chemical Name', how='left').merge(usage_sum, on='Chemical Name', how='left')
    df_lab['Restocked Weight Added (g/ml)'] = df_lab['Restocked Weight Added (g/ml)'].fillna(0)
    df_lab['Quantity Used (g/ml)'] = df_lab['Quantity Used (g/ml)'].fillna(0)

    # Respect manual edits in Excel/Google Sheets for Initial Open Bottle Weight
    base_weight_col = 'Initial Open Bottle Weight' if 'Initial Open Bottle Weight' in df_lab.columns else 'Bottle Capacity'
    df_lab['Current Available Weight'] = df_lab[base_weight_col].fillna(df_lab['Bottle Capacity']) + df_lab['Restocked Weight Added (g/ml)'] - df_lab['Quantity Used (g/ml)']
    
    df_lab['Status'] = df_lab.apply(
        lambda row: '🔴 Empty' if row['Current Available Weight'] <= 0 else ('⚠️ Low Stock (<25%)' if row['Current Available Weight'] <= 0.25 * row['Bottle Capacity'] else '✅ In Stock'),
        axis=1
    )

    lab_display_cols = ['Chemical ID', 'Category', 'Chemical Name', 'Grade', 'Bottle Capacity', 'Quantity Used (g/ml)', 'Current Available Weight', 'Status']
    lab_display_cols = [c for c in lab_display_cols if c in df_lab.columns]

    # Sidebar Navigation
    menu = st.sidebar.radio("Navigation", [
        "🔬 Lab Inventory", 
        "🧬 Nanomaterials Inventory", 
        "📦 Warehouse Stock", 
        "✏️ Log Usage", 
        "🔄 Quick Restock", 
        "➕ Add New Items",
        "📜 Usage History"
    ])

    if menu == "🔬 Lab Inventory":
        st.header("📊 Lab Chemical Inventory")
        st.dataframe(df_lab[lab_display_cols], use_container_width=True)

    elif menu == "🧬 Nanomaterials Inventory":
        st.header("🧪 Nanomaterials Inventory")
        if df_nano is not None:
            nano_usage = df_usage.groupby('Chemical Name')['Quantity Used (g/ml)'].sum().reset_index() if not df_usage.empty else pd.DataFrame()
            if not nano_usage.empty and 'Product Name' in df_nano.columns:
                df_nano_merged = df_nano.merge(nano_usage, left_on='Product Name', right_on='Chemical Name', how='left')
                df_nano_merged['Quantity Used (g/ml)'] = df_nano_merged['Quantity Used (g/ml)'].fillna(0)
                if 'Full Bottle Size' in df_nano_merged.columns:
                    df_nano_merged['Current Stock'] = df_nano_merged['Full Bottle Size'] - df_nano_merged['Quantity Used (g/ml)']
                    df_nano_merged['Status'] = df_nano_merged.apply(
                        lambda r: '⚠️ Low Stock' if r['Current Stock'] <= 0.25 * r['Full Bottle Size'] else '✅ In Stock', axis=1
                    )
                cols_to_drop = ['Starting Stock', 'Total Used']
                for c in cols_to_drop:
                    if c in df_nano_merged.columns:
                        df_nano_merged.drop(columns=[c], inplace=True)
                st.dataframe(df_nano_merged, use_container_width=True)
            else:
                cols_to_drop = ['Starting Stock', 'Total Used']
                df_nano_clean = df_nano.copy()
                for c in cols_to_drop:
                    if c in df_nano_clean.columns:
                        df_nano_clean.drop(columns=[c], inplace=True)
                st.dataframe(df_nano_clean, use_container_width=True)
        else:
            st.info("Nano Materials Google Sheet not found.")

    elif menu == "📦 Warehouse Stock":
        st.header("📦 Warehouse Unopened Stock")
        st.dataframe(df_wh, use_container_width=True)

    elif menu == "✏️ Log Usage":
        st.header("✏️ Record Chemical / Nanomaterial Usage")
        
        all_materials = list(df_lab["Chemical Name"].dropna().unique())
        if df_nano is not None and "Product Name" in df_nano.columns:
            all_materials += list(df_nano["Product Name"].dropna().unique())

        with st.form("usage_form"):
            researcher = st.text_input("Researcher Name")
            chemical = st.selectbox("Select Material", sorted(list(set(all_materials))))
            qty = st.number_input("Quantity Used (g or ml)", min_value=0.0, step=0.1)
            notes = st.text_input("Experiment / Notes")
            submit = st.form_submit_button("Submit Usage")

            if submit and researcher and chemical and qty > 0:
                try:
                    new_entry = pd.DataFrame([{
                        "Date": datetime.date.today().strftime("%Y-%m-%d"),
                        "Researcher Name": researcher,
                        "Chemical Name": chemical,
                        "Unit": "g/ml",
                        "Quantity Used (g/ml)": qty,
                        "Experiment / Notes": notes
                    }])
                    updated_usage = pd.concat([df_usage, new_entry], ignore_index=True)
                    conn.update(spreadsheet=URL_LAB_SYSTEM, worksheet="Lab Usage Log", data=updated_usage)
                    st.success(f"Successfully recorded {qty} g/ml for {chemical}!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating Google Sheet: {e}")

    elif menu == "🔄 Quick Restock":
        st.header("🔄 Restock Bottle to Lab & Deduct from Warehouse")
        st.info("Select the chemical and corresponding warehouse batch to transfer a bottle to the lab.")

        selected_chem = st.selectbox("Select Chemical to Restock", df_lab["Chemical Name"].unique())
        
        wh_matches = df_wh[df_wh['Chemical Name'].str.contains(selected_chem[:5], case=False, na=False)]
        
        with st.form("restock_action_form"):
            staff_name = st.text_input("Staff / Researcher Name")
            
            if not wh_matches.empty:
                wh_option = st.selectbox("Select Warehouse Batch", 
                                         wh_matches.apply(lambda r: f"{r['Chemical Name']} | Grade: {r['Company / Grade']} | Available: {r['Unopened Bottles Stock']}", axis=1))
            else:
                wh_option = st.selectbox("Select from Available Warehouse Stock", 
                                         df_wh.apply(lambda r: f"{r['Chemical Name']} | Grade: {r['Company / Grade']} | Available: {r['Unopened Bottles Stock']}", axis=1))

            notes = st.text_input("Notes")
            btn_restock = st.form_submit_button("Confirm Restock & Transfer")

            if btn_restock and staff_name:
                try:
                    capacity = df_lab[df_lab["Chemical Name"] == selected_chem]["Bottle Capacity"].values[0] if selected_chem in df_lab["Chemical Name"].values else 500
                    
                    new_restock = pd.DataFrame([{
                        "Restock Date": datetime.date.today().strftime("%Y-%m-%d"),
                        "Researcher / Staff Name": staff_name,
                        "Chemical Name": selected_chem,
                        "Warehouse Source": "Main Warehouse",
                        "Restocked Weight Added (g/ml)": capacity,
                        "Notes": f"Restock from warehouse ({wh_option}). Notes: {notes}"
                    }])
                    updated_restock = pd.concat([df_restock, new_restock], ignore_index=True)
                    conn.update(spreadsheet=URL_LAB_SYSTEM, worksheet="Restock Log", data=updated_restock)
                    st.success(f"Successfully restocked 1 bottle of {selected_chem} ({capacity} g/ml)!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating Google Sheet: {e}")

    elif menu == "➕ Add New Items":
        st.header("➕ Add New Items to System")
        
        add_type = st.radio("Select Target Inventory", ["Warehouse Chemical", "Lab Chemical", "Nanomaterial"])
        
        if add_type == "Warehouse Chemical":
            with st.form("add_wh_form"):
                st.subheader("Add New Chemical to Warehouse Stock")
                item_id = st.text_input("Item ID (e.g. WH-100)")
                chem_name = st.text_input("Chemical Name")
                company_grade = st.text_input("Company / Grade (e.g. Loba / AR)")
                bottle_size = st.number_input("Bottle Size (g/ml)", min_value=1.0, value=500.0)
                initial_stock = st.number_input("Unopened Bottles Stock", min_value=1, value=5)
                submit_wh = st.form_submit_button("Add to Warehouse")
                
                if submit_wh and item_id and chem_name:
                    try:
                        new_wh = pd.DataFrame([{
                            "Item ID": item_id,
                            "Chemical Name": chem_name,
                            "Company / Grade": company_grade,
                            "Bottle Size (g/ml)": bottle_size,
                            "Unopened Bottles Stock": initial_stock
                        }])
                        updated_wh = pd.concat([df_wh, new_wh], ignore_index=True)
                        conn.update(spreadsheet=URL_LAB_SYSTEM, worksheet="Warehouse Stock", data=updated_wh)
                        st.success(f"Successfully added {chem_name} to Warehouse Stock!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating Google Sheet: {e}")
                        
        elif add_type == "Lab Chemical":
            with st.form("add_lab_form"):
                st.subheader("Add New Chemical to Lab Inventory")
                chem_id = st.text_input("Chemical ID (e.g. CHEM-300)")
                category = st.selectbox("Category", ["Solid", "Liquid", "Solvent"])
                chem_name = st.text_input("Chemical Name")
                grade = st.text_input("Grade (e.g. Loba, Merck)")
                bottle_capacity = st.number_input("Bottle Capacity (g/ml)", min_value=1.0, value=500.0)
                submit_lab = st.form_submit_button("Add to Lab Inventory")
                
                if submit_lab and chem_id and chem_name:
                    try:
                        new_lab = pd.DataFrame([{
                            "Chemical ID": chem_id,
                            "Category": category,
                            "Chemical Name": chem_name,
                            "Grade": grade,
                            "Bottle Capacity": bottle_capacity,
                            "Initial Open Bottle Weight": bottle_capacity
                        }])
                        updated_lab = pd.concat([df_lab, new_lab], ignore_index=True)
                        conn.update(spreadsheet=URL_LAB_SYSTEM, worksheet="Lab Inventory", data=updated_lab)
                        st.success(f"Successfully added {chem_name} to Lab Inventory!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating Google Sheet: {e}")
                        
        elif add_type == "Nanomaterial":
            with st.form("add_nano_form"):
                st.subheader("Add Synthesized / New Nanomaterial")
                nano_id = st.text_input("ID (e.g. NANO-400)")
                category = st.text_input("Category (e.g. Metal Oxides, MOFs)")
                drawer = st.text_input("Drawer / Location (e.g. Drawer 1)")
                product_name = st.text_input("Product Name")
                full_size = st.number_input("Full Bottle Size / Mass (g)", min_value=0.1, value=20.0)
                unit = st.text_input("Unit", value="g")
                submit_nano = st.form_submit_button("Add Nanomaterial")
                
                if submit_nano and nano_id and product_name:
                    try:
                        new_nano = pd.DataFrame([{
                            "ID": nano_id,
                            "Category": category,
                            "Drawer / Location": drawer,
                            "Product Name": product_name,
                            "Full Bottle Size": full_size,
                            "Starting Stock": full_size,
                            "Unit": unit,
                            "Total Used": 0
                        }])
                        updated_nano = pd.concat([df_nano, new_nano], ignore_index=True)
                        conn.update(spreadsheet=URL_NANO_SYSTEM, worksheet="Nano Inventory", data=updated_nano)
                        st.success(f"Successfully added {product_name} to Nanomaterials Inventory!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating Google Sheet: {e}")

    elif menu == "📜 Usage History":
        st.header("📜 Usage & Restock History Logs")
        
        st.subheader("📋 Lab & Nanomaterial Usage Log")
        clean_usage = df_usage.dropna(subset=['Chemical Name']).copy() if not df_usage.empty and 'Chemical Name' in df_usage.columns else pd.DataFrame()
        if not clean_usage.empty:
            st.dataframe(clean_usage, use_container_width=True)
        else:
            st.info("No usage records found yet.")

        st.markdown("---")
        st.subheader("🔄 Bottle Restock Log")
        clean_restock = df_restock.dropna(subset=['Chemical Name']).copy() if not df_restock.empty and 'Chemical Name' in df_restock.columns else pd.DataFrame()
        if not clean_restock.empty:
            st.dataframe(clean_restock, use_container_width=True)
        else:
            st.info("No restock records found yet.")
