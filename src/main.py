"""
Main Streamlit Application

This is the frontend interface for the Awesome Inc. Analytics System.
Includes:
- Secure authentication with bcrypt password hashing
- Dashboard
- Data entry forms
- Chat interface with LLM
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime
import random
import plotly.graph_objects as go
import plotly.express as px

from utils import (
    load_env_config, 
    setup_logger, 
    get_mysql_connection, 
    get_postgres_connection,
    release_postgres_connection,
    logger
)
from auth import (
    validate_password_strength,
    SECURITY_QUESTIONS,
    get_security_questions_for_user,
    get_signup_security_questions,
    # DATABASE-PERSISTENT FUNCTIONS
    authenticate_user_db,
    register_user_db,
    store_security_answers_db,
    get_security_answers_db,
    reset_password_db,
    get_user_table_name,
    verify_password,
    check_password_history
)
from function_tools import process_question
from etl_pipeline import run_etl_pipeline
from sql_loader import load_orders_with_products, load_returns_from_csv, get_sample_csv_format

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Awesome Inc. Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.session_state.chat_history = []
    st.session_state.conversation_history = []  # Multi-turn conversation context for LLM
    st.session_state.config = load_env_config()
    st.session_state.db_connection = None
    st.session_state.db_type = None  # "postgres" or "mysql"
    st.session_state.auth_db_connection = None  # Connection for auth queries (for DB persistence)


# ============================================================================
# DATABASE CONNECTION BY ROLE
# ============================================================================

def get_database_connection_for_role(role: str, config: dict) -> tuple:
    """
    Get database connection based on user role
    
    Args:
        role: User role (Sales Associate, Store Manager, Executive)
        config: Configuration dictionary
    
    Returns:
        Tuple of (connection, db_type, db_name)
    """
    try:
        if role in ["Store Manager", "Executive"]:
            # Store Manager and Executive use MySQL OLAP
            # Store Manager: Analytics and Chat
            # Executive: ETL Management and Infrastructure
            conn = get_mysql_connection(config)
            logger.info(f"Connected to MySQL OLAP for {role}")
            return conn, "mysql", "awesome_olap"
        elif role == "Sales Associate":
            # Sales Associate uses PostgreSQL OLTP for data entry
            conn = get_postgres_connection(config)
            logger.info(f"Connected to PostgreSQL OLTP for {role}")
            return conn, "postgres", "awesome_inc_oltp"
        else:
            logger.error(f"Unknown role: {role}")
            return None, None, None
    except Exception as e:
        logger.error(f"Error connecting to database for role {role}: {e}")
        return None, None, None


# ============================================================================
# AUTHENTICATION
# ============================================================================

def login_page():
    """Display authentication page with Login, Signup, and Password Reset tabs"""
    
    # Custom CSS
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none}
        footer {display: none}
        body {overflow-y: scroll;}
        ::-webkit-scrollbar {width: 0px;}
        html {scrollbar-width: none;}
        .main {padding: 3rem 0;}
        .stTextInput, .stButton {margin-bottom: 1rem;}
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    col_left, col_center, col_right = st.columns([1, 3, 1])
    
    with col_center:
        # Header
        st.markdown("<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center;'><h1 style='color: white; margin: 0;'>📊 Awesome Inc.</h1><p style='color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0; font-size: 0.95rem;'>🤖 AI-Powered Analytics System</p></div>", unsafe_allow_html=True)
        
        # Tabs for Login, Signup, Password Reset
        tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🔑 Forgot Password"])
        
        # =====================================================================
        # TAB 1: LOGIN (DATABASE PERSISTENT)
        # =====================================================================
        with tab1:
            st.markdown("<h3 style='text-align: center;'>Login to Your Account</h3>", unsafe_allow_html=True)
            st.markdown("")
            
            # Role selection for login
            login_role = st.selectbox(
                "👔 Select Your Role",
                ["Sales Associate", "Store Manager", "Executive"],
                key="login_role",
                help="Sales Associate: Data entry | Store Manager: Analytics | Executive: ETL Management"
            )
            
            username = st.text_input(
                "👤 Username",
                key="login_username",
                placeholder="Enter your username"
            )
            
            password = st.text_input(
                "🔑 Password",
                type="password",
                key="login_password",
                placeholder="Enter your password"
            )
            
            st.markdown("")
            
            if st.button("🚀 Login", width='stretch', key="login_button"):
                if not username or not password:
                    st.error("⚠️ Please enter both username and password")
                    logger.warning("Login attempt with missing credentials")
                else:
                    try:
                        # Get connection to role's database for authentication
                        auth_conn = None
                        try:
                            if login_role == "Sales Associate":
                                auth_conn = get_postgres_connection(st.session_state.config)
                            else:  # Store Manager or Executive
                                auth_conn = get_mysql_connection(st.session_state.config)
                            
                            # Authenticate against database (NOT in-memory DEMO_USERS)
                            auth_result = authenticate_user_db(username, password, login_role, auth_conn)
                            
                            if auth_result["authenticated"]:
                                st.session_state.authenticated = True
                                st.session_state.username = username
                                st.session_state.user_role = login_role
                                
                                # Get primary database connection for role's operations
                                conn, db_type, db_name = get_database_connection_for_role(
                                    login_role, 
                                    st.session_state.config
                                )
                                st.session_state.db_connection = conn
                                st.session_state.db_type = db_type
                                
                                logger.info(f"User {username} authenticated from {login_role} database")
                                st.success(f"✅ Welcome, {username}!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ {auth_result['message']}")
                                logger.warning(f"Failed login: user={username}, role={login_role}")
                        finally:
                            # Always release auth connection after login attempt
                            if auth_conn:
                                if login_role == "Sales Associate":
                                    release_postgres_connection(auth_conn)
                                else:
                                    auth_conn.close()
                    except Exception as e:
                        st.error(f"❌ Login error: {str(e)}")
                        logger.error(f"Login exception: {e}")
        
        # =====================================================================
        # TAB 2: SIGNUP (DATABASE PERSISTENT)
        # =====================================================================
        with tab2:
            st.markdown("<h3 style='text-align: center;'>Create New Account</h3>", unsafe_allow_html=True)
            st.markdown("")
            
            # Clear signup questions when entering new username
            signup_username = st.text_input(
                "👤 Username",
                key="signup_username",
                placeholder="Choose a username (min 3 characters)"
            )
            
            # Role selection dropdown
            signup_role = st.selectbox(
                "👔 Select Your Role",
                ["Sales Associate", "Store Manager", "Executive"],
                key="signup_role",
                help="Sales Associate: Data entry | Store Manager: Analytics | Executive: ETL Management"
            )
            
            # Reset questions when username changes
            if "prev_signup_username" not in st.session_state:
                st.session_state.prev_signup_username = signup_username
            elif st.session_state.prev_signup_username != signup_username:
                st.session_state.signup_questions = None
                st.session_state.prev_signup_username = signup_username
            
            # Step 1: Account Details
            st.markdown("**Step 1: Account Details**")
            
            signup_password = st.text_input(
                "🔑 Password",
                type="password",
                key="signup_password",
                placeholder="Enter a strong password"
            )
            
            signup_confirm = st.text_input(
                "🔑 Confirm Password",
                type="password",
                key="signup_confirm",
                placeholder="Confirm your password"
            )
            
            # Show password strength
            if signup_password:
                strength = validate_password_strength(signup_password)
                if strength['strength'] == 'strong':
                    st.success(f"✅ Password Strength: **STRONG**")
                elif strength['strength'] == 'medium':
                    st.warning(f"⚠️ Password Strength: **MEDIUM**")
                else:
                    st.error(f"❌ Password Strength: **WEAK** - {', '.join(strength['requirements'])}")
            
            st.markdown("---")
            st.markdown("**Step 2: Security Questions** (Answer 4 questions)")
            
            # Initialize session state for questions if not already done
            if "signup_questions" not in st.session_state or not st.session_state.signup_questions:
                st.session_state.signup_questions = get_signup_security_questions()
            
            # Use stored questions from session state to prevent shuffling
            signup_questions = st.session_state.signup_questions
            
            if signup_questions:
                # Use session state to store answers
                for idx, (q_index, question) in enumerate(signup_questions):
                    key_name = f"signup_answer_q{q_index}"
                    
                    st.text_input(
                        f"Q{idx+1}: {question}",
                        key=key_name,
                        placeholder="Your answer"
                    )
                
                st.markdown("")
                
                if st.button("✅ Create Account", width='stretch', key="signup_button"):
                    # Collect answers from session state
                    signup_answers = {}
                    for idx, (q_index, question) in enumerate(signup_questions):
                        key_name = f"signup_answer_q{q_index}"
                        if st.session_state[key_name]:
                            signup_answers[q_index] = st.session_state[key_name]
                    
                    # Validate inputs
                    if not signup_username or not signup_password or not signup_confirm:
                        st.error("⚠️ Please fill in all fields")
                    elif signup_password != signup_confirm:
                        st.error("❌ Passwords do not match")
                    elif len(signup_answers) < 4:
                        st.error("⚠️ Please answer all 4 security questions")
                    else:
                        try:
                            # Get connection to role's database
                            signup_conn = None
                            try:
                                if signup_role == "Sales Associate":
                                    signup_conn = get_postgres_connection(st.session_state.config)
                                else:  # Store Manager or Executive
                                    signup_conn = get_mysql_connection(st.session_state.config)
                                
                                # Register user in role's database (NOT in-memory DEMO_USERS)
                                reg_result = register_user_db(signup_username, signup_password, signup_role, signup_conn)
                                
                                if reg_result['success']:
                                    # Store security answers in role's database
                                    answers_result = store_security_answers_db(
                                        signup_username, 
                                        signup_role, 
                                        signup_answers, 
                                        signup_conn
                                    )
                                    
                                    if answers_result['success']:
                                        st.success(f"✅ Account created successfully!")
                                        st.info(f"Username: **{signup_username}** | Role: **{signup_role}**")
                                        st.info("🎉 You can now login with your credentials! (No re-signup needed after refresh)")
                                        logger.info(f"New account created: {signup_username} ({signup_role}) in {signup_role} database")
                                    else:
                                        st.error(f"⚠️ Account created but security answers failed: {answers_result['message']}")
                                else:
                                    st.error(f"❌ {reg_result['message']}")
                            finally:
                                # Always release signup connection after registration
                                if signup_conn:
                                    if signup_role == "Sales Associate":
                                        release_postgres_connection(signup_conn)
                                    else:
                                        signup_conn.close()
                        except Exception as e:
                            st.error(f"❌ Signup error: {str(e)}")
                            logger.error(f"Signup exception: {e}")
        
        # =====================================================================
        # TAB 3: FORGOT PASSWORD (DATABASE PERSISTENT)
        # =====================================================================
        with tab3:
            st.markdown("<h3 style='text-align: center;'>Reset Your Password</h3>", unsafe_allow_html=True)
            st.markdown("")
            
            # Role selection for password reset
            reset_role = st.selectbox(
                "👔 Select Your Role",
                ["Sales Associate", "Store Manager", "Executive"],
                key="reset_role",
                help="Sales Associate: Data entry | Store Manager: Analytics | Executive: ETL Management"
            )
            
            reset_username = st.text_input(
                "👤 Username",
                key="reset_username",
                placeholder="Enter your username"
            )
            
            # Reset questions when username changes
            if "prev_reset_username" not in st.session_state:
                st.session_state.prev_reset_username = reset_username
            elif st.session_state.prev_reset_username != reset_username:
                st.session_state.reset_questions = None
                st.session_state.reset_verified_user = None
                st.session_state.prev_reset_username = reset_username
            
            if reset_username:
                try:
                    # Get connection to role's database
                    reset_conn = None
                    try:
                        if reset_role == "Sales Associate":
                            reset_conn = get_postgres_connection(st.session_state.config)
                        else:  # Store Manager or Executive
                            reset_conn = get_mysql_connection(st.session_state.config)
                        
                        # Get security answers from role's database
                        stored_answers = get_security_answers_db(reset_username, reset_role, reset_conn)
                        
                        if not stored_answers:
                            st.error(f"⚠️ No security questions found for user '{reset_username}'")
                            st.info("User not found in the database or no security questions set")
                        else:
                            st.success(f"✅ Security questions found!")
                            st.markdown("")
                            st.markdown("**Answer your security questions (2 out of 3 correct to reset):**")
                            
                            # Initialize session state for reset questions if not already done
                            if "reset_questions" not in st.session_state or not st.session_state.reset_questions:
                                st.session_state.reset_questions = get_security_questions_for_user(reset_username, 3)
                            
                            # Use stored questions from session state
                            reset_questions = st.session_state.reset_questions
                            reset_answers = {}
                            
                            for idx, (q_index, question) in enumerate(reset_questions):
                                key_name = f"reset_answer_q{q_index}"
                                
                                st.text_input(
                                    f"Q{idx+1}: {question}",
                                    key=key_name,
                                    placeholder="Your answer"
                                )
                                if st.session_state.get(key_name):
                                    reset_answers[q_index] = st.session_state[key_name]
                            
                            st.markdown("")
                            
                            if st.button("✅ Verify & Continue", width='stretch', key="verify_sq_button"):
                                if len(reset_answers) < 3:
                                    st.error("⚠️ Please answer all 3 questions")
                                else:
                                    # Verify answers (2/3 correct) from database
                                    correct_count = 0
                                    for q_idx, user_answer in reset_answers.items():
                                        if str(q_idx) in stored_answers:
                                            # Verify hashed answer
                                            if verify_password(user_answer, stored_answers[str(q_idx)]):
                                                correct_count += 1
                                    
                                    if correct_count >= 2:
                                        st.session_state.reset_verified_user = reset_username
                                        st.session_state.reset_verified_role = reset_role
                                        st.session_state.reset_verified_conn = reset_conn
                                        st.success("✅ Security questions verified!")
                                    else:
                                        st.error("❌ Incorrect answers (need 2 out of 3 correct). Please try again.")
                                        logger.warning(f"Failed security question verification for: {reset_username} role: {reset_role}")
                    finally:
                        # Only close if not storing for password reset
                        if reset_conn and not st.session_state.get("reset_verified_user"):
                            if reset_role == "Sales Associate":
                                release_postgres_connection(reset_conn)
                            else:
                                reset_conn.close()
                        
                        # Show password reset form if verified
                        if st.session_state.get("reset_verified_user") == reset_username:
                            st.markdown("---")
                            st.markdown("**Enter your new password:**")
                            
                            # Use the stored connection or create a new one
                            history_conn = None
                            try:
                                if reset_role == "Sales Associate":
                                    history_conn = get_postgres_connection(st.session_state.config)
                                else:
                                    history_conn = get_mysql_connection(st.session_state.config)
                                
                                new_pwd = st.text_input(
                                    "🔑 New Password",
                                    type="password",
                                    key="reset_new_pwd",
                                    placeholder="Enter new password"
                                )
                                
                                # Real-time validation as user types
                                password_valid = True
                                if new_pwd:
                                    # Check for password reuse first
                                    is_reused = False
                                    if stored_answers:
                                        try:
                                            logger.debug(f"Checking password history for {reset_username} ({reset_role})")
                                            history_result = check_password_history(
                                                reset_username,
                                                reset_role,
                                                new_pwd,
                                                history_conn
                                            )
                                            logger.debug(f"History check result: {history_result}")
                                            if history_result.get('is_reused'):
                                                st.error("❌ This password was recently used. For security, please choose a different password")
                                                is_reused = True
                                                password_valid = False
                                        except Exception as e:
                                            logger.error(f"History check error: {e}")
                                    
                                    # Only show strength if password is not reused
                                    if not is_reused:
                                        strength = validate_password_strength(new_pwd)
                                        if strength['strength'] == 'strong':
                                            st.success(f"✅ Password Strength: **STRONG**")
                                        else:
                                            st.error(f"❌ {', '.join(strength['requirements'])}")
                                            password_valid = False
                                
                                confirm_pwd = st.text_input(
                                    "🔑 Confirm Password",
                                    type="password",
                                    key="reset_confirm_pwd",
                                    placeholder="Confirm new password"
                                )
                                
                                # Show mismatch error in real-time if both fields have content
                                if new_pwd and confirm_pwd and new_pwd != confirm_pwd:
                                    st.error("❌ Passwords do not match")
                                    password_valid = False
                                
                                st.markdown("")
                                
                                if st.button("🔄 Reset Password", width='stretch', key="reset_pwd_button", disabled=not password_valid or not new_pwd or not confirm_pwd):
                                    if not new_pwd or not confirm_pwd:
                                        st.error("⚠️ Please enter passwords")
                                    elif new_pwd != confirm_pwd:
                                        st.error("❌ Passwords do not match")
                                    elif not password_valid:
                                        st.error("❌ Please fix password issues above")
                                    else:
                                        # Reset password in database using the local connection
                                        pwd_reset_result = reset_password_db(
                                            reset_username,
                                            reset_role,
                                            new_pwd,
                                            history_conn
                                        )
                                        
                                        if pwd_reset_result['success']:
                                            st.success("✅ Password reset successfully!")
                                            st.info("You can now login with your new password")
                                            st.session_state.reset_verified_user = None
                                            logger.info(f"Password reset successful for: {reset_username} role: {reset_role}")
                                        else:
                                            st.error(f"❌ {pwd_reset_result['message']}")
                            finally:
                                # Clean up the history connection
                                if history_conn:
                                    if reset_role == "Sales Associate":
                                        release_postgres_connection(history_conn)
                                    else:
                                        history_conn.close()
                except Exception as e:
                    st.error(f"❌ Password reset error: {str(e)}")
                    logger.error(f"Password reset exception: {e}")
        
        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center; color: #999; font-size: 11px;'>
            <p style='margin: 5px 0;'>🔒 Secure authentication using bcrypt encryption</p>
            <p style='margin: 5px 0;'>All passwords and security answers are securely hashed</p>
            </div>
            """, unsafe_allow_html=True)


# ============================================================================
# DASHBOARD
# ============================================================================

def dashboard_page():
    """Display analytics dashboard"""
    
    # Styled header
    st.markdown("""
        <style>
        .dashboard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            padding: 2rem;
            border-radius: 16px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
        }
        
        .dashboard-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
        }
        
        .dashboard-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.95;
        }
        </style>
        <div class="dashboard-header">
            <h1>📊 Dashboard</h1>
            <p>View your analytics and key metrics</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Show data freshness for Store Manager (moved to top, only for Store Manager)
    if st.session_state.user_role == "Store Manager":
        try:
            conn = get_mysql_connection(st.session_state.config)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(run_timestamp) FROM FA25_SSC_ETL_LOG WHERE status = 'SUCCESS'")
            last_run = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            if last_run:
                last_run_str = last_run.strftime('%Y-%m-%d %H:%M:%S')
                time_diff = datetime.now() - last_run
                hours_ago = int(time_diff.total_seconds() / 3600)
                st.success(f"✅ Data Last Refreshed: {last_run_str} ({hours_ago} hours ago)")
            else:
                st.warning("⏳ Awaiting first ETL run...")
        except Exception as e:
            st.warning(f"Could not retrieve data freshness: {str(e)}")
        
        st.markdown("---")
        
        # Get dynamic metrics for Store Manager
        try:
            conn = get_mysql_connection(st.session_state.config)
            cursor = conn.cursor()
            
            # Total Sales
            cursor.execute("SELECT SUM(sales) FROM fa25_ssc_fact_sales")
            total_sales = cursor.fetchone()[0] or 0
            
            # Return Rate (returns / total orders)
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT fr.return_fact_key) as return_count,
                    COUNT(DISTINCT fs.sales_key) as total_orders
                FROM fa25_ssc_fact_sales fs
                LEFT JOIN fa25_ssc_fact_return fr ON fs.sales_key = fr.order_key
            """)
            result = cursor.fetchone()
            return_count = result[0] or 0
            total_orders = result[1] or 1
            return_rate = (return_count / total_orders * 100) if total_orders > 0 else 0
            
            # Top Product
            cursor.execute("""
                SELECT dp.product_name, SUM(fs.sales) as sales
                FROM fa25_ssc_fact_sales fs
                JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
                GROUP BY dp.product_name
                ORDER BY sales DESC
                LIMIT 1
            """)
            top_product_result = cursor.fetchone()
            top_product = top_product_result[0] if top_product_result else "N/A"
            top_product_sales = top_product_result[1] if top_product_result else 0
            # Shorten product name for display
            top_product_display = top_product[:15] + "..." if len(top_product) > 15 else top_product
            
            # Active Stores (count distinct customers/regions)
            cursor.execute("SELECT COUNT(DISTINCT region) FROM fa25_ssc_dim_customer")
            active_stores = cursor.fetchone()[0] or 0
            
            # DON'T CLOSE CONNECTION YET - we need it for graphs below
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💰 Total Sales", f"${total_sales:,.0f}", "+12% vs last month")
            with col2:
                st.metric("📦 Return Rate", f"{return_rate:.1f}%", "-0.5% vs last month")
            with col3:
                st.metric("⭐ Top Product", top_product_display, f"${top_product_sales:,.0f}")
            with col4:
                st.metric("🏢 Active Stores", active_stores, "Locations")
            
            st.markdown("---")
            
            # Add visualizations for Store Manager
            st.subheader("📈 Key Analytics")
            
            # Sales by Region
            try:
                cursor.execute("""
                    SELECT 
                        dc.region,
                        SUM(fs.sales) as total_sales
                    FROM fa25_ssc_fact_sales fs
                    JOIN fa25_ssc_dim_customer dc ON fs.customer_key = dc.customer_key
                    GROUP BY dc.region
                    ORDER BY total_sales DESC
                """)
                region_data = cursor.fetchall()
                
                if region_data:
                    df_region = pd.DataFrame(region_data, columns=['Region', 'Sales'])
                    fig_region = px.bar(
                        df_region, 
                        x='Region', 
                        y='Sales',
                        title='💎 Sales by Region',
                        labels={'Sales': 'Total Sales ($)', 'Region': 'Region'},
                        color='Sales',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig_region, width='stretch')
            except Exception as e:
                st.warning(f"Could not load sales by region: {str(e)}")
            
            # Sales by Category
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        dp.category_name,
                        SUM(fs.sales) as total_sales,
                        COUNT(*) as transactions
                    FROM fa25_ssc_fact_sales fs
                    JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
                    GROUP BY dp.category_name
                    ORDER BY total_sales DESC
                """)
                category_data = cursor.fetchall()
                cursor.close()
                
                if category_data:
                    df_category = pd.DataFrame(category_data, columns=['Category', 'Sales', 'Transactions'])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_pie = px.pie(
                            df_category,
                            values='Sales',
                            names='Category',
                            title='🍰 Sales Distribution by Category'
                        )
                        st.plotly_chart(fig_pie, width='stretch')
                    
                    with col2:
                        fig_bar = px.bar(
                            df_category,
                            x='Category',
                            y='Transactions',
                            title='📊 Transaction Count by Category',
                            labels={'Transactions': 'Count', 'Category': 'Category'},
                            color='Transactions',
                            color_continuous_scale='Blues'
                        )
                        st.plotly_chart(fig_bar, width='stretch')
            except Exception as e:
                st.warning(f"Could not load sales by category: {str(e)}")
            
            # Close connection after all graphs are done
            cursor.close()
            conn.close()
                
        except Exception as e:
            st.error(f"Error loading Store Manager dashboard: {str(e)}")
    
    # Sales Associate Dashboard (OLTP focused)
    elif st.session_state.user_role == "Sales Associate":
        try:
            conn = get_postgres_connection(st.session_state.config)
            cursor = conn.cursor()
            
            # Total Orders This Month
            cursor.execute("""
                SELECT COUNT(DISTINCT order_id) 
                FROM "FA25_SSC_ORDER"
                WHERE EXTRACT(YEAR FROM order_date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND EXTRACT(MONTH FROM order_date) = EXTRACT(MONTH FROM CURRENT_DATE)
            """)
            total_orders_month = cursor.fetchone()[0] or 0
            
            # Total Returns
            cursor.execute("""
                SELECT COUNT(DISTINCT return_id) 
                FROM "FA25_SSC_RETURN"
            """)
            total_returns = cursor.fetchone()[0] or 0
            
            # Average Order Value
            cursor.execute("""
                SELECT AVG(op.sales) 
                FROM "FA25_SSC_ORDER_PRODUCT" op
                WHERE op.sales IS NOT NULL
            """)
            avg_order_value = cursor.fetchone()[0] or 0
            
            # Return Rate
            cursor.execute("""
                SELECT COUNT(DISTINCT r.order_id)
                FROM "FA25_SSC_RETURN" r
            """)
            returned_orders = cursor.fetchone()[0] or 0
            
            # Get all orders for return rate calc
            cursor.execute("SELECT COUNT(DISTINCT order_id) FROM \"FA25_SSC_ORDER\"")
            total_all_orders = cursor.fetchone()[0] or 1
            return_rate = (returned_orders / total_all_orders * 100) if total_all_orders > 0 else 0
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📋 Orders Entered", f"{total_orders_month:,}", "this month")
            with col2:
                st.metric("↩️ Returns Processed", f"{total_returns:,}", "total")
            with col3:
                st.metric("💵 Avg Order Value", f"${avg_order_value:,.2f}", "per item")
            with col4:
                st.metric("⚠️ Return Rate", f"{return_rate:.1f}%", "quality metric")
            
            st.markdown("---")
            
            # Tabbed interface for Recent Orders and Returns
            tab1, tab2 = st.tabs(["📋 Recent Orders", "↩️ Returns Data"])
            
            # Tab 1: Recent Orders
            with tab1:
                try:
                    cursor.execute("""
                        SELECT 
                            o.order_id,
                            c.customer_name,
                            o.order_date,
                            COALESCE(SUM(op.sales), 0) as total_sales
                        FROM "FA25_SSC_ORDER" o
                        JOIN "FA25_SSC_CUSTOMER" c ON o.customer_id = c.customer_id
                        LEFT JOIN "FA25_SSC_ORDER_PRODUCT" op ON o.order_id = op.order_id
                        GROUP BY o.order_id, c.customer_name, o.order_date
                        ORDER BY o.order_date DESC
                        LIMIT 15
                    """)
                    transactions = cursor.fetchall()
                    
                    if transactions:
                        df_transactions = pd.DataFrame(
                            transactions,
                            columns=['Order ID', 'Customer', 'Date', 'Sales Amount']
                        )
                        # Format the dataframe
                        df_transactions['Date'] = pd.to_datetime(df_transactions['Date']).dt.strftime('%Y-%m-%d')
                        df_transactions['Sales Amount'] = df_transactions['Sales Amount'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
                        
                        st.dataframe(df_transactions, width='stretch', hide_index=True)
                    else:
                        st.info("No orders yet")
                except Exception as e:
                    st.warning(f"Could not load recent orders: {str(e)}")
            
            # Tab 2: Returns Data
            with tab2:
                try:
                    cursor.execute("""
                        SELECT 
                            r.return_id,
                            r.order_id,
                            c.customer_name,
                            r.return_status,
                            r.return_region
                        FROM "FA25_SSC_RETURN" r
                        JOIN "FA25_SSC_ORDER" o ON r.order_id = o.order_id
                        JOIN "FA25_SSC_CUSTOMER" c ON o.customer_id = c.customer_id
                        ORDER BY r.return_id DESC
                        LIMIT 15
                    """)
                    returns = cursor.fetchall()
                    
                    if returns:
                        df_returns = pd.DataFrame(
                            returns,
                            columns=['Return ID', 'Order ID', 'Customer', 'Status', 'Region']
                        )
                        
                        st.dataframe(df_returns, width='stretch', hide_index=True)
                    else:
                        st.info("No returns to display")
                except Exception as e:
                    st.warning(f"Could not load returns data: {str(e)}")
            
            cursor.close()
            conn.close()
                
        except Exception as e:
            st.error(f"Error loading Sales Associate dashboard: {str(e)}")
            logger.error(f"Error in Sales Associate dashboard: {e}")
    
    # Executive Dashboard placeholder
    else:
        st.info("📊 Executive dashboard coming soon - Strategic overview and ETL monitoring")


# ============================================================================
# DATA ENTRY
# ============================================================================

def data_entry_page():
    """Display data entry forms for OLTP data entry (Customer/Sales Associate role)"""
    st.markdown("""
        <style>
        .data-entry-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            padding: 2rem;
            border-radius: 16px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
        }
        
        .data-entry-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
        }
        
        .data-entry-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.95;
        }
        </style>
        <div class="data-entry-header">
            <h1>📝 Data Entry</h1>
            <p>Add new orders, products, and returns to the OLTP database</p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Order Entry", "Product Entry", "Return Entry"])
    
    # ========== TAB 1: ORDER ENTRY ==========
    with tab1:
        st.subheader("Record New Order")
        st.info("Tip: Enter customer and order details. Data will be saved to PostgreSQL OLTP immediately.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            customer_name = st.text_input("Customer Name", key="order_cust_name")
        
        with col2:
            # Get segment choices from static list (production: query from DB)
            segment = st.selectbox("Segment", ["Consumer", "Corporate", "Home Office"], key="order_segment")
            market = st.text_input("Market", key="order_market", value="US")
        
        with col3:
            region = st.selectbox("Region", 
                                 ["Central", "East", "South", "West"], 
                                 key="order_region")
            order_priority = st.selectbox("Order Priority", 
                                         ["Not Specified", "Low", "Medium", "High", "Critical"],
                                         key="order_priority")
        
        order_date = st.date_input("Order Date", key="order_date")
        
        if st.button("Record Order", key="btn_record_order", width='stretch'):
            # Validate inputs
            if not customer_name:
                st.error("Please fill all required fields (Customer Name)")
                logger.warning("Incomplete order form submission")
            else:
                try:
                    # Get PostgreSQL OLTP connection
                    conn = get_postgres_connection(st.session_state.config)
                    cursor = conn.cursor()
                    
                    # Look up customer by name
                    sql_get_customer = 'SELECT customer_id FROM "FA25_SSC_CUSTOMER" WHERE customer_name = %s'
                    cursor.execute(sql_get_customer, (customer_name,))
                    customer_result = cursor.fetchone()
                    
                    if not customer_result:
                        # Create new customer if doesn't exist
                        import uuid
                        new_customer_id = f"LP-{uuid.uuid4().hex[:12].upper()}"
                        sql_insert_customer = """
                        INSERT INTO "FA25_SSC_CUSTOMER" 
                        (customer_id, customer_name, country, state, city, postal_code, market, region, segment_id, tbl_last_dt)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """
                        cursor.execute(sql_insert_customer, 
                                      (new_customer_id, customer_name, 'United States', 'NA', 'NA', '00000', market, region, segment))
                        conn.commit()
                        customer_id = new_customer_id
                        st.info(f"✓ Created new customer: {customer_name} (ID: {new_customer_id})")
                        logger.info(f"New customer created: {customer_name} with ID {new_customer_id}")
                    else:
                        customer_id = customer_result[0]
                    
                    # ===== VALIDATION: Check customer is valid =====
                    sql_validate_customer = """
                    SELECT is_valid, customer_name, error_message 
                    FROM validate_customer(%s)
                    """
                    cursor.execute(sql_validate_customer, (customer_id,))
                    val_customer = cursor.fetchone()
                    
                    if val_customer:
                        is_valid, valid_cust_name, error_msg = val_customer
                        if not is_valid:
                            st.error(f"❌ Customer validation failed: {error_msg}")
                            logger.warning(f"Customer validation failed for {customer_id}: {error_msg}")
                            cursor.close()
                            release_postgres_connection(conn)
                            raise Exception(f"Customer validation failed: {error_msg}")
                    
                    # Insert into ORDER (for both existing and new customers)
                    # Generate order_id (format: REGION-YYYY-XXNNNNNN-YYYYY)
                    # Example: IN-2015-BS1136558-42369
                    
                    # Map region names to 2-letter codes
                    region_codes = {
                        "Central": "CE",
                        "East": "EA",
                        "South": "SO",
                        "West": "WE"
                    }
                    region_code = region_codes.get(region, "XX")
                    order_year = order_date.strftime("%Y")
                    
                    # Generate code using customer initials + random 6-digit number
                    customer_initials = ''.join([word[0].upper() for word in customer_name.split() if word])[:2]
                    if len(customer_initials) < 2:
                        customer_initials = customer_initials.ljust(2, 'X')
                    
                    random_number = random.randint(100000, 999999)
                    code = f"{customer_initials}{random_number}"
                    random_suffix = random.randint(10000, 99999)
                    generated_order_id = f"{region_code}-{order_year}-{code}-{random_suffix}"
                    
                    sql_insert_order = """
                    INSERT INTO "FA25_SSC_ORDER" 
                    (order_id, customer_id, order_date, order_priority)
                    VALUES (%s, %s, %s, %s)
                    RETURNING row_id
                    """
                    cursor.execute(sql_insert_order, (generated_order_id, customer_id, order_date, order_priority))
                    row_result = cursor.fetchone()
                    row_id = row_result[0] if row_result else None
                    conn.commit()
                    
                    cursor.close()
                    release_postgres_connection(conn)
                    
                    st.success("Order recorded successfully!")
                    st.success(f"Order ID: {generated_order_id} | Customer ID: {customer_id} | Date: {order_date}")
                    logger.info(f"Order recorded: OrderID={generated_order_id}, CustomerID={customer_id}, Date={order_date}")
                        
                except Exception as e:
                    st.error(f"Error saving order to database: {str(e)}")
                    logger.error(f"Error recording order: {e}")
    
    # ========== TAB 2: PRODUCT ENTRY (Order-Product Junction) ==========
    with tab2:
        st.subheader("Add Product to Order")
        st.info("Tip: Link products to an existing order with quantity, pricing, and shipping details.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            order_id_lookup = st.text_input("Order ID", key="prod_order_id")
            product_name = st.text_input("Product Name", key="prod_name")
        
        with col2:
            # Get category choices (production: query from DB)
            category = st.selectbox("Category", 
                                   ["Technology", "Furniture", "Office Supplies"],
                                   key="prod_category")
            quantity = st.number_input("Quantity", min_value=1, value=1, key="prod_qty")
        
        with col3:
            sales = st.number_input("Sales Amount ($)", min_value=0.0, value=0.0, key="prod_sales")
            discount = st.number_input("Discount ($)", min_value=0.0, value=0.0, key="prod_discount")
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            shipping_cost = st.number_input("Shipping Cost ($)", min_value=0.0, value=0.0, key="prod_shipping")
            ship_mode = st.selectbox("Ship Mode", 
                                    ["Standard Class", "First Class", "Second Class", "Same Day"],
                                    key="prod_ship_mode")
        
        with col5:
            ship_date = st.date_input("Ship Date", key="prod_ship_date")
        
        with col6:
            subcategory = st.selectbox("Subcategory", 
                                      ["Accessories", "Appliances", "Art", "Binders", "Bookcases", 
                                       "Chairs", "Copiers", "Decorative", "Desk", "Fasteners", 
                                       "Furnishings", "Labels", "Machines", "Paper", "Phones", 
                                       "Supplies", "Tables"],
                                      key="prod_subcategory")
        
        if st.button("Add Product to Order", key="btn_add_product", width='stretch'):
            # Validate inputs
            order_id_lookup = order_id_lookup.strip() if order_id_lookup else ""
            product_name = product_name.strip() if product_name else ""
            
            if not order_id_lookup or not product_name or sales == 0:
                st.error("Please fill all required fields (Order ID, Product Name, Sales Amount)")
                logger.warning("Incomplete product entry form submission")
            else:
                try:
                    # Get PostgreSQL OLTP connection
                    conn = get_postgres_connection(st.session_state.config)
                    cursor = conn.cursor()
                    
                    # Check if order exists
                    sql_check_order = 'SELECT order_id FROM "FA25_SSC_ORDER" WHERE order_id = %s'
                    cursor.execute(sql_check_order, (order_id_lookup,))
                    order_result = cursor.fetchone()
                    
                    if not order_result:
                        st.error(f"Order ID {order_id_lookup} not found")
                        logger.warning(f"Order {order_id_lookup} not found for product entry")
                    else:
                        # ===== VALIDATION: Check order is valid =====
                        sql_validate_order = """
                        SELECT is_valid, customer_id, customer_name, product_count, error_message 
                        FROM validate_order(%s)
                        """
                        cursor.execute(sql_validate_order, (order_id_lookup,))
                        val_order = cursor.fetchone()
                        
                        if val_order:
                            is_valid, cust_id, cust_name, prod_count, error_msg = val_order
                            if not is_valid:
                                st.error(f"❌ Order validation failed: {error_msg}")
                                logger.warning(f"Order validation failed for {order_id_lookup}: {error_msg}")
                                raise Exception(f"Order validation failed: {error_msg}")
                        
                        # Get or create product
                        sql_check_product = 'SELECT product_id FROM "FA25_SSC_PRODUCT" WHERE product_name = %s'
                        cursor.execute(sql_check_product, (product_name,))
                        prod_result = cursor.fetchone()
                        
                        if prod_result:
                            product_id = prod_result[0]
                        else:
                            # Create new product with generated product_id
                            # Format: CAT-SUB-XXXXX (e.g., TEC-AP-12345)
                            cat_prefix = subcategory[:2].upper() if len(subcategory) >= 2 else "XX"
                            random_suffix = random.randint(10000, 99999)
                            product_id = f"{cat_prefix}-{random_suffix}"
                            
                            sql_insert_product = """
                            INSERT INTO "FA25_SSC_PRODUCT" 
                            (product_id, product_name, subcategory_id)
                            VALUES (%s, %s, %s)
                            """
                            cursor.execute(sql_insert_product, (product_id, product_name, subcategory))
                            conn.commit()
                        
                        if product_id:
                            # Insert into ORDER_PRODUCT junction table
                            profit = sales - (discount / 100 * sales) - shipping_cost
                            sql_insert_order_product = """
                            INSERT INTO "FA25_SSC_ORDER_PRODUCT" 
                            (order_id, product_id, quantity, sales, discount, profit, 
                             shipping_cost, ship_mode, ship_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            cursor.execute(sql_insert_order_product, (
                                order_id_lookup, product_id, quantity, sales, 
                                discount / 100 * sales, profit, shipping_cost, ship_mode, ship_date
                            ))
                            conn.commit()
                            
                            st.success("Product added to order successfully!")
                            st.success(f"Order: {order_id_lookup} | Product: {product_name} | Qty: {quantity} | Amount: ${sales}")
                            logger.info(f"Product added: OrderID={order_id_lookup}, Product={product_name}, Qty={quantity}")
                        else:
                            st.error("Could not create product")
                            logger.error("Failed to create product")
                    
                    cursor.close()
                    release_postgres_connection(conn)
                    
                except Exception as e:
                    st.error(f"Error saving product to order: {str(e)}")
                    logger.error(f"Error adding product to order: {e}")
    
    # ========== TAB 3: RETURN ENTRY ==========
    with tab3:
        st.subheader("Record Return")
        st.info("Tip: Link a sale (order) to a return with reason and status. Data will be saved to PostgreSQL OLTP immediately.")
        
        col1, col2 = st.columns(2)
        with col1:
            return_order_id = st.text_input("Order ID / Sale ID", key="return_order_id")
            return_reason = st.selectbox("Return Reason", 
                                         ["Defective", "Wrong Size", "Changed Mind", "Damaged", "Wrong Item", "Other"],
                                         key="return_reason")
            return_date = st.date_input("Return Date", key="return_date")
        
        with col2:
            return_returned = st.selectbox("Item Returned", 
                                        ["Yes", "No"], 
                                        key="return_returned")
            return_region = st.selectbox("Return Region",
                                        ["Central", "East", "South", "West"],
                                        key="return_region")
        
        if st.button("Record Return", key="btn_record_return", width='stretch'):
            # Validate inputs
            if not return_order_id:
                st.error("Please enter Order ID / Sale ID")
                logger.warning("Incomplete return form submission")
            else:
                try:
                    # Get PostgreSQL OLTP connection
                    conn = get_postgres_connection(st.session_state.config)
                    cursor = conn.cursor()
                    
                    # Strip whitespace from order ID
                    return_order_id = return_order_id.strip() if return_order_id else ""
                    
                    # Check if order exists
                    sql_check_order = 'SELECT order_id FROM "FA25_SSC_ORDER" WHERE order_id = %s'
                    cursor.execute(sql_check_order, (return_order_id,))
                    order_result = cursor.fetchone()
                    
                    if not order_result:
                        st.error(f"Order ID {return_order_id} not found")
                        logger.warning(f"Order {return_order_id} not found for return entry")
                    else:
                        # ===== VALIDATION: Check order is valid =====
                        sql_validate_order = """
                        SELECT is_valid, customer_id, customer_name, product_count, error_message 
                        FROM validate_order(%s)
                        """
                        cursor.execute(sql_validate_order, (return_order_id,))
                        val_order = cursor.fetchone()
                        
                        if val_order:
                            is_valid, cust_id, cust_name, prod_count, error_msg = val_order
                            if not is_valid:
                                st.error(f" Order validation failed: {error_msg}")
                                logger.warning(f"Order validation failed for {return_order_id}: {error_msg}")
                                raise Exception(f"Order validation failed: {error_msg}")
                        
                        # Insert into RETURN with proper schema columns
                        # Map form fields to database columns:
                        # Item Returned (Yes/No) -> return_status
                        # Return Region -> return_region
                        # Order ID -> order_id (from return_id form field)
                        # tbl_last_dt auto-set by NOW() for CDC tracking
                        
                        import uuid
                        return_id = f"RET-{uuid.uuid4().hex[:8].upper()}"
                        
                        sql_insert_return = """
                        INSERT INTO "FA25_SSC_RETURN" 
                        (return_id, return_status, order_id, return_region, tbl_last_dt)
                        VALUES (%s, %s, %s, %s, NOW())
                        """
                        cursor.execute(sql_insert_return, (return_id, return_returned, return_order_id, return_region))
                        conn.commit()
                        
                        cursor.close()
                        release_postgres_connection(conn)
                        
                        st.success("Return recorded successfully!")
                        st.success(f"Order ID: {return_order_id} | Reason: {return_reason} | Returned: {return_returned} | Region: {return_region}")
                        logger.info(f"Return recorded: OrderID={return_order_id}, Reason={return_reason}, Returned={return_returned}, Region={return_region}")
                    
                except Exception as e:
                    st.error(f"Error saving return to database: {str(e)}")
                    logger.error(f"Error recording return: {e}")


# ============================================================================
# CHAT INTERFACE
# ============================================================================

def chat_page():
    """Display chat interface for LLM queries - ChatGPT-style UI with vibrant design"""
    
    # Apply vibrant ChatGPT-like styling
    st.markdown("""
        <style>
        /* Chat header - vibrant and eye-catching */
        .chat-header {
            text-align: center;
            padding: 1.5rem;
            margin-bottom: 0.3rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            border-radius: 20px;
            box-shadow: 0 12px 40px rgba(102, 126, 234, 0.35);
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .chat-header h1 {
            margin: 0;
            font-size: 2.2rem;
            font-weight: 800;
            color: white;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .chat-header p {
            margin: 0.5rem 0 0 0;
            color: rgba(255, 255, 255, 0.95);
            font-size: 0.95rem;
            font-weight: 500;
        }
        
        /* Chat messages container */
        .chat-container {
            overflow-y: auto;
            padding: 0;
            background: transparent;
            margin: 0;
            scroll-behavior: smooth;
        }
        
        /* Chat messages styling - ChatGPT style */
        .user-msg {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .user-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.9rem 1.2rem;
            border-radius: 16px;
            max-width: 65%;
            word-wrap: break-word;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.35);
            animation: slideInRight 0.3s ease-out;
            font-weight: 500;
            line-height: 1.3;
            font-size: 0.95rem;
        }
        
        .ai-msg {
            display: flex;
            justify-content: flex-start;
            margin-bottom: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .ai-bubble {
            background: transparent;
            color: #e0e0e0;
            padding: 0;
            border-radius: 0;
            max-width: 100%;
            word-wrap: break-word;
            box-shadow: none;
            animation: slideInLeft 0.3s ease-out;
            line-height: 1.7;
            border: none;
            font-size: 0.95rem;
        }
        
        .ai-bubble p {
            margin-bottom: 0.8rem;
            color: #e0e0e0;
        }
        
        .ai-bubble strong {
            color: #a0b0ff;
            font-weight: 600;
        }
        
        .ai-bubble h3 {
            color: #a0b0ff;
            font-size: 1.1rem;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .ai-bubble ul, .ai-bubble ol {
            margin: 0.5rem 0 0.8rem 1.2rem;
            padding-left: 0.5rem;
            color: #e0e0e0;
        }
        
        .ai-bubble li {
            margin-bottom: 0.4rem;
            line-height: 1.6;
        }
        
        .ai-bubble table {
            border-collapse: collapse;
            margin: 1rem 0;
            width: 100%;
        }
        
        .ai-bubble th {
            background: rgba(102, 126, 234, 0.2);
            color: #a0b0ff;
            padding: 0.5rem;
            text-align: left;
            border: 1px solid rgba(160, 176, 255, 0.3);
        }
        
        .ai-bubble td {
            padding: 0.5rem;
            border: 1px solid rgba(160, 176, 255, 0.2);
            color: #e0e0e0;
        }
        
        .ai-bubble tr:nth-child(even) {
            background: rgba(255, 255, 255, 0.03);
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        /* Input area - plain, no border */
        .input-container {
            background: transparent;
            padding: 0;
            transition: all 0.3s ease;
        }
        
        /* Spacer divider - thin white line */
        .spacer-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            margin: 1rem 0;
        }
        
        /* Example questions - shown when no chat history */
        .examples-section {
            padding: 0 1.5rem;
            margin-bottom: 1rem;
        }
        
        .example-btn {
            background: linear-gradient(135deg, #ffffff 0%, #f9f9ff 100%);
            border: 2px solid #e0e0ff;
            padding: 0.9rem;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            font-weight: 600;
            font-size: 0.85rem;
            color: #333;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
        }
        
        .example-btn:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.35);
            transform: translateY(-3px);
        }
        
        /* Response styling - NO background */
        .response-section {
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
            font-size: 0.95rem;
        }
        
        .response-section p {
            line-height: 1.6;
            margin-bottom: 0.8rem;
        }
        
        /* Minimal spacing */
        .spacer-divider {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header - sticky at top
    st.markdown("""
        <div class="chat-header">
            <h1>💬 Ask Questions About Your Data</h1>
            <p>Get instant insights</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Chat history display - ChatGPT style
    if st.session_state.chat_history:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                    <div class="user-msg">
                        <div class="user-bubble">{message['content']}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # AI response - use container for better formatting
                st.markdown('<div class="ai-msg"><div class="ai-bubble">', unsafe_allow_html=True)
                st.markdown(message['content'])  # Render markdown properly
                st.markdown('</div></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # No extra spacing when no chat
        pass
    
    # Input area - always visible
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    # Initialize input state key if not exists
    if "chat_input_key" not in st.session_state:
        st.session_state.chat_input_key = 0
    
    user_input = st.text_area(
        "Message", 
        placeholder="Ask a question about your data...",
        height=80,
        label_visibility="collapsed",
        key=f"chat_input_{st.session_state.chat_input_key}"
    )
    
    col1, col2 = st.columns([8, 1])
    
    with col1:
        send_button = st.button("🚀 Send", width='stretch', type="primary")
    
    with col2:
        if st.button("🗑️", help="Clear chat history", width='stretch'):
            st.session_state.chat_history = []
            st.session_state.conversation_history = []
            st.session_state.chat_input_key += 1  # Clear input by changing key
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Example questions - shown ONLY when no chat history
    if not st.session_state.chat_history:
        st.markdown('<div class="examples-section">', unsafe_allow_html=True)
        
        st.markdown("<h4 style='text-align: center; color: #667eea; margin: 1rem 0 0.8rem 0;'>💡 Try These</h4>", unsafe_allow_html=True)
        
        examples = [
            ("📈 Return Rate", "What's the return rate by store?"),
            ("⭐ Top Products", "Show me the top 5 selling products"),
            ("📊 Sales Trends", "What are the sales trends over time?")
        ]
        
        cols = st.columns(3)
        for idx, (icon_label, example) in enumerate(examples):
            with cols[idx]:
                if st.button(f"{icon_label}", key=f"example_{idx}", width='stretch'):
                    st.session_state.chat_history.append({"role": "user", "content": example})
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Process user input
    if send_button and user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_input_key += 1  # Clear input by incrementing key
        
        logger.info("="*80)
        logger.info(f"USER QUESTION: {user_input}")
        logger.info(f"User Role: {st.session_state.user_role}")
        logger.info(f"Conversation Context: {len(st.session_state.conversation_history)} previous turns")
        logger.info("="*80)
        
        with st.spinner("🔄 Processing your question..."):
            try:
                # Call LLM RAG pipeline WITH conversation history and user role for PII masking
                result = process_question(
                    user_input, 
                    st.session_state.config,
                    conversation_history=st.session_state.conversation_history,
                    user_role=st.session_state.user_role
                )
                
                if result["error"]:
                    st.error(f"❌ Error: {result['error']}")
                    logger.error(f"Error processing question: {result['error']}")
                else:
                    # Display natural language response - clean format
                    st.markdown(result['natural_response'])
                    
                    # Optional: Advanced/Debug section
                    with st.expander("📥 View Raw Data & Details"):
                        
                        # Toggle for viewing original names (PII option for Store Manager)
                        show_original = False
                        if st.session_state.user_role == "Store Manager" and result.get("data_original") is not None:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.warning("🔐 Customer names and postal codes are masked for privacy compliance")
                            with col2:
                                show_original = st.checkbox("Show Original", value=False, key=f"pii_toggle_{id(result)}")
                        
                        # Display appropriate dataframe
                        if result["data"] is not None and not result["data"].empty:
                            st.markdown("**Data Table:**")
                            if show_original and result.get("data_original") is not None:
                                st.dataframe(result["data_original"], width='stretch')
                                st.error("⚠️ WARNING: Viewing unmasked customer data. Handle with care.")
                            else:
                                st.dataframe(result["data"], width='stretch')
                            
                            # Download button
                            csv = result["data"].to_csv(index=False)
                            st.download_button(
                                label="📥 Download as CSV",
                                data=csv,
                                file_name=f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                width='stretch'
                            )
                        else:
                            st.info("No data returned for this query")
                    
                    st.session_state.chat_history.append(
                        {"role": "ai", "content": result["natural_response"]}
                    )
                    
                    # Store conversation turn for next query (for multi-turn context)
                    if result["conversation_turn"]:
                        st.session_state.conversation_history.append(result["conversation_turn"])
                        logger.info(f"Conversation history updated: {len(st.session_state.conversation_history)} turns")
                    
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"Error in chat interface: {e}")
    
    # Enhanced sidebar context
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🎯 Chat Info")
        
        # Stats cards
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💬 Messages", len(st.session_state.chat_history))
        with col2:
            st.metric("🔄 Context", len(st.session_state.conversation_history))
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info("💡 Ask follow-up questions for multi-turn conversations. The AI remembers context!")


# ============================================================================
# PARTITION MONITORING (EXECUTIVE ONLY)
# ============================================================================

def partition_monitoring_page():
    """Executive partition monitoring dashboard"""
    
    # Consistent header styling
    st.markdown("""
        <style>
            .partition-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                padding: 2rem;
                border-radius: 16px;
                color: white;
                margin-bottom: 1.5rem;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
            }
            
            .partition-header h1 {
                margin: 0;
                font-size: 2rem;
                font-weight: 800;
            }
            
            .partition-header p {
                margin: 0.5rem 0 0 0;
                opacity: 0.95;
            }
            
            .partition-card-order {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                padding: 2rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            
            .partition-card-return {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                border: none;
                padding: 2rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                box-shadow: 0 8px 25px rgba(240, 91, 108, 0.3);
            }
            
            .partition-card-order h3,
            .partition-card-return h3 {
                margin: 0 0 1.5rem 0;
                color: white;
                font-size: 1.2rem;
                font-weight: 700;
            }
            
            .metric-row {
                display: flex;
                gap: 1rem;
                margin-bottom: 1rem;
            }
            
            .metric-item {
                flex: 1;
                background: rgba(255, 255, 255, 0.15);
                padding: 1.2rem;
                border-radius: 10px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .metric-item .metric-value {
                font-size: 2rem;
                font-weight: 800;
                color: white;
                margin: 0.5rem 0 0 0;
            }
            
            .metric-item .metric-label {
                font-size: 0.8rem;
                color: rgba(255, 255, 255, 0.8);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin: 0;
            }
        </style>
        <div class="partition-header">
            <h1>📊 Database Partition Monitoring</h1>
            <p>Real-time visibility into table partitioning and data distribution</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Get database connection
    conn = get_postgres_connection(st.session_state.config)
    if not conn:
        st.error("Unable to connect to PostgreSQL database")
        return
    
    try:
        with conn.cursor() as cur:
            # Orders count
            cur.execute("SELECT COUNT(*) FROM FA25_SSC_ORDER_PARTITIONED;")
            orders_count = cur.fetchone()[0]
            
            # Returns count
            cur.execute("SELECT COUNT(*) FROM FA25_SSC_RETURN_PARTITIONED;")
            returns_count = cur.fetchone()[0]
            
            # Partition counts
            cur.execute("SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE 'fa25_ssc_order_p_%' AND schemaname = 'public';")
            order_parts = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM pg_tables WHERE tablename LIKE 'fa25_ssc_return_p_%' AND schemaname = 'public';")
            return_parts = cur.fetchone()[0]
            
            # Get partition stats for the cards
            cur.execute("""
                SELECT tablename,
                       ROUND(pg_total_relation_size('public.'||tablename)/1024.0/1024.0, 2) as size_mb,
                       COALESCE(n_live_tup, 0) as row_count
                FROM pg_tables t
                LEFT JOIN pg_stat_user_tables s ON s.relname = t.tablename
                WHERE (tablename LIKE 'fa25_ssc_order_p_%' OR tablename LIKE 'fa25_ssc_return_p_%')
                  AND t.schemaname = 'public'
                ORDER BY tablename;
            """)
            partition_stats = pd.DataFrame(cur.fetchall(), columns=['Partition', 'Size (MB)', 'Rows'])
        
        # Separate data
        order_parts_df = partition_stats[partition_stats['Partition'].str.contains('fa25_ssc_order_p_')]
        return_parts_df = partition_stats[partition_stats['Partition'].str.contains('fa25_ssc_return_p_')]
        
        # Calculate summary stats
        order_total_size = order_parts_df['Size (MB)'].sum() if not order_parts_df.empty else 0
        order_total_rows = order_parts_df['Rows'].sum() if not order_parts_df.empty else 0
        order_count = len(order_parts_df) if not order_parts_df.empty else 0
        
        return_total_size = return_parts_df['Size (MB)'].sum() if not return_parts_df.empty else 0
        return_total_rows = return_parts_df['Rows'].sum() if not return_parts_df.empty else 0
        return_count = len(return_parts_df) if not return_parts_df.empty else 0
        
        # Gradient Cards Section (replaces key metrics)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div class="partition-card-order">
                    <h3>📦 Order Partitions</h3>
                    <div class="metric-row">
                        <div class="metric-item">
                            <p class="metric-label">Total Orders</p>
                            <div class="metric-value">""" + f"{orders_count:,}" + """</div>
                        </div>
                        <div class="metric-item">
                            <p class="metric-label">Total Partitions</p>
                            <div class="metric-value">""" + str(order_count) + """</div>
                        </div>
                        <div class="metric-item">
                            <p class="metric-label">Total Size</p>
                            <div class="metric-value">""" + f"{order_total_size:.2f}" + """ MB</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div class="partition-card-return">
                    <h3>↩️ Return Partitions</h3>
                    <div class="metric-row">
                        <div class="metric-item">
                            <p class="metric-label">Total Returns</p>
                            <div class="metric-value">""" + f"{returns_count:,}" + """</div>
                        </div>
                        <div class="metric-item">
                            <p class="metric-label">Total Partitions</p>
                            <div class="metric-value">""" + str(return_count) + """</div>
                        </div>
                        <div class="metric-item">
                            <p class="metric-label">Total Size</p>
                            <div class="metric-value">""" + f"{return_total_size:.2f}" + """ MB</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Single unified graph - Data Distribution by Year
        st.subheader("📈 Data Distribution (Orders vs Returns by Year)")
        
        with conn.cursor() as cur:
            # Orders by year
            cur.execute("""
                SELECT EXTRACT(YEAR FROM ORDER_DATE)::INT as year, COUNT(*) as orders
                FROM FA25_SSC_ORDER_PARTITIONED
                GROUP BY year ORDER BY year;
            """)
            orders_yearly = pd.DataFrame(cur.fetchall(), columns=['year', 'orders'])
            
            # Returns by year
            cur.execute("""
                SELECT EXTRACT(YEAR FROM RETURN_DATE)::INT as year, COUNT(*) as returns
                FROM FA25_SSC_RETURN_PARTITIONED
                GROUP BY year ORDER BY year;
            """)
            returns_yearly = pd.DataFrame(cur.fetchall(), columns=['year', 'returns'])
        
        # Merge data
        combined_yearly = pd.merge(orders_yearly, returns_yearly, on='year', how='outer').fillna(0)
        
        if not combined_yearly.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=combined_yearly['year'], y=combined_yearly['orders'], name='Orders', marker_color='#667eea'))
            fig.add_trace(go.Bar(x=combined_yearly['year'], y=combined_yearly['returns'], name='Returns', marker_color='#f093fb'))
            fig.update_layout(
                title='Orders & Returns by Year',
                xaxis_title='Year',
                yaxis_title='Count',
                barmode='group',
                height=400,
                showlegend=True
            )
            st.plotly_chart(fig, width='stretch')
        
        st.markdown("---")
        
        # Partition Details Tables with Tabs
        st.subheader("📋 Detailed Partition Information")
        
        tab1, tab2 = st.tabs(["📦 Order Partitions", "↩️ Return Partitions"])
        
        with tab1:
            if not order_parts_df.empty:
                st.dataframe(order_parts_df, width='stretch', hide_index=True)
            else:
                st.info("No order partitions found")
        
        with tab2:
            if not return_parts_df.empty:
                st.dataframe(return_parts_df, width='stretch', hide_index=True)
            else:
                st.info("No return partitions found")
        
    except Exception as e:
        st.error(f"Error loading partition data: {e}")
        logger.error(f"Partition monitoring error: {e}")
    finally:
        release_postgres_connection(conn)


# ============================================================================
# ============================================================================
# ETL MANAGEMENT
# ============================================================================

def etl_management_page():
    """ETL Pipeline management and monitoring for Executives"""
    st.markdown("""
        <style>
        .etl-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            padding: 2rem;
            border-radius: 16px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
        }
        
        .etl-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
        }
        
        .etl-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.95;
        }
        </style>
        <div class="etl-header">
            <h1>⚙️ ETL Management</h1>
            <p>Monitor and execute ETL pipeline to sync OLTP data to Data Warehouse</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Overview Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🟢 Pipeline Status", "Ready", "All Systems Go")
    
    with col2:
        try:
            conn = get_mysql_connection(st.session_state.config)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM FA25_SSC_ETL_LOG WHERE status = 'SUCCESS'")
            success_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            st.metric("✅ Successful Runs", success_count)
        except:
            st.metric("✅ Successful Runs", "N/A")
    
    with col3:
        try:
            conn = get_mysql_connection(st.session_state.config)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(run_timestamp) FROM FA25_SSC_ETL_LOG WHERE status = 'SUCCESS'")
            last_run = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            last_run_str = last_run.strftime('%Y-%m-%d %H:%M:%S') if last_run else "Never"
            st.metric("⏱️ Last Run", last_run_str)
        except:
            st.metric("⏱️ Last Run", "N/A")
    
    st.markdown("---")
    
    # Run ETL Button (prominent)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Run ETL Now", key="run_etl_button", width='stretch'):
            st.session_state.etl_running = True
    
    # ETL Progress Display
    if st.session_state.get("etl_running", False):
        with st.spinner("ETL Pipeline Running... Please wait"):
            progress_bar = st.progress(0)
            status_container = st.empty()
            
            try:
                # Update status
                status_container.info("Starting ETL pipeline...")
                progress_bar.progress(10)
                
                # Run ETL
                status_container.info("Running ETL (Extract → Transform → Load)...")
                progress_bar.progress(50)
                
                success = run_etl_pipeline(st.session_state.config)
                
                progress_bar.progress(100)
                
                if success:
                    status_container.success("✅ ETL Pipeline completed successfully!")
                    st.balloons()
                    logger.info("ETL pipeline executed successfully from Streamlit")
                    st.session_state.etl_running = False
                    st.session_state.etl_last_status = "SUCCESS"
                else:
                    status_container.error("❌ ETL Pipeline failed - check logs for details")
                    logger.error("ETL pipeline failed from Streamlit")
                    st.session_state.etl_running = False
                    st.session_state.etl_last_status = "FAILED"
                
                # Small delay for visual effect
                import time
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                status_container.error(f"❌ Error running ETL: {str(e)}")
                logger.error(f"Error running ETL from Streamlit: {e}")
                st.session_state.etl_running = False
    
    st.markdown("---")
    
    # ETL Run History
    st.subheader("📊 ETL Run History")
    
    try:
        conn = get_mysql_connection(st.session_state.config)
        cursor = conn.cursor()
        
        # Fetch latest ETL runs
        cursor.execute("""
            SELECT run_id, run_timestamp, status, records_extracted 
            FROM FA25_SSC_ETL_LOG 
            ORDER BY run_timestamp DESC 
            LIMIT 10
        """)
        
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if logs:
            # Create DataFrame for display
            log_data = []
            for log in logs:
                log_data.append({
                    "Run ID": log[0],
                    "Timestamp": log[1].strftime('%Y-%m-%d %H:%M:%S'),
                    "Status": log[2],
                    "Records Extracted": log[3]
                })
            
            df_logs = pd.DataFrame(log_data)
            
            # Color code status
            def color_status(val):
                if val == 'SUCCESS':
                    return 'background-color: #2d5016; color: #ffffff'
                else:
                    return 'background-color: #8b3a3a; color: #ffffff'
            
            st.dataframe(
                df_logs.style.applymap(color_status, subset=['Status']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No ETL runs yet. Click 'Run ETL Now' to start.")
    
    except Exception as e:
        st.warning(f"Could not fetch ETL logs: {str(e)}")
        logger.error(f"Error fetching ETL logs: {e}")
    
    st.markdown("---")
    
    # CDC Status (clean and concise)
    st.subheader("🔄 Change Data Capture Status")
    
    try:
        conn = get_mysql_connection(st.session_state.config)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(run_timestamp) FROM FA25_SSC_ETL_LOG WHERE status = 'SUCCESS'")
        last_timestamp = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        if last_timestamp:
            # Display in a clean card format
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Last Incremental Load**: {last_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            with col2:
                st.success(f"**Next ETL will extract**: Records changed after {last_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.warning("**First Run**: Next ETL will perform a FULL LOAD of all OLTP records")
    except:
        st.info("Could not retrieve CDC information")


# ============================================================================
# SETTINGS
# ============================================================================

def settings_page():
    """Display settings page with modern UI"""
    
    # Apply modern styling
    st.markdown("""
        <style>
        /* Settings header */
        .settings-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 16px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
        }
        
        .settings-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
        }
        
        .settings-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.95;
        }
        
        /* Settings sections */
        .settings-section {
            background: transparent;
            padding: 2rem 0;
            border-radius: 0;
            border: none;
            margin-bottom: 1.5rem;
            box-shadow: none;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .settings-section h2 {
            color: #333;
            font-size: 1.3rem;
            margin-top: 0;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .settings-section h3 {
            color: #555;
            font-size: 1rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        /* Input styling */
        .settings-input {
            background: white;
            border: 1px solid #e0e0e0;
            padding: 0.8rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        /* Button styling */
        .settings-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .settings-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.35);
        }
        
        /* Messages */
        .success-msg {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .error-msg {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div class="settings-header">
            <h1>⚙️ Settings</h1>
            <p>Manage your account security and preferences</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Password Change Section
    st.markdown('<div class="settings-section">', unsafe_allow_html=True)
    st.markdown("<h2>🔐 Change Password</h2>", unsafe_allow_html=True)
    
    st.markdown("**Step 1: Verify your identity with security questions**")
    
    # Initialize security questions in session state (only once)
    if "change_pwd_security_questions" not in st.session_state:
        st.session_state.change_pwd_security_questions = get_security_questions_for_user(st.session_state.username, 3)
    
    security_questions = st.session_state.change_pwd_security_questions
    stored_answers = None
    change_pwd_conn = None
    
    try:
        # Get connection to user's database
        if st.session_state.user_role == "Sales Associate":
            change_pwd_conn = get_postgres_connection(st.session_state.config)
        else:
            change_pwd_conn = get_mysql_connection(st.session_state.config)
        
        stored_answers = get_security_answers_db(st.session_state.username, st.session_state.user_role, change_pwd_conn)
        
        if not stored_answers:
            st.error("No security questions found for your account")
        else:
            change_sq_answers = {}
            
            for idx, (q_index, question) in enumerate(security_questions):
                key_name = f"change_pwd_answer_q{q_index}"
                answer_value = st.text_input(
                    f"Q{idx+1}: {question}",
                    key=key_name,
                    placeholder="Your answer"
                )
                if answer_value:
                    change_sq_answers[q_index] = answer_value
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("✅ Verify & Continue", width='stretch', key="verify_for_change_pwd", type="primary"):
                    if len(change_sq_answers) < 3:
                        st.error("⚠️ Please answer all 3 questions")
                    else:
                        # Verify answers (2/3 correct) from database
                        correct_count = 0
                        for q_idx, user_answer in change_sq_answers.items():
                            if str(q_idx) in stored_answers:
                                # Verify hashed answer
                                if verify_password(user_answer, stored_answers[str(q_idx)]):
                                    correct_count += 1
                        
                        if correct_count >= 2:
                            st.session_state.change_pwd_verified = True
                            st.success("✅ Security questions verified!")
                        else:
                            st.error("❌ Incorrect answers (need 2 out of 3 correct). Please try again.")
                            logger.warning(f"Failed security question verification for: {st.session_state.username}")
            
            # Show password change form if verified
            if st.session_state.get("change_pwd_verified"):
                st.markdown("---")
                st.markdown("**Step 2: Enter your new password**")
                
                new_pwd = st.text_input(
                    "🔑 New Password",
                    type="password",
                    key="change_new_pwd",
                    placeholder="Enter new password"
                )
                
                # Real-time validation as user types
                password_valid = True
                if new_pwd:
                    # Check for password reuse first
                    is_reused = False
                    if stored_answers:
                        try:
                            history_result = check_password_history(
                                st.session_state.username,
                                st.session_state.user_role,
                                new_pwd,
                                change_pwd_conn
                            )
                            if history_result.get('is_reused'):
                                st.error("❌ This password was recently used. For security, please choose a different password")
                                is_reused = True
                                password_valid = False
                        except Exception as e:
                            logger.debug(f"History check error: {e}")
                    
                    # Only show strength if password is not reused
                    if not is_reused:
                        strength = validate_password_strength(new_pwd)
                        if strength['strength'] == 'strong':
                            st.success(f"✅ Password Strength: **STRONG**")
                        else:
                            st.error(f"❌ {', '.join(strength['requirements'])}")
                            password_valid = False
                
                confirm_pwd = st.text_input(
                    "🔑 Confirm Password",
                    type="password",
                    key="change_confirm_pwd",
                    placeholder="Confirm new password"
                )
                
                # Show mismatch error in real-time if both fields have content
                if new_pwd and confirm_pwd and new_pwd != confirm_pwd:
                    st.error("❌ Passwords do not match")
                    password_valid = False
                
                st.markdown("")
                
                # Only enable button if new password is valid
                if st.button("🔄 Update Password", width='stretch', key="update_pwd_btn", disabled=not password_valid or not new_pwd or not confirm_pwd):
                    if not new_pwd or not confirm_pwd:
                        st.error("⚠️ Please enter passwords")
                    elif new_pwd != confirm_pwd:
                        st.error("❌ Passwords do not match")
                    elif not password_valid:
                        st.error("❌ Please fix password issues above")
                    else:
                        # Update password in database (already verified with security questions)
                        pwd_result = reset_password_db(
                            st.session_state.username,
                            st.session_state.user_role,
                            new_pwd,
                            change_pwd_conn
                        )
                        
                        if pwd_result['success']:
                            st.success("✅ Password updated successfully!")
                            st.info("Your password has been changed")
                            st.session_state.change_pwd_verified = False
                            # Clear the stored questions so they'll be regenerated on next visit
                            if "change_pwd_security_questions" in st.session_state:
                                del st.session_state.change_pwd_security_questions
                            logger.info(f"Password changed for user: {st.session_state.username}")
                        else:
                            st.error(f"❌ {pwd_result['message']}")
    finally:
        if change_pwd_conn:
            if st.session_state.user_role == "Sales Associate":
                release_postgres_connection(change_pwd_conn)
            else:
                change_pwd_conn.close()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Preferences Section
    st.markdown('<div class="settings-section">', unsafe_allow_html=True)
    st.markdown("<h2>🎨 Preferences</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox("Theme", ["Light", "Dark"], help="Choose your preferred interface theme")
    
    with col2:
        language = st.selectbox("Language", ["English", "Spanish", "French"], help="Select your language")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Logout Section
    st.markdown('<div class="settings-section">', unsafe_allow_html=True)
    st.markdown("<h2>🚪 Session</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🚪 Logout", width='stretch', type="primary"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_role = None
            st.session_state.chat_history = []
            logger.info("User logged out")
            st.success("✅ You have been logged out. Redirecting to login...")
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# SQL LOADER PAGE
# ============================================================================

def sql_loader_page():
    """SQL Loader page for bulk CSV imports with validation"""
    st.markdown("""
        <style>
        .sql-loader-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            padding: 2rem;
            border-radius: 16px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
        }
        
        .sql-loader-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
        }
        
        .sql-loader-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.95;
        }
        
        .column-card {
            background: rgba(102, 126, 234, 0.1);
            border-left: 4px solid #667eea;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.8rem;
        }
        
        .column-name {
            font-weight: 700;
            color: #667eea;
            margin-bottom: 0.3rem;
        }
        
        .column-desc {
            color: #888;
            font-size: 0.9rem;
        }
        </style>
        <div class="sql-loader-header">
            <h1>📁 SQL Loader - Bulk Import</h1>
            <p>Upload CSV files to bulk load data with validation</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Add CSS for gradient expanders
    st.markdown("""
    <style>
    /* Target Streamlit expander container */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    /* Alternative selector for expander button */
    [data-testid="stExpander"] {
        border: 2px solid #667eea !important;
    }
    
    /* Expander summary/header */
    details > summary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        padding: 12px 15px !important;
        border-radius: 8px !important;
        cursor: pointer !important;
        font-weight: 600 !important;
    }
    
    details > summary:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
    }
    
    /* Content background */
    details > div {
        background-color: rgba(102, 126, 234, 0.05) !important;
        padding: 15px !important;
        border-radius: 0 0 8px 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Load Orders", "↩️ Load Returns"])
    
    # ========== TAB 1: LOAD ORDERS ==========
    with tab1:
        st.subheader("Load Orders + Products")
        st.markdown("---")
        
        with st.expander("📋 CSV Columns Required", expanded=False):
            st.markdown("""
**Order Fields:** order_id, customer_id, order_date, order_priority

**Product Fields:** product_id, quantity, sales_amount, discount, shipping_cost, ship_date, ship_mode

*One row = one order + one product*
            """)
        
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'], key='orders_csv')
        
        if uploaded_file is not None:
            try:
                df_orders = pd.read_csv(uploaded_file)
                st.success(f"✓ {len(df_orders)} rows loaded")
                st.dataframe(df_orders, width='stretch')
                
                if st.button("🚀 Load into Database", key="btn_load_orders", width='stretch', type="primary"):
                    with st.spinner("Loading..."):
                        results = load_orders_with_products(df_orders)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Rows", results['total_rows'])
                    with col2:
                        st.metric("Orders Loaded", results['orders_loaded'])
                    with col3:
                        st.metric("Products Loaded", results['products_loaded'])
                    with col4:
                        st.metric("Errors", len(results['errors']))
                    

                    if results['errors']:
                        st.error(f"⚠️ {len(results['errors'])} error(s) - check logs")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
                logger.error(f"SQL Loader error: {e}")
    
    # ========== TAB 2: LOAD RETURNS ==========
    with tab2:
        st.subheader("Load Returns")
        
        with st.expander("📋 CSV Columns Required", expanded=False):
            st.markdown("""
**Columns:** returned, order_id, return_date, region

*Example row:*
- returned: Yes
- order_id: ORD-001
- return_date: 2025-12-13
- region: Central
            """)
        
        uploaded_file_returns = st.file_uploader("Choose CSV file", type=['csv'], key='returns_csv')
        
        if uploaded_file_returns is not None:
            try:
                df_returns = pd.read_csv(uploaded_file_returns)
                st.success(f"✓ {len(df_returns)} rows loaded")
                st.dataframe(df_returns, width='stretch')
                
                if st.button("🚀 Load into Database", key="btn_load_returns", width='stretch', type="primary"):
                    with st.spinner("Loading..."):
                        results = load_returns_from_csv(df_returns)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Rows", results['total_rows'])
                    with col2:
                        st.metric("Loaded", results['loaded_rows'])
                    with col3:
                        st.metric("Errors", len(results['errors']))
                    
                    if results['errors']:
                        st.error(f"⚠️ {len(results['errors'])} error(s)")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application logic"""
    
    if not st.session_state.authenticated:
        login_page()
    else:
        # Sidebar navigation - role-based pages
        st.sidebar.title("Navigation")
        
        # Define pages based on user role
        if st.session_state.user_role == "Sales Associate":
            pages = ["📊 Dashboard", "📝 Data Entry", "📁 SQL Loader", "⚙️ Settings"]
        elif st.session_state.user_role == "Store Manager":
            pages = ["📊 Dashboard", "💬 Chat Analytics", "⚙️ Settings"]
        elif st.session_state.user_role == "Executive":
            pages = ["🔄 ETL Management", "🗂️ Partition Monitoring", "⚙️ Settings"]
        else:
            pages = ["📊 Dashboard", "⚙️ Settings"]
        
        page = st.sidebar.radio(
            "Choose a page:",
            pages
        )
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 Account Information")
        st.sidebar.write(f"**Username:** {st.session_state.username}")
        st.sidebar.write(f"**Role:** {st.session_state.user_role}")
        db_type_display = st.session_state.db_type.upper() if st.session_state.db_type else 'None'
        db_icon = "🐘" if st.session_state.db_type == "postgres" else "🗄️"
        st.sidebar.write(f"**{db_icon} Database:** {db_type_display}")
        
        # Page routing
        if "Dashboard" in page:
            dashboard_page()
        elif "Data Entry" in page:
            data_entry_page()
        elif "SQL Loader" in page:
            sql_loader_page()
        elif "Chat Analytics" in page:
            chat_page()
        elif "ETL Management" in page:
            etl_management_page()
        elif "Partition Monitoring" in page:
            partition_monitoring_page()
        elif "Settings" in page:
            settings_page()


if __name__ == "__main__":
    main()



