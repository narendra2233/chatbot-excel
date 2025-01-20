import openai
import streamlit as st
import pandas as pd
import io
#import os
#from dotenv import load_dotenv

# Function to get the response from GPT-3 or GPT-4
def get_bot_response(user_input, excel_data=None):
    try:
        # Ensure the excel_data is not None
        if excel_data is None:
            return "Error: No data uploaded. Please upload an Excel file first."
        if user_input:
        
            # Handle requests related to the Excel data
            if "summary" in user_input.lower():
                return excel_data.describe().to_string()  # Show a statistical summary
            elif "columns" in user_input.lower():
                return f"The columns in the data are: {excel_data.columns.tolist()}"  # List the columns of the data
            elif any(last in user_input.lower() for last in ['last rows','bottom rows','tail']):
                return str(st.dataframe(excel_data.tail()))
            elif any(keyword in user_input.lower() for keyword in ["head", 'top rows', 'show', 'few rows']):
                return str(st.dataframe(excel_data.head()))  # Show the first 5 rows
            elif 'rows' in user_input.lower() or 'total rows' in user_input.lower():
                # Ensure that the integer is converted to a string
                return f"The total number of rows is: {str(excel_data.shape[0])}"
            elif "shape" in user_input.lower():
                return str(excel_data.shape)  # Show the shape of the data
            elif "unique clients" in user_input.lower() or "distinct clients" in user_input.lower():
                return str(excel_data['Client name'].unique())
            elif any(maximum in user_input.lower() for maximum in ['highest transaction','maximum*','top transactions']):
                excel_data['Transaction amount']=pd.to_numeric(excel_data['Transaction amount'],errors='coerce')
                maximum_transaction=excel_data[excel_data['Transaction amount']==excel_data['Transaction amount'].max()]
                return str(maximum_transaction)
            elif 'transaction type' in user_input.lower():
                excel_data=pd.to_numeric(excel_data['Transaction amount'])
                aggregated_data=excel_data.groupby('Transaction type')['Transaction amount'].sum()
                return aggregated_data
            elif "info" in user_input.lower() or 'describe' in user_input.lower() or 'schema' in user_input.lower():
                buffer = io.StringIO()
                excel_data.info(buf=buffer)
                return buffer.getvalue()  # Show general information about the data
            elif "which country" in user_input.lower():
                data=excel_data.groupby('country').size()
                maximum_customers=data.max()
                return str(maximum_customers)
                        
                
            elif "transactions on" in user_input.lower():
                date_input = user_input.lower().split("transactions on")[-1].strip()  # Extract date after 'transaction on'
                specific_date = pd.to_datetime(date_input, errors='coerce')
                if specific_date:
                      filtered_data = excel_data[excel_data['Transaction date'] == specific_date]
                      if filtered_data.empty:
                            return f"No Transaction found on {specific_date}."
                      else:
                            return filtered_data
                else:
                      return "Invalid date format. Please use YYYY/MM/DD."
            else:
                #load_dotenv()
                openai.api_key = "API_KEY"   #os.getenv('openai_api_key')  
                response = openai.Completion.create(
                    model="gpt-3.5-turbo",  # or "gpt-4"
                    messages=[{'role': 'system', 'content': excel_data.to_string(index=False)},
                              {"role": "user", "content": user_input}],
                    max_tokens=150
                )
                bot_message = response['choices'][0]['message']['content']
                return bot_message
        else:
            return "Error: Please enter your input."
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit app
def main():
    # App title
    st.title("AI Chatbot with Excel File Handling")

    # Greeting message
    if "history" not in st.session_state or len(st.session_state.history) == 0:
       st.markdown("""
       **Hello and welcome!** 👋 I'm your AI-powered assistant, ready to help you explore and interact with your data.

      🗂️ **Upload your Excel file** below and ask me anything about the data! Whether you want to know the summary, columns, or even details like the shape     of your dataset – I'm here to assist.

      Let’s get started! Feel free to upload your file and ask away.
      """)
    
    # Initialize session state for the model, messages, and uploaded file
    if "openai_model" not in st.session_state:
       st.session_state["openai_model"] = "gpt-3.5-turbo"
    if "messages" not in st.session_state:
       st.session_state.messages = []
    if "excel_data" not in st.session_state:
       st.session_state.excel_data = None

    # Allow user to upload an Excel file (only accepts xlsx, xls)
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

    excel_data = None

    if uploaded_file is not None:
         st.session_state.excel_data = pd.read_excel(uploaded_file)
         st.write(f"Excel Data loaded: {st.session_state.excel_data.shape}")
         st.write("Preview of the data:")
         st.write(st.session_state.excel_data.head())

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Get user input after file is uploaded
    if uploaded_file is not None and st.session_state.excel_data is not None:
         prompt = st.chat_input("Ask about the data:")

         if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display the user message
            with st.chat_message("user"):
               st.markdown(prompt)

            # Get the chatbot's response
            with st.chat_message("assistant"):
               message_placeholder = st.empty()
               full_response = "" 

               # If the user wants to exit, end the chat
               if "exit" in prompt.lower() or "thank you" in prompt.lower():
                   st.session_state.messages.append({"role": "assistant", "content": "Goodbye! Feel free to come back anytime."})
                   full_response='Goodbye! Feel free to come back anytime'
                   message_placeholder.markdown(full_response)
                   st.stop()  # Stop the app from further execution

               # Get the chatbot's response based on the Excel data 
               full_response += get_bot_response(prompt, st.session_state.excel_data)

               # Update the response in the chat
               message_placeholder.markdown(full_response)

            # Append assistant's response to the session state
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    else:
        st.info("Please upload an Excel file to start chatting with the bot.")

if __name__ == "__main__":
    main()
