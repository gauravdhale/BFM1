import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import numpy as np

st.set_page_config(layout="wide")

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load CSS
load_css("styles.css")

@st.cache_data
def fetch_stock_data(ticker):
    return yf.download(ticker, start="2020-01-01", end="2025-01-25")

@st.cache_data
def fetch_fundamental_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    financials = stock.financials
    balance_sheet = stock.balance_sheet
    cashflow = stock.cashflow
    
    dates = pd.date_range(start="2020-01-01", end="2025-01-25", freq='D')
    fundamental_data = []
    
    for date in dates:
        try:
            total_revenue = financials.loc["Total Revenue"].get(date.strftime("%Y-%m-%d"), None) if "Total Revenue" in financials.index else None
            debt_to_equity = (balance_sheet.loc["Total Debt"].get(date.strftime("%Y-%m-%d"), None) / balance_sheet.loc["Total Equity"].get(date.strftime("%Y-%m-%d"), None)) if ("Total Debt" in balance_sheet.index and "Total Equity" in balance_sheet.index) else None
            net_cashflow = cashflow.loc["Total Cash From Operating Activities"].get(date.strftime("%Y-%m-%d"), None) if "Total Cash From Operating Activities" in cashflow.index else None
        except Exception:
            total_revenue, debt_to_equity, net_cashflow = None, None, None
        
        data = {
            "Date": date,
            "Market Cap": info.get("marketCap"),
            "Enterprise Value": info.get("enterpriseValue"),
            "P/E Ratio": info.get("trailingPE"),
            "Debt-to-Equity Ratio": debt_to_equity,
            "Total Revenue": total_revenue,
            "Net Cash Flow": net_cashflow
        }
        fundamental_data.append(data)
    
    return pd.DataFrame(fundamental_data)

@st.cache_data
def fetch_live_news(api_key, query):
    url = f'https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={api_key}'
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    news_data = response.json()
    return news_data['articles'] if 'articles' in news_data else []

@st.cache_data
def fetch_eps_pe_ipo_kpi(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    data = {
        "EPS": info.get("trailingEps"),
        "PE Ratio": info.get("trailingPE"),
        "IPO Date": info.get("ipoDate"),
        "KPI": info.get("kpi"),
        "Current Price": info.get("regularMarketPrice")
    }
    return data

@st.cache_data
def fetch_company_info(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return info.get("longBusinessSummary", "No information available.")

@st.cache_data
def load_opening_price_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="max")
    hist = hist[hist.index <= '2025-01-25']  # Limit data till 25th January 2025
    hist.reset_index(inplace=True)
    hist['Year'] = hist['Date'].dt.year
    hist['Month'] = hist['Date'].dt.month
    hist['Day'] = hist['Date'].dt.day
    hist['Opening Price'] = hist['Open']  # Assuming 'Open' prices as 'Opening Price'
    return hist

@st.cache_data
def fetch_current_stock_price(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="1d")["Close"].iloc[-1]

# Plot actual vs predicted prices
def plot_actual_vs_predicted(company_name, file_name):
    # Load the data
    data = pd.read_csv(file_name)
    
    # Set the date as the index for plotting
    data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)
    data.set_index('Date', inplace=True)
    
    # Calculate the error percentage for January 24, 2025
    specific_date = pd.Timestamp('2025-01-24')
    if specific_date in data.index:
        actual_price = data.loc[specific_date, 'Actual Price']
        predicted_price = data.loc[specific_date, 'Predicted Price']
        error_percentage = abs((actual_price - predicted_price) / actual_price) * 100
        error_text = f"Error percentage as on January 24, 2025: {error_percentage:.2f}%"
    else:
        error_text = "No data for January 24, 2025"
    
    # Create the figure
    fig = go.Figure()
    
    # Add actual price trace
    fig.add_trace(go.Scatter(x=data.index, y=data['Actual Price'], mode='lines', name='Actual Price', line=dict(color='blue')))
    
    # Add predicted price trace
    fig.add_trace(go.Scatter(x=data.index, y=data['Predicted Price'], mode='lines', name='Predicted Price', line=dict(color='red', dash='dash')))
    
    # Update layout with titles and labels
    fig.update_layout(
        title=f'{company_name} - Actual vs Predicted Opening Prices',
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='x unified'
    )
    
    # Update hover information
    fig.update_traces(
        hovertemplate='<b>Date</b>: %{x|%d/%m/%Y}<br><b>Actual Price</b>: %{y}<br><b>Predicted Price</b>: %{customdata:.2f}<extra></extra>',
        customdata=data['Predicted Price']
    )
    
    # Use Streamlit to display the plot and error percentage
    st.plotly_chart(fig)
    st.write(error_text)

# Fetch alternative KPI and IPO data from Alpha Vantage
@st.cache_data
def fetch_alternative_kpi_ipo(ticker, api_key):
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    data = response.json()
    return {
        "IPO Date": data.get("IPODate", "N/A"),
        "KPI": data.get("ProfitMargin", "N/A")  # Assuming KPI is represented by Profit Margin
    }

# Main function
def main():
    st.title("📈 Stock Market Dashboard")

    # Sidebar
    st.sidebar.header("Select Company")
    companies = {
        "Adani Green Energy": "ADANIGREEN.NS",
        "Tata Power": "TATAPOWER.NS",
        "Jsw Energy": "JSWENERGY.NS",
        "NTPC": "NTPC.NS",
        "Power Grid Corp": "POWERGRID.NS",
        "NHPC": "NHPC.NS"
    }
    company = st.sidebar.selectbox("Choose a company", list(companies.keys()))
    ticker = companies[company]

    # Page filter
    st.sidebar.header("Select Page")
    page = st.sidebar.selectbox("Choose a page", ["Page 1", "Page 2"])

    if page == "Page 2":
        col1, col2, col3 = st.columns([4, 3, 2])

        with col1:
            st.subheader("Opening Price Prediction")

            # Fetch current stock price
            current_price = fetch_current_stock_price(ticker)
            st.markdown(f"<h4 style='color: green;'>Current Stock Price: ₹{current_price:.2f}</h4>", unsafe_allow_html=True)

            # Perform prediction on page load
            opening_price_data = load_opening_price_data(ticker)
            
            # Plot the predictions
            plot_actual_vs_predicted(company, f"{company}_opening_price_data_with_predictions.csv")

            year = st.selectbox("Select Year", [2020, 2021, 2022, 2023, 2024, 2025])

            st.subheader("Opening Price Data")
            filtered_data = opening_price_data[opening_price_data['Year'] == year]
            st.dataframe(filtered_data, height=200)  # Decrease height of the opening price data chart

        with col2:
            st.subheader(f"About {company}")
            company_info = fetch_company_info(ticker)
            st.text_area("Company Information", company_info, height=150)

            st.subheader(f"{company} Performance")
            df_stock = fetch_stock_data(ticker)
            year_data = df_stock[df_stock.index.year == year]
            volume_range = st.slider("Volume Traded", min_value=int(year_data['Volume'].min()), max_value=int(year_data['Volume'].max()), value=int(year_data['Volume'].mean()), step=1)
            
            # Display the selected volume range
            st.write(f"Selected Volume Range: {volume_range}")

            st.subheader("Company Weightage Heatmap")

            # Load heatmap data
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

            # Create interactive heatmap using Plotly
            heatmap_data = padded_weights.reshape(num_rows, num_cols)
            hovertext = np.array([f"{company}<br>Weight: {weight:.2f}<br>Rank: {rank+1}" for rank, (company, weight) in enumerate(zip(padded_companies, padded_weights))]).reshape(num_rows, num_cols)

            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                text=hovertext,
                hoverinfo='text',
                colorscale='YlOrBr',
                showscale=True,
                colorbar=dict(title='Weightage')
            ))

            fig.update_layout(
                title='Company Weightage Heatmap',
                xaxis=dict(showticklabels=False),
                yaxis=dict(showticklabels=False),
                height=535  # Increase height of the heatmap
            )

            st.plotly_chart(fig)

        with col3:
            st.subheader("Live News")
            news_api_key = "31739ed855eb4759908a898ab99a43e7"
            query = company
            news_articles = fetch_live_news(news_api_key, query)
            news_text = ""
            for article in news_articles:
                news_text += f"{article['title']}\n\n{article['description']}\n\n[Read more]({article['url']})\n\n\n"
            st.text_area("Live News", news_text, height=150)
        
            st.subheader(f"{company} EPS, PE, IPO KPI")
            eps_pe_ipo_kpi = fetch_eps_pe_ipo_kpi(ticker)
            
            # Fetch alternative data if main source fails
            if eps_pe_ipo_kpi["IPO Date"] is None or eps_pe_ipo_kpi["KPI"] is None:
                alpha_vantage_api_key = "YOUR_ALPHA_VANTAGE_API_KEY"
                alternative_data = fetch_alternative_kpi_ipo(ticker, alpha_vantage_api_key)
                ipo_date = alternative_data["IPO Date"]
                kpi = alternative_data["KPI"]
            else:
                ipo_date = eps_pe_ipo_kpi.get("IPO Date", ipo_dates.get(ticker, "N/A"))
                kpi = eps_pe_ipo_kpi["KPI"]
            
            st.write(f"EPS: {eps_pe_ipo_kpi['EPS']}")
            st.write(f"PE Ratio: {eps_pe_ipo_kpi['PE Ratio']}")
            st.write(f"IPO Date: {ipo_date}")
            st.write(f"KPI: {kpi}")
            st.write(f"Current Price: ₹{current_price:.2f}")

       

if __name__ == "__main__":
    main()
