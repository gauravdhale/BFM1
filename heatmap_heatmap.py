import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

st.set_page_config(layout="wide")

def main():
    st.title("Company Weightage Heatmap")

    # Load data
    data_url = "https://raw.githubusercontent.com/SpartanKurt051/BFM/main/Heatmap.csv"
    df = pd.read_csv(data_url)

    # Strip any leading/trailing spaces from column names
    df.columns = df.columns.str.strip()

    # Set the 'Company' column as index
    df.set_index('Company', inplace=True)

    # Generate a grid layout for the heatmap
    num_companies = df.shape[0]
    num_cols = 5  # Define the number of columns in the "periodic table"
    num_rows = int(np.ceil(num_companies / num_cols))

    # Pad the data to fit into the grid layout
    padded_weights = np.pad(df['Weight'].values, (0, num_rows * num_cols - num_companies), mode='constant', constant_values=np.nan)
    padded_companies = np.pad(df.index.values, (0, num_rows * num_cols - num_companies), mode='constant', constant_values='')

    fig, ax = plt.subplots(figsize=(5, 3))
    heatmap_data = padded_weights.reshape(num_rows, num_cols)

    # Use a custom colormap with shades of brown
    cmap = sns.light_palette("brown", as_cmap=True)

    sns.heatmap(heatmap_data, annot=padded_companies.reshape(num_rows, num_cols),
                fmt='', cmap=cmap, cbar_kws={'label': 'Weightage'}, linewidths=.5, ax=ax, annot_kws={"size": 8})

    ax.set_title('Company Weightage Heatmap')

    # Adjust font size and layout
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)

    # Display heatmap in Streamlit
    st.pyplot(fig)

if __name__ == "__main__":
    main()
