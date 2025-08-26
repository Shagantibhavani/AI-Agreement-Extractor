import streamlit as st
import os
import sys
print(sys.executable)
import json
import pandas as pd
from datetime import datetime
from main import get_file_processor
import google.generativeai as genai # Import for token counting
from ai_analyzer import analyze_text_with_llm
from processors.image_processor import process_image
import io

# --- Constants ---
USER_DATA_FILE = "user_data.json"
# Configure genai for token counting
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("Gemini API key not found in .streamlit/secrets.toml. Token counting may not work.")

# --- Helper Functions ---
def load_user_data():
    """Loads user data from the JSON file."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # Return a default structure if the file is corrupted or empty
                return {"users": {}, "token_logs": {}, "daily_usage": {}, "overall_usage": {}}
    else:
        # Return a default structure if the file doesn't exist
        return {"users": {}, "token_logs": {}, "daily_usage": {}, "overall_usage": {}}


def save_user_data(data):
    """Saves user data to the JSON file."""
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user_token_history(username):
    """Retrieves token history for a specific user."""
    user_data = load_user_data()
    return user_data.get("token_logs", {}).get(username, [])

def add_token_log(username, filename, token_usage):
    """Adds a new token log entry for a user."""
    user_data = load_user_data()

    # Ensure username and token_logs structure exists
    if username not in user_data["token_logs"]:
        user_data["token_logs"][username] = []

    # Add the current file's log
    user_data["token_logs"][username].append({
        "filename": filename,
        "token_usage": token_usage,
        "date": datetime.now().strftime("%Y-%m-%d") # Store the date
    })

    # Update daily usage for the specific user
    today_str = datetime.now().strftime("%Y-%m-%d")
    if today_str not in user_data["daily_usage"]:
        user_data["daily_usage"][today_str] = {}
    if username not in user_data["daily_usage"][today_str]:
        user_data["daily_usage"][today_str][username] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    user_data["daily_usage"][today_str][username]["input_tokens"] += token_usage.get("input_tokens", 0)
    user_data["daily_usage"][today_str][username]["output_tokens"] += token_usage.get("output_tokens", 0)
    user_data["daily_usage"][today_str][username]["total_tokens"] += token_usage.get("total_tokens", 0)

    # Update overall usage for the specific user
    if username not in user_data["overall_usage"]:
        user_data["overall_usage"][username] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    user_data["overall_usage"][username]["input_tokens"] += token_usage.get("input_tokens", 0)
    user_data["overall_usage"][username]["output_tokens"] += token_usage.get("output_tokens", 0)
    user_data["overall_usage"][username]["total_tokens"] += token_usage.get("total_tokens", 0)

    save_user_data(user_data)

def authenticate_user(username, password):
    """Authenticates user credentials."""
    user_data = load_user_data()
    if username in user_data["users"] and user_data["users"][username] == password:
        return True
    return False

def register_user(username, password):
    """Registers a new user."""
    user_data = load_user_data()
    if username in user_data["users"]:
        return False # User already exists
    user_data["users"][username] = password
    # Initialize user's logs and usage if new user
    if username not in user_data["token_logs"]:
        user_data["token_logs"][username] = []
    # Initialize daily usage for new user (nested under today's date)
    today_str = datetime.now().strftime("%Y-%m-%d")
    if today_str not in user_data["daily_usage"]:
        user_data["daily_usage"][today_str] = {}
    if username not in user_data["daily_usage"][today_str]:
        user_data["daily_usage"][today_str][username] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    if username not in user_data["overall_usage"]:
        user_data["overall_usage"][username] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    save_user_data(user_data)
    return True

def clear_user_data_file():
    """Deletes the user_data.json file to clear all user details."""
    if os.path.exists(USER_DATA_FILE):
        os.remove(USER_DATA_FILE)
        st.success("Previous user data cleared.")

# --- Streamlit App ---
st.set_page_config(layout="wide")
st.title("Agreement Extraction Tool")

# --- User Data Persistence ---
# The clear_user_data_file() call has been removed to persist user data.
# User data (usernames, passwords, and token logs) will now be maintained in user_data.json.

# --- Session State Initialization ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "current_document_text" not in st.session_state: # Store document text
    st.session_state.current_document_text = ""
if "current_extracted_data_markdown" not in st.session_state: # Store extracted data as Markdown
    st.session_state.current_extracted_data_markdown = ""
if "current_token_usage" not in st.session_state: # Store current file token usage
    st.session_state.current_token_usage = None

# --- Login Page ---
if not st.session_state.logged_in:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Login"):
            if authenticate_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.current_token_usage = None # Reset token usage on new login
                st.session_state.current_document_text = "" # Clear previous document
                st.session_state.current_extracted_data_markdown = ""
                st.rerun() # Rerun to show the main app
            else:
                st.error("Invalid username or password")
    
    with col2:
        if st.button("Register"):
            if register_user(username, password):
                st.success("User registered successfully. Please login.")
            else:
                st.error("Username already exists.")
else:
    # --- Main App Content (after login) ---
    
    # --- Sidebar for Dashboard ---
    st.sidebar.title("Dashboard")
    
    # Display current user
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
    
    # Display token usage for the current file
    st.sidebar.subheader("Current File Token Usage")
    current_token_usage = st.session_state.current_token_usage
    if current_token_usage:
        st.sidebar.write(f"Input Tokens: {current_token_usage.get('input_tokens', 'N/A')}")
        st.sidebar.write(f"Output Tokens: {current_token_usage.get('output_tokens', 'N/A')}")
        st.sidebar.write(f"Total Tokens: {current_token_usage.get('total_tokens', 'N/A')}")
    else:
        st.sidebar.write("Input Tokens: N/A")
        st.sidebar.write("Output Tokens: N/A")
        st.sidebar.write("Total Tokens: N/A")
    
    # Display Today's and Overall Token Usage
    # --- MODIFICATION: Renamed subheaders ---
    st.sidebar.subheader("Today's Token Usage")
    user_data = load_user_data()
    today_str = datetime.now().strftime("%Y-%m-%d")
    # Retrieve today's usage for the specific logged-in user
    today_usage_for_user = user_data.get("daily_usage", {}).get(today_str, {}).get(st.session_state.username, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
    st.sidebar.write(f"Input: {today_usage_for_user.get('input_tokens', 0)}, Output: {today_usage_for_user.get('output_tokens', 0)}, Total: {today_usage_for_user.get('total_tokens', 0)}")
    
    st.sidebar.subheader("Overall Token Usage")
    user_data = load_user_data()
    if st.session_state.username in user_data["overall_usage"]:
        user_overall_usage = user_data["overall_usage"][st.session_state.username]
        st.sidebar.write(f"Input: {user_overall_usage.get('input_tokens', 0)}, Output: {user_overall_usage.get('output_tokens', 0)}, Total: {user_overall_usage.get('total_tokens', 0)}")
    else:
        st.sidebar.write("Input: 0, Output: 0, Total: 0")

    # Display token history for the user with date dropdown
    st.sidebar.subheader("Token History")
    token_history = get_user_token_history(st.session_state.username)
    
    # Group history by date
    history_by_date = {}
    for entry in token_history:
        date_str = entry.get("date", "Unknown Date")
        if date_str not in history_by_date:
            history_by_date[date_str] = []
        history_by_date[date_str].append(entry)
    
    # Sort dates in descending order
    sorted_dates = sorted(history_by_date.keys(), reverse=True)
    
    # --- MODIFICATION: Removed dropdown, display as expanders ---
    if sorted_dates:
        for date_heading in sorted_dates:
            with st.sidebar.expander(f"**{date_heading}**"):
                for entry in history_by_date[date_heading]:
                    st.write(f"  **{entry['filename']}**:")
                    st.write(f"    Input: {entry['token_usage'].get('input_tokens', 'N/A')}, Output: {entry['token_usage'].get('output_tokens', 'N/A')}, Total: {entry['token_usage'].get('total_tokens', 'N/A')}")
    else:
        st.sidebar.write("No history yet.")

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.current_token_usage = None # Clear token usage on logout
        st.session_state.current_document_text = "" # Clear previous document
        st.session_state.current_extracted_data_markdown = ""
        st.rerun()

    # --- File Upload and Analysis ---
    uploaded_file = st.file_uploader("Upload an agreement file", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"])

    if uploaded_file is not None:
        # To read file as bytes:
        bytes_data = uploaded_file.getvalue()
        
        # Create a temp_files directory if it doesn't exist
        if not os.path.exists("temp_files"):
            os.makedirs("temp_files")

        # To save the file temporarily to be able to use the existing get_processor
        file_path = os.path.join("temp_files", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(bytes_data)

        st.write("Filename:", uploaded_file.name)

        if st.button("Analyze Agreement"):
            try:
                with st.spinner("Analyzing..."):
                    api_key = st.secrets["GEMINI_API_KEY"]
                    if not api_key or api_key == "your_api_key_here":
                        st.error("Please add your Gemini API key to the .streamlit/secrets.toml file.")
                        st.stop()

                    # --- Document Processing ---
                    if uploaded_file.type.startswith('image/'):
                        tesseract_cmd = st.secrets.get("TESSERACT_CMD_PATH", None)
                        if not tesseract_cmd or tesseract_cmd == "your_tesseract_path_here":
                            st.error("Please add your Tesseract OCR path to the .streamlit/secrets.toml file.")
                            st.stop()
                        document_text = process_image(file_path, tesseract_cmd=tesseract_cmd)
                    else:
                        document_text = get_file_processor(file_path)
                    
                    # Store document text in session state
                    st.session_state.current_document_text = document_text

                    # --- Data Extraction and Token Usage Calculation ---
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    input_tokens = model.count_tokens(document_text).total_tokens

                    #extracted_data = json.loads(st.session_state.current_extracted_data_markdown["text"])

                    #parties = extracted_data.get("parties", "N/A")
                    prompt = f"Identify the Parties Involved, Vendor, and Receiver from the document text: {document_text}"
                    analysis_result = analyze_text_with_llm(prompt, api_key)

                    output_tokens = model.count_tokens(analysis_result).total_tokens
                    total_tokens = input_tokens + output_tokens

                    #extracted_data = json.loads(st.session_state.current_extracted_data_markdown["text"])
                    extracted_data = json.loads(analysis_result["text"])
                    #extracted_data["vendor"] = analysis_result.get("vendor", "N/A")
                    #extracted_data["receiver"] = analysis_result.get("receiver", "N/A")

                    token_usage = {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens
                    }

                    # Store token usage for the current file in session state
                    st.session_state.current_token_usage = token_usage
                    
                    # Store extracted data (Markdown table) in session state
                    st.session_state.current_extracted_data_markdown = analysis_result

                    # Add token log for the current user
                    add_token_log(st.session_state.username, uploaded_file.name, token_usage)
                    st.rerun() # Rerun to update the dashboard with new token usage

            except Exception as e:
                st.error(f"An error occurred: {e}")

            finally:
                # Clean up the temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)

        # --- Display Document Preview and Extracted Data (from session state) ---
        
        if st.session_state.get("current_extracted_data_markdown"):
            col1, col2 = st.columns(2) # Create two columns for layout

            with col1:
                st.subheader("Document Preview")
                st.text_area("Agreement Content", st.session_state.current_document_text, height=500)

            with col2:
                st.subheader("Extracted Data")
                extracted_data = json.loads(st.session_state.current_extracted_data_markdown["text"])

                agreement_terms = {
                    "Parties Involved": "parties",
                    "Effective Date": "effective_date",
                    "Termination Clauses": "termination_clause",
                    "Payment Terms": "payment_terms",
                    "Confidentiality Obligations": "confidentiality_obligations",
                    "Risky/Unusual Clauses": "risky_clauses",
                    "Vendor": "vendor",
                    "Receiver": "receiver"
                }

                data = []
                for i, (term, key) in enumerate(agreement_terms.items()):
                    value = extracted_data.get(key, "N/A")
                    # Ensure all values are strings
                    value = str(value) if value is not None else "N/A"
                    data.append([term, value])

                df = pd.DataFrame(data, columns=["Agreement Terms", "Data Extracted from the Agreement"])
                try:
                    st.dataframe(df)
                except Exception as e:
                    st.write(f"Error displaying dataframe: {e}")
                    st.write(df.to_dict())

                # --- Download Buttons ---
                import io
                def download_json():
                    json_data = st.session_state.current_extracted_data_markdown["text"]
                    return json_data.encode('utf-8')

                def download_csv():
                    extracted_data = json.loads(st.session_state.current_extracted_data_markdown["text"])
                    
                    agreement_terms_list = [
                        "Parties Involved",
                        "Effective Date",
                        "Termination Clauses",
                        "Payment Terms",
                        "Confidentiality Obligations",
                        "Risky/Unusual Clauses",
                        "Vendor",
                        "Receiver"
                    ]
                    
                    data_for_csv = []
                    for i, term_display_name in enumerate(agreement_terms_list):
                        # Map display name to key used in extracted_data
                        key_map = {
                            "Parties Involved": "parties",
                            "Effective Date": "effective_date",
                            "Termination Clauses": "termination_clause",
                            "Payment Terms": "payment_terms",
                            "Confidentiality Obligations": "confidentiality_obligations",
                            "Risky/Unusual Clauses": "risky_clauses",
                            "Vendor": "vendor",
                            "Receiver": "receiver"
                        }
                        key = key_map.get(term_display_name, term_display_name.lower().replace(" ", "_"))
                        value = extracted_data.get(key, "N/A")
                        value = str(value) if value is not None else "N/A"
                        data_for_csv.append([i + 1, term_display_name, value])

                    df_csv = pd.DataFrame(data_for_csv, columns=["Serial Number", "Agreement Terms", "Data Extracted from the Agreement"])
                    csv_data = df_csv.to_csv(index=False).encode('utf-8')
                    return csv_data

                st.download_button(
                    label="Download as JSON",
                    data=download_json(),
                    file_name="extracted_data.json",
                    mime="application/json",
                )

                st.download_button(
                    label="Download as CSV",
                    data=download_csv(),
                    file_name="extracted_data.csv",
                    mime="text/csv",
                )
    else:
        st.info("Please upload an agreement file to begin.")
