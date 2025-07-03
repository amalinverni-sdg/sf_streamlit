import os
import io
import pandas as pd
import streamlit as st
from snowflake.snowpark.context import get_active_session

# -------------------------------------
# Get Snowflake session
# -------------------------------------
session = get_active_session()

# -------------------------------------
# Constants and settings
# -------------------------------------
database_name = 'ACCELERATORS'
schema_name = 'STP'
stage_name = '__functions_stmts'

# -------------------------------------
# Return list of databases
# -------------------------------------
def get_databases():
    return session.sql("""
        select database_name
        from snowflake.information_schema.databases
    """).collect()

    

# -------------------------------------
# Stage existence check and creation
# -------------------------------------
def ensure_stage_exists():
    """
    Creates a stage if it doesn't exist. Does nothing if it already exists.
    """
    try:
        session.sql(f"""
            CREATE STAGE IF NOT EXISTS {database_name}.{schema_name}.__functions_stmts
            ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
            DIRECTORY = (ENABLE = TRUE)
        """).collect()
        st.success(f"Stage @`{database_name.lower()}`.`{schema_name.lower()}`.`__functions_stmts` will hold the sql file.")
    except Exception as e:
        st.error(f"Failed to create stage: {str(e)}")
        st.stop()



def retrieve_udf_udtfs():
    return session.sql(f"""
    select *
    from {database_name}.{schema_name}.functions
    """).collect()



def write_to_stage(file_name='test.sql'):
    try:
        file_content = f"SONO QUI"
        file_name = 'udf_ddl.txt'

        # Convert the string to bytes
        file_bytes = file_content.encode('utf-8')
        # Write to a bytes-like object
        file = io.BytesIO(file_bytes)
    except Exception as e:
        st.error(f"An error occurred: {e}")

    st.write('qui')
        
    # Use Snowflake's PUT command to upload the file to the internal stage
    try:
        session.file.put_stream(file, f"@{database_name}.{schema_name}.__functions_stmts/{file_name}", auto_compress = False, overwrite=True)
        st.success('File saved to Snowflake internal stage successfully!')
    except Exception as e:
        st.error(f"An error occurred: {e}")


def downloader():
    st.header("File Download")
    st.write("Download files from stage.")

    # Get list of files in stage
    try:
        stage_files = session.sql(f"LIST @{database_name}.{schema_name}.{stage_name}").collect()
    except Exception as e:
        st.error(f"An error occurred while listing files: {str(e)}")
        return

    if stage_files:
        file_names = [
            row['name'].split('/', 1)[1] if '/' in row['name'] else row['name']
            for row in stage_files
        ]
        selected_file = st.selectbox(
            "Select a file to download",
            file_names
        )

        if st.button("Download"):
            try:
                # Use the correct method to get the file stream
                with session.file.get_stream(f"@{database_name}.{schema_name}.{stage_name}/{selected_file}") as file_stream:
                    file_content = file_stream.read()
                    st.download_button(
                        label="Download File",
                        data=file_content,
                        file_name=selected_file,
                        mime="application/octet-stream"
                    )
            except Exception as e:
                st.error(f"An error occurred during download: {str(e)}")
    else:
        st.warning("No files found in stage.")

# -------------------------------------
# Main Streamlit app
# -------------------------------------
def main():

    ensure_stage_exists()

    st.write(session)
    # st.write(st.user)

    function_option = st.selectbox(
        "Do you need to edit an existing function o create a new one?",
        ("Create", "Edit"),
        index=None
    )

    if function_option == 'Create':
        udf_name = st.text_input("Enter the Ud(T)F name:")

    
    # -------------------------
    # Create tabs
    # -------------------------
    tab_secrets, tab_network_rule, tab_external_access_integration = st.tabs([
        "Create Secret",
        "Create Network Rule",
        "Create External Access Integration"
    ])

    # -------------------------
    # Create Secret tab
    # -------------------------
    with tab_secrets:
        st.header("Create Secret")
        st.write("Create a secret to store your informations.")

        with st.form("secret_form"):
            sec_name = st.text_input("Enter secret name (e.g., SEC_DATABRICKS_PAT)")
            password = st.text_input("Enter your password", type="password")
            submit_button = st.form_submit_button("Create Secret")

        if sec_name and password and submit_button:
            try:
                session.sql(f"""
                CREATE OR REPLACE SECRET {database_name}.{schema_name}.{sec_name}
                    TYPE = GENERIC_STRING
                    SECRET_STRING = '{password}';
                """).collect()
                # Delete the password variable
                del password
                                
                st.success(f"Secret '{database_name}.{schema_name}.{sec_name}' has been created!")

            except Exception as e:
                del password
                st.error(f"Error occurred while creating secret: {str(e)}")

            write_to_stage()

    
    # -------------------------
    # Create Network Rule tab
    # -------------------------
    with tab_network_rule:
        st.header("Create Network Rule")
        st.write("Create a network rule for the .")

        with st.form("rule_form"):
            rule_name = st.text_input("Enter rule name (e.g., NR_DATABRICKS)")
            address = st.text_input("Enter your endpoint")
            submit_button = st.form_submit_button("Create Network Rule")

        if rule_name and address and submit_button:
            try:
                session.sql(f"""
                CREATE OR REPLACE NETWORK RULE {database_name}.{schema_name}.{rule_name}
                    MODE = EGRESS
                    TYPE = HOST_PORT
                    VALUE_LIST = ('{address}')
                ;    
                """).collect()
                                
                st.success(f"Network Rule '{database_name}.{schema_name}.{rule_name}' has been created!")

            except Exception as e:
                st.error(f"Error occurred while creating Network Rule: {str(e)}")
    
    # -------------------------
    # Create External Access Integration
    # -------------------------
    with tab_external_access_integration:
        st.header("Create External Access Integration")
        st.write("Create an external access integration for the UdF.")

        with st.form("access_integration_form"):
            access_integration_name = st.text_input("Enter external access integration name (e.g., EAI_DATABRICKS)")

            net_rules_list = session.sql(f"""
                show network rules in {database_name}.{schema_name}
                    ->> select concat_ws('.', "database_name", "schema_name", "name") as fqn from $1
            """).collect()
            
            net_rules = st.multiselect(
                "What Network Rule(s) do you want to include?",
                net_rules_list
            )

            secrets_list = session.sql(f"""
                show secrets in {database_name}.{schema_name}
                    ->> select concat_ws('.', "database_name", "schema_name", "name") as fqn from $1
            """).collect()
            
            secs = st.multiselect(
                "What Secret(s) do you want to include?",
                secrets_list
            )
                        
            submit_button = st.form_submit_button("Create External Access Integration")

        if access_integration_name and net_rules and secs:
            try:
                session.sql(f"""
                CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION {access_integration_name}
                    ALLOWED_NETWORK_RULES = ({', '.join(net_rules)})
                    ALLOWED_AUTHENTICATION_SECRETS = ({', '.join(secs)})
                    ENABLED = TRUE
                ;    
                """).collect()
                                
                st.success(f"External Access Integration has '{access_integration_name}' has been created!")

            except Exception as e:
                st.error(f"Error occurred while creating Network Rule: {str(e)}")


# -------------------------------------
# Launch app
# -------------------------------------
if __name__ == "__main__":
    main()
    downloader()
