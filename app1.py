import openai
import streamlit as st
import pandas as pd
import io
import sqlite3

# Function to get table columns from SQLite database
def get_table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print("Columns in the table:", columns)
    return [column[1] for column in columns]

# Function to generate SQL query from input text using ChatGPT
def generate_sql_query(table_name, text, columns):
    # OpenAI API key (replace this with your actual key or load from an environment variable)
    openai.api_key = "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"
    prompt = f"""
You are a ChatGPT language model that can generate SQL queries.
Please provide a natural language input text, and I will generate the corresponding SQL query for you.
The table name is {table_name} and corresponding columns are {columns}.

Input: {text}
SQL Query:
"""
    print("Prompt for OpenAI API:", prompt)
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Use a valid model
        messages=[{"role": "user", "content": prompt}]
    )
    sql_query = response['choices'][0]['message']['content'].strip()

    # Clean up the query string to remove markdown code block formatting
    if sql_query.startswith("```sql"):
        sql_query = sql_query[6:].strip()  # Remove the opening ```sql
    if sql_query.endswith("```"):
        sql_query = sql_query[:-3].strip()  # Remove the closing ```
    
    print("Generated SQL Query:", sql_query)
    return sql_query

# Function to execute SQL query on SQLite database
def execute_sql_query(cursor, query):
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        print("Query Result:", result)
        return result
    except sqlite3.OperationalError as e:
        print(f"SQL Error: {str(e)}")
        return None

# Function to get the response from GPT-3 or GPT-4
def get_bot_response(cursor, table_name, user_input, columns, excel_data=None):
    try:
        if excel_data is None:
            return "Error: No data uploaded. Please upload an Excel file first."
        
        if user_input:
            if "summary" in user_input.lower():
                return st.dataframe(excel_data.describe().to_string())
            elif "columns" in user_input.lower():
                return f"The columns in the data are: {excel_data.columns.tolist()}"
            elif "transactions on" in user_input.lower():
                date_input = user_input.lower().split("transactions on")[-1].strip()
                specific_date = pd.to_datetime(date_input, errors='coerce')
                if specific_date:
                    filtered_data = excel_data[excel_data['Transaction date'] == specific_date]
                    if filtered_data.empty:
                        return f"No Transaction found on {specific_date}."
                    else:
                        return str(filtered_data)
                else:
                    return "Invalid date format. Please use YYYY/MM/DD."
            else:
                sql_query = generate_sql_query(table_name, user_input, columns)
                if sql_query:
                    result = execute_sql_query(cursor, sql_query)
                    return result if result else "No data returned from the query."
        else:
            return "Error: Please enter your input."
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit app
def main():
    conn = sqlite3.connect("chatgb.db")
    cursor = conn.cursor()

    # Streamlit app title
    st.title("AI Chatbot with Excel File Handling")

    # Greeting message
    if "history" not in st.session_state or len(st.session_state.history) == 0:
        st.markdown("""
        **Hello and welcome!** 👋 I'm your AI-powered assistant, ready to help you explore and interact with your data.
        🗂️ **Upload your Excel file** below and ask me anything about the data! Whether you want to know the summary, columns, or even details like the shape of your dataset – I'm here to assist.
        Let’s get started! Feel free to upload your file and ask away.
        """)

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "excel_data" not in st.session_state:
        st.session_state.excel_data = None

    # Allow user to upload an Excel file
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        st.session_state.excel_data = pd.read_excel(uploaded_file)
        st.write(f"Excel Data loaded: {st.session_state.excel_data.shape}")
        st.write("Preview of the data:")
        st.write(st.session_state.excel_data.head())

    # Create a table in the SQLite database
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TRANSACTION1 (
        "Transaction ID" TEXT,
        "Transaction date" TEXT,
        "Client name" TEXT,
        "Transaction type" TEXT,
        "Transaction amount" REAL
    )""")

    if st.session_state.excel_data is not None and not st.session_state.excel_data.empty:
        st.session_state.excel_data.to_sql('TRANSACTION1', conn, if_exists='replace', index=False)

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Get user input after file is uploaded
    if uploaded_file is not None and st.session_state.excel_data is not None:
        user_input = st.chat_input("Ask about the data:")
        table_name = 'TRANSACTION1'
        columns = get_table_columns(cursor, table_name)

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Display the user message
            with st.chat_message("user"):
                st.markdown(user_input)

            # Get the chatbot's response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                # If the user wants to exit, end the chat
                if "exit" in user_input.lower() or "thank you" in user_input.lower():
                    st.session_state.messages.append({"role": "assistant", "content": "Goodbye! Feel free to come back anytime."})
                    full_response = 'Goodbye! Feel free to come back anytime'
                    message_placeholder.markdown(full_response)
                    st.stop()  # Stop the app from further execution

                # Get the chatbot's response based on the Excel data
                full_response = get_bot_response(cursor, table_name, user_input, columns, st.session_state.excel_data)

                # Update the response in the chat
                message_placeholder.markdown(full_response)

            # Append assistant's response to the session state
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    else:
        st.info("Please upload an Excel file to start chatting with the bot.")

if __name__ == "__main__":
    main()
