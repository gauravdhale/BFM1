import streamlit as st

st.set_page_config(layout="wide")

def main():
    st.title("Page with Two Columns")

    col1, col2 = st.columns(2)

    with col1:
        st.header("Column 1")
        st.write("This is some dummy data for column 1.")
        st.write("More dummy data for column 1.")

    with col2:
        st.header("Column 2")
        st.write("This is some dummy data for column 2.")
        st.write("More dummy data for column 2.")

if __name__ == "__main__":
    main()
