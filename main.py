import streamlit as st
import pandas as pd
from datetime import datetime
import traceback
import json
import os
from pathlib import Path
from app.auth import register_user, login_user, get_user_vcs, save_user_vcs
import time

# Set page config
st.set_page_config(page_title="VC Tracker", page_icon="💰", layout="wide")

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
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = time.time()
    
    # Check for existing cookie
    if 'vc_tracker_session' in st.session_state:
        try:
            session_data = json.loads(st.session_state.vc_tracker_session)
            if time.time() - session_data['timestamp'] < 600:  # 10 minutes
                st.session_state.logged_in = True
                st.session_state.username = session_data['username']
                st.session_state.last_activity = session_data['timestamp']
            else:
                # Clear expired session
                del st.session_state.vc_tracker_session
        except:
            pass
    
    # Update last activity
    st.session_state.last_activity = time.time()

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
                    # Set session cookie
                    session_data = {
                        'username': username,
                        'timestamp': time.time()
                    }
                    st.session_state.vc_tracker_session = json.dumps(session_data)
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
        num_members = st.number_input("Number of Members", min_value=2, step=1)
        current_month = st.number_input("VC No", min_value=1, step=1, 
                                      help="Enter the VC number")
        start_date = st.date_input("Start Date")
        
        # Calculate months completed and remaining
        months_completed = current_month  # VC No 1 means 1 month completed
        months_left = num_members - current_month 
        
        st.write(f"Months Completed: {months_completed}")
        st.write(f"Months Remaining: {months_left}")
        
        # Monthly payments input
        st.subheader("Monthly Payments")
        monthly_payments = []
        payment_dates = []
        for i in range(months_completed):
            col1, col2 = st.columns(2)
            with col1:
                payment = st.number_input(f"Payment for Month {i+1} (PKR)", min_value=0.0, step=1000.0)
            with col2:
                payment_date = st.date_input(f"Payment Date for Month {i+1}", key=f"date_{i}")
            monthly_payments.append(payment)
            payment_dates.append(payment_date.strftime("%Y-%m-%d"))
        
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
            
            # Calculate expected monthly payment
            expected_monthly = total_amount / num_members
            
            # Calculate actual payments and savings
            total_paid = sum(monthly_payments)
            expected_total = expected_monthly * months_completed
            total_savings = expected_total - total_paid
            monthly_savings = total_savings / months_completed if months_completed > 0 else 0
            
            # Calculate profit percentage
            profit_percentage = (total_savings / expected_total) * 100 if expected_total > 0 else 0
            
            # Calculate interest rate for each month
            interest_rates = []
            for payment in monthly_payments:
                x = total_amount - payment * num_members
                y = x / months_left
                interest_rate = (y / (payment * num_members)) * 100 if x > 0 else 0
                interest_rates.append(interest_rate)
            
            new_vc = {
                'name': vc_name,
                'total_amount': float(total_amount),
                'num_members': int(num_members),
                'current_month': int(current_month),
                'months_left': months_left,
                'bid_amount': monthly_payments[-1] if monthly_payments else total_amount / num_members,
                'start_date': start_date.strftime("%Y-%m-%d"),
                'is_historical': months_left == 0,
                'monthly_interest_rate': interest_rates[-1] if interest_rates else 0,
                'original_monthly': expected_monthly,
                'new_monthly': monthly_payments[-1] / months_left if monthly_payments else total_amount / num_members,
                'monthly_savings': monthly_savings,
                'total_savings': total_savings,
                'expected_total': expected_total,
                'total_paid': total_paid,
                'profit_percentage': profit_percentage,
                'monthly_payments': monthly_payments,
                'payment_dates': payment_dates,
                'interest_rates': interest_rates,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            vcs.append(new_vc)
            save_user_vcs(st.session_state.username, vcs)
            st.success("VC added successfully!")

@handle_error
def view_all_vcs():
    """View all VCs and their details."""
    st.header("Your VCs")
    
    vcs = get_user_vcs(st.session_state.username)
    
    if not vcs:
        st.info("No VCs found. Add a new VC to get started.")
        return
    
    for vc in vcs:
        with st.expander(f"{vc['name']} - VC No: {vc.get('current_month', 'N/A')}"):
            # Basic VC Info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Amount", f"PKR {vc['total_amount']:,.2f}")
                st.metric("Number of Members", vc.get('num_members', 'N/A'))
            with col2:
                st.metric("VC No", vc.get('current_month', 'N/A'))
                st.metric("Months Left", vc.get('months_left', 'N/A'))
            with col3:
                st.metric("Monthly Payment", f"PKR {vc.get('original_monthly', 0):,.2f}")
            
            # Add payment and delete buttons
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Add Latest Payment")
                with st.form(f"add_payment_{vc['name']}"):
                    payment_amount = st.number_input("Payment Amount (PKR)", min_value=0.0, step=1000.0)
                    payment_date = st.date_input("Payment Date")
                    if st.form_submit_button("Add Payment"):
                        if payment_amount <= 0:
                            st.error("Payment amount must be greater than 0")
                            return
                        
                        # Update VC data
                        vc['monthly_payments'] = vc.get('monthly_payments', []) + [payment_amount]
                        vc['payment_dates'] = vc.get('payment_dates', []) + [payment_date.strftime("%Y-%m-%d")]
                        vc['current_month'] = vc.get('current_month', 1) + 1
                        vc['months_left'] = vc.get('months_left', 1) - 1
                        
                        # Recalculate values
                        expected_monthly = vc['total_amount'] / vc.get('num_members', 1)
                        total_paid = sum(vc['monthly_payments'])
                        expected_total = expected_monthly * len(vc['monthly_payments'])
                        total_savings = expected_total - total_paid
                        monthly_savings = total_savings / len(vc['monthly_payments'])
                        profit_percentage = (total_savings / expected_total) * 100 if expected_total > 0 else 0
                        
                        # Calculate interest rates
                        interest_rates = []
                        for payment in vc['monthly_payments']:
                            x = vc['total_amount'] - payment * vc.get('num_members', 1)
                            y = x / vc.get('months_left', 1)
                            interest_rate = (y / (payment * vc.get('num_members', 1))) * 100 if x > 0 else 0
                            interest_rates.append(interest_rate)
                        
                        # Update VC entry
                        vc.update({
                            'original_monthly': expected_monthly,
                            'new_monthly': payment_amount / vc.get('months_left', 1),
                            'monthly_savings': monthly_savings,
                            'total_savings': total_savings,
                            'expected_total': expected_total,
                            'total_paid': total_paid,
                            'profit_percentage': profit_percentage,
                            'interest_rates': interest_rates
                        })
                        
                        # Save updated VCs
                        save_user_vcs(st.session_state.username, vcs)
                        st.success("Payment added successfully!")
                        st.rerun()
            
            with col2:
                st.subheader("Delete VC")
                if st.button("Delete VC", key=f"delete_{vc['name']}"):
                    vcs.remove(vc)
                    save_user_vcs(st.session_state.username, vcs)
                    st.success("VC deleted successfully!")
                    st.rerun()
            
            # Payment History
            st.header("Payment History")
            if 'monthly_payments' in vc and vc['monthly_payments']:
                # Create columns for the table header
                cols = st.columns([1, 2, 2, 2, 2, 2, 1])
                headers = ["Month", "Payment Date", "Expected Payment", "Actual Payment", "Monthly Savings", "Interest Rate", "Action"]
                for col, header in zip(cols, headers):
                    col.write(f"**{header}**")
                
                # Display each row
                for i in range(len(vc['monthly_payments'])):
                    cols = st.columns([1, 2, 2, 2, 2, 2, 1])
                    
                    # Format the data
                    month = i + 1
                    payment_date = vc.get('payment_dates', ['N/A'] * len(vc['monthly_payments']))[i]
                    expected_payment = f"PKR {vc.get('original_monthly', 0):,.2f}"
                    actual_payment = f"PKR {vc['monthly_payments'][i]:,.2f}"
                    monthly_savings = f"PKR {vc.get('original_monthly', 0) - vc['monthly_payments'][i]:,.2f}"
                    interest_rate = f"{vc.get('interest_rates', [0] * len(vc['monthly_payments']))[i]:,.2f}%"
                    
                    # Display the data
                    cols[0].write(month)
                    cols[1].write(payment_date)
                    cols[2].write(expected_payment)
                    cols[3].write(actual_payment)
                    cols[4].write(monthly_savings)
                    cols[5].write(interest_rate)
                    
                    # Add delete button
                    if cols[6].button("Delete", key=f"delete_payment_{vc['name']}_{i}", help=f"Delete payment for month {month}"):
                        # Remove the payment and its associated data
                        vc['monthly_payments'].pop(i)
                        if 'payment_dates' in vc:
                            vc['payment_dates'].pop(i)
                        if 'interest_rates' in vc:
                            vc['interest_rates'].pop(i)
                        
                        # Update VC data
                        vc['current_month'] = len(vc['monthly_payments']) + 1
                        vc['months_left'] = vc.get('num_members', 1) - len(vc['monthly_payments'])
                        
                        # Recalculate values
                        expected_monthly = vc['total_amount'] / vc.get('num_members', 1)
                        total_paid = sum(vc['monthly_payments'])
                        expected_total = expected_monthly * len(vc['monthly_payments'])
                        total_savings = expected_total - total_paid
                        monthly_savings = total_savings / len(vc['monthly_payments']) if vc['monthly_payments'] else 0
                        profit_percentage = (total_savings / expected_total) * 100 if expected_total > 0 else 0
                        
                        # Update VC entry
                        vc.update({
                            'original_monthly': expected_monthly,
                            'new_monthly': vc['monthly_payments'][-1] / vc['months_left'] if vc['monthly_payments'] else expected_monthly,
                            'monthly_savings': monthly_savings,
                            'total_savings': total_savings,
                            'expected_total': expected_total,
                            'total_paid': total_paid,
                            'profit_percentage': profit_percentage
                        })
                        
                        # Save updated VCs
                        save_user_vcs(st.session_state.username, vcs)
                        st.success("Payment entry deleted successfully!")
                        st.rerun()
            else:
                st.info("No payment history available")
            
            # Profit Analysis
            st.header("Profit Analysis")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Expected", f"PKR {vc.get('expected_total', 0):,.2f}")
                st.metric("Total Paid", f"PKR {vc.get('total_paid', 0):,.2f}")
            with col2:
                st.metric("Total Savings", f"PKR {vc.get('total_savings', 0):,.2f}")
                st.metric("Monthly Savings", f"PKR {vc.get('monthly_savings', 0):,.2f}")
            with col3:
                st.metric("Profit Percentage", f"{vc.get('profit_percentage', 0):,.2f}%")

@handle_error
def interest_calculator():
    """Calculate interest rates and profits."""
    st.header("VC Interest Calculator")
    
    # Input parameters
    st.subheader("Enter VC Details")
    
    col1, col2 = st.columns(2)
    with col1:
        total_vc = st.number_input("Total VC Amount (PKR)", min_value=0.0, step=1000.0)
        num_members = st.number_input("Number of Members", min_value=2, step=1)
    with col2:
        months_left = st.number_input("Months Left", min_value=1, step=1)
        bid_amount = st.number_input("Bid Amount (PKR)", min_value=0.0, step=1000.0)
    
    # Validate inputs
    if total_vc > 0 and months_left > 0 and bid_amount > 0 and num_members > 0:
        # Calculate expected monthly payment
        expected_monthly = total_vc / num_members
        
        # Calculate interest rate
        x = total_vc - bid_amount  # Difference between total VC and bid
        y = bid_amount / months_left  # Monthly bid amount
        
        if x > 0:  # Check if difference is not zero
            monthly_interest_rate = (y / x) * 100  # Monthly interest rate calculation
            
            # Calculate savings
            new_monthly = bid_amount / num_members
            monthly_savings = expected_monthly - new_monthly
            
            
            # Calculate remaining payment
            remaining_amount = total_vc - bid_amount
            remaining_monthly = monthly_savings
            
            # Display results
            st.header("Results")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Expected Monthly", f"PKR {expected_monthly:,.2f}")
                st.metric("Discount", f"PKR {new_monthly:,.2f}")
            with col2:
                st.metric("Remaining Amount", f"PKR {remaining_amount:,.2f}")
                st.metric("Remaining Monthly", f"PKR {remaining_monthly:,.2f}")
                
            with col3:
                st.metric("Monthly Interest Rate", f"{monthly_interest_rate:,.2f}%")
                
        else:
            st.error("The difference between Total VC and Bid Amount cannot be zero. Please enter a valid bid amount.")
    else:
        st.error("Please enter valid values for all fields. All values must be greater than zero.")

@handle_error
def main():
    """Main application function."""
    init_session_state()
    
    # Debug mode toggle in sidebar
    if st.session_state.logged_in:
        st.sidebar.checkbox("Debug Mode", key="debug_mode")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            if 'vc_tracker_session' in st.session_state:
                del st.session_state.vc_tracker_session
            st.rerun()
    
    if not st.session_state.logged_in:
        # Show calculator on home page
        st.title("VC Tracker")
        interest_calculator()
        
        # Show login/register below calculator
        st.markdown("---")
        login_page()
    else:
        # Create tabs for navigation
        tab1, tab2 = st.tabs(["My VCs", "Add New VC"])
        
        with tab1:
            view_all_vcs()
        
        with tab2:
            add_new_vc()

if __name__ == "__main__":
    main() 