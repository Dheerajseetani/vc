import streamlit as st
import pandas as pd
from datetime import datetime
import traceback
from app.auth import register_user, login_user, get_user_vcs, save_user_vcs

def handle_error(func):
    """Decorator for handling errors in functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            if st.session_state.get('debug_mode', False):
                st.code(traceback.format_exc())
            return None
    return wrapper

@handle_error
def init_session_state():
    """Initialize session state variables."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False

@handle_error
def login_page():
    """Display login and registration forms."""
    st.title("VC Tracker Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not username or not password:
                    st.error("Please fill in all fields")
                    return
                
                success, message = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register")
            
            if submit:
                if not new_username or not new_password or not confirm_password:
                    st.error("Please fill in all fields")
                    return
                    
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    return
                    
                if len(new_password) < 6:
                    st.error("Password must be at least 6 characters long")
                    return
                    
                success, message = register_user(new_username, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)

@handle_error
def add_new_vc():
    """Add a new VC entry."""
    st.header("Add New VC")
    
    with st.form("new_vc_form"):
        vc_name = st.text_input("VC Name")
        total_amount = st.number_input("Total VC Amount (PKR)", min_value=0.0, step=1000.0)
        num_members = st.number_input("Number of Members", min_value=1, step=1)
        current_month = st.number_input("VC No", min_value=1, step=1)
        start_date = st.date_input("Start Date")
        is_active = st.checkbox("Mark as Active")
        
        if is_active:
            months_left = st.number_input("Months Left", min_value=1, step=1)
        
        submit = st.form_submit_button("Add VC")
        
        if submit:
            if not vc_name:
                st.error("Please enter a VC name")
                return
                
            if total_amount <= 0:
                st.error("Total amount must be greater than 0")
                return
                
            if num_members <= 0:
                st.error("Number of members must be greater than 0")
                return
                
            vcs = get_user_vcs(st.session_state.username)
            
            new_vc = {
                'name': vc_name,
                'total_amount': float(total_amount),
                'num_members': int(num_members),
                'current_month': int(current_month),
                'start_date': start_date.strftime("%Y-%m-%d"),
                'is_active': is_active,
                'monthly_payments': [],
                'payment_dates': [],
                'interest_rates': []
            }
            
            if is_active:
                new_vc['months_left'] = int(months_left)
            
            vcs.append(new_vc)
            save_user_vcs(st.session_state.username, vcs)
            st.success("VC added successfully!")

@handle_error
def view_all_vcs():
    """View all VCs and their details."""
    st.header("View All VCs")
    
    vcs = get_user_vcs(st.session_state.username)
    
    if not vcs:
        st.info("No VCs found. Add a new VC to get started.")
        return
    
    for vc in vcs:
        with st.expander(f"{vc['name']} - {'Active' if vc['is_active'] else 'Completed'}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Amount", f"PKR {vc['total_amount']:,.2f}")
                st.metric("Number of Members", vc['num_members'])
                st.metric("Current Month", vc['current_month'])
            
            with col2:
                if vc['is_active']:
                    st.metric("Months Left", vc['months_left'])
                    if st.button("Add Latest Payment", key=f"add_{vc['name']}"):
                        payment = st.number_input("Payment Amount", min_value=0.0, step=1000.0)
                        payment_date = st.date_input("Payment Date")
                        if st.button("Save Payment"):
                            if payment <= 0:
                                st.error("Payment amount must be greater than 0")
                                return
                                
                            vc['monthly_payments'].append(float(payment))
                            vc['payment_dates'].append(payment_date.strftime("%Y-%m-%d"))
                            vc['current_month'] += 1
                            vc['months_left'] -= 1
                            save_user_vcs(st.session_state.username, vcs)
                            st.rerun()
            
            if vc['monthly_payments']:
                st.subheader("Payment History")
                payment_data = {
                    "Month": range(1, len(vc['monthly_payments']) + 1),
                    "Payment Date": vc['payment_dates'],
                    "Expected Payment": [vc['total_amount'] / vc['num_members']] * len(vc['monthly_payments']),
                    "Actual Payment": vc['monthly_payments'],
                    "Monthly Savings": [vc['total_amount'] / vc['num_members'] - p for p in vc['monthly_payments']],
                    "Interest Rate": [(p / (vc['total_amount'] - sum(vc['monthly_payments'][:i]))) * 100 
                                    for i, p in enumerate(vc['monthly_payments'], 1)]
                }
                
                df = pd.DataFrame(payment_data)
                st.dataframe(df.style.format({
                    "Expected Payment": "PKR {:,.2f}",
                    "Actual Payment": "PKR {:,.2f}",
                    "Monthly Savings": "PKR {:,.2f}",
                    "Interest Rate": "{:.2f}%"
                }))

@handle_error
def interest_calculator():
    """Calculate interest rates and profits."""
    st.header("Interest Calculator")
    
    vcs = get_user_vcs(st.session_state.username)
    
    if not vcs:
        st.info("No VCs found. Add a new VC to calculate interest.")
        return
    
    for vc in vcs:
        if vc['monthly_payments']:
            with st.expander(f"{vc['name']} - Interest Analysis"):
                total_paid = sum(vc['monthly_payments'])
                total_expected = vc['total_amount']
                total_savings = total_expected - total_paid
                monthly_savings = total_savings / len(vc['monthly_payments'])
                profit_percentage = (total_savings / total_expected) * 100
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Expected", f"PKR {total_expected:,.2f}")
                    st.metric("Total Paid", f"PKR {total_paid:,.2f}")
                
                with col2:
                    st.metric("Total Savings", f"PKR {total_savings:,.2f}")
                    st.metric("Monthly Savings", f"PKR {monthly_savings:,.2f}")
                    st.metric("Profit Percentage", f"{profit_percentage:.2f}%")

@handle_error
def main():
    """Main application function."""
    st.set_page_config(page_title="VC Tracker", layout="wide")
    
    init_session_state()
    
    # Debug mode toggle in sidebar
    if st.session_state.logged_in:
        st.sidebar.checkbox("Debug Mode", key="debug_mode")
    
    if not st.session_state.logged_in:
        login_page()
    else:
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Add New VC", "View All VCs", "Interest Calculator"])
        
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
        
        if page == "Add New VC":
            add_new_vc()
        elif page == "View All VCs":
            view_all_vcs()
        else:
            interest_calculator()

if __name__ == "__main__":
    main() 