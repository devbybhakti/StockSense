
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="StockSense | Premium Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- PREMIUM DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background: #081321;
    color: #F1F5F9;
}
[data-testid="stSidebar"] {
    background: #0D1B2A;
    border-right: 1px solid #20364C;
}
.block-container {
    padding-top: 1.8rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}
h1, h2, h3 {
    color: #F8FAFC !important;
    letter-spacing: -0.5px;
}
p, label {
    color: #AAB8CA;
}
[data-testid="stMetric"] {
    background: linear-gradient(145deg,#14283D,#102033);
    border: 1px solid #24425C;
    padding: 19px;
    border-radius: 15px;
}
[data-testid="stMetricLabel"] {
    color: #AAB8CA !important;
}
[data-testid="stMetricValue"] {
    color: #16C784 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 13px;
}
div[data-baseweb="select"] > div {
    background: #14283D;
    border-color: #29445D;
    border-radius: 10px;
}
.stButton > button {
    background: #087F5B;
    color: white;
    border: none;
    border-radius: 9px;
}
.stButton > button:hover {
    background: #10A878;
    color: white;
    border: none;
}
.hero {
    background: linear-gradient(110deg,#10263C,#123B39);
    border: 1px solid #245247;
    padding: 24px 27px;
    border-radius: 17px;
    margin-bottom: 25px;
}
.hero-title {
    font-size: 30px;
    font-weight: 750;
    color: #FFFFFF;
}
.hero-subtitle {
    color: #AFC4D4;
    font-size: 14px;
    margin-top: 6px;
}
.section-title {
    color: #F1F5F9;
    font-size: 21px;
    font-weight: 700;
    margin: 20px 0 12px 0;
}
.small-note {
    color: #8295AA;
    font-size: 12px;
}
hr {
    border-color: #20364C;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA FUNCTIONS ----------------

@st.cache_data(ttl=300)
def get_stock_data(symbol, period="1mo"):
    df = yf.Ticker(symbol).history(
        period=period,
        interval="1d",
        auto_adjust=False
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.dropna()

def get_market_info(symbol):
    try:
        df = get_stock_data(symbol, "5d")

        if len(df) < 2:
            return None

        current = float(df["Close"].iloc[-1])
        previous = float(df["Close"].iloc[-2])

        change = current - previous
        percentage = (change / previous) * 100

        return current, change, percentage

    except Exception:
        return None

# ---------------- SIDEBAR ----------------

st.sidebar.markdown("""
<div style="padding:12px 0 20px 0;">
    <div style="font-size:26px;font-weight:800;color:white;">
        <span style="color:#16C784;">◈</span> StockSense
    </div>
    <div style="color:#8EA3B8;font-size:12px;">
        SMART MARKET INTELLIGENCE
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()
import sqlite3

conn = sqlite3.connect("stocksense.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock TEXT,
    symbol TEXT,
    purchase_price REAL,
    quantity INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock TEXT,
    symbol TEXT
)
""")

conn.commit()
conn.close()
page = st.sidebar.radio(
    "WORKSPACE",
    ["Dashboard", "Analytics", "Prediction", "Watchlist", "Portfolio"]
)

st.sidebar.divider()

st.sidebar.markdown("### MARKET")
st.sidebar.markdown(
    "<span style='color:#16C784;'>●</span> "
    "<span style='color:#AAB8CA;'>Indian Equities · NSE</span>",
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.sidebar.caption("STOCKSENSE v1.0")
st.sidebar.caption("Market data may be delayed.")

# ---------------- HEADER ----------------


# ---------------- ADVANCED ANALYTICS PAGE ----------------

if page == "Analytics":

    st.title("📊 Advanced Stock Analytics")
    st.caption("Technical indicators and quantitative market insights")

    analytics_stocks = {
        "TCS": "TCS.NS",
        "Reliance Industries": "RELIANCE.NS",
        "Infosys": "INFY.NS"
    }

    col1, col2 = st.columns(2)

    with col1:
        selected_stock = st.selectbox(
            "Select stock",
            list(analytics_stocks.keys())
        )

    with col2:
        selected_period = st.selectbox(
            "Analysis period",
            ["3mo", "6mo", "1y", "2y"]
        )

    df = get_stock_data(
        analytics_stocks[selected_stock],
        selected_period
    )

    if not df.empty:

        # 1. Moving Averages
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()

        # 2. RSI Calculation
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1/14,
            adjust=False,
            min_periods=14
        ).mean()

        avg_loss = loss.ewm(
            alpha=1/14,
            adjust=False,
            min_periods=14
        ).mean()

        rs = avg_gain / avg_loss.replace(0, float("nan"))

        df["RSI"] = 100 - (100 / (1 + rs))

        df.loc[
            (avg_loss == 0) & (avg_gain > 0),
            "RSI"
        ] = 100

        # 3. MACD Calculation
        ema12 = df["Close"].ewm(
            span=12,
            adjust=False
        ).mean()

        ema26 = df["Close"].ewm(
            span=26,
            adjust=False
        ).mean()

        df["MACD"] = ema12 - ema26

        df["Signal"] = df["MACD"].ewm(
            span=9,
            adjust=False
        ).mean()

        df["Histogram"] = df["MACD"] - df["Signal"]

        # 4. Indicator Cards
        latest = df.iloc[-1]

        st.markdown("### Key Technical Indicators")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "RSI (14)",
            f"{latest['RSI']:.2f}"
            if pd.notna(latest["RSI"]) else "N/A"
        )

        c2.metric(
            "MACD",
            f"{latest['MACD']:.2f}"
        )

        c3.metric(
            "50-Day Moving Average",
            f"₹{latest['SMA50']:,.2f}"
            if pd.notna(latest["SMA50"]) else "N/A"
        )

        st.markdown("---")
        st.markdown("### Technical Analysis Charts")

        # 5. Create Four Interactive Charts
        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.045,
            row_heights=[0.48, 0.17, 0.18, 0.17],
            subplot_titles=[
                "Price & Moving Averages",
                "Trading Volume",
                "Relative Strength Index (RSI)",
                "MACD Analysis"
            ]
        )

        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                increasing_line_color="#16C784",
                decreasing_line_color="#EA3943",
                name="Price"
            ),
            row=1, col=1
        )

        # SMA 20
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["SMA20"],
                name="SMA 20",
                line=dict(color="#F5B942", width=2)
            ),
            row=1, col=1
        )

        # SMA 50
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["SMA50"],
                name="SMA 50",
                line=dict(color="#4DA3FF", width=2)
            ),
            row=1, col=1
        )

        # Volume
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Volume",
                marker_color="#16C784",
                opacity=0.65
            ),
            row=2, col=1
        )

        # RSI
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["RSI"],
                name="RSI",
                line=dict(color="#B58AFF", width=2)
            ),
            row=3, col=1
        )

        fig.add_hline(
            y=70,
            line_dash="dash",
            line_color="#EA3943",
            row=3, col=1
        )

        fig.add_hline(
            y=30,
            line_dash="dash",
            line_color="#16C784",
            row=3, col=1
        )

        # MACD
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MACD"],
                name="MACD",
                line=dict(color="#4DA3FF", width=2)
            ),
            row=4, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Signal"],
                name="Signal",
                line=dict(color="#F5B942", width=2)
            ),
            row=4, col=1
        )

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Histogram"],
                name="Histogram",
                marker_color="#16C784",
                opacity=0.5
            ),
            row=4, col=1
        )

        # Chart Styling
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0D1B2A",
            plot_bgcolor="#102238",
            font=dict(color="#DCE7F2"),
            height=950,
            hovermode="x unified",
            xaxis_rangeslider_visible=False,
            margin=dict(l=20, r=20, t=70, b=20)
        )

        fig.update_xaxes(
            showgrid=False,
            rangeslider_visible=False
        )

        fig.update_yaxes(
            gridcolor="#24394F"
        )

        fig.update_yaxes(
            range=[0, 100],
            row=3,
            col=1
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.markdown("### Indicator Interpretation")

        st.info(
            "RSI above 70 may indicate overbought conditions. "
            "RSI below 30 may indicate oversold conditions. "
            "These indicators are analytical tools, not guaranteed predictions."
        )

    else:
        st.warning("No historical data available.")

# ---------------- MACHINE LEARNING PREDICTION ----------------

elif page == "Prediction":

    import numpy as np
    import plotly.graph_objects as go
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    st.title("🤖 AI Stock Price Prediction")
    st.caption("Machine learning powered stock market forecasting")

    stock_options = {
        "TCS": "TCS.NS",
        "Reliance Industries": "RELIANCE.NS",
        "Infosys": "INFY.NS"
    }

    col1, col2 = st.columns(2)

    with col1:
        selected_stock = st.selectbox(
            "Choose stock",
            list(stock_options.keys()),
            key="prediction_stock"
        )

    with col2:
        period = st.selectbox(
            "Historical data",
            ["6mo", "1y", "2y", "5y"],
            key="prediction_period"
        )

    df = get_stock_data(
        stock_options[selected_stock],
        period
    )

    if not df.empty and len(df) >= 40:

        df = df.sort_index().copy()

        # FEATURE ENGINEERING

        features = pd.DataFrame(index=df.index)

        for lag in range(1, 6):
            features[f"Lag_{lag}"] = df["Close"].shift(lag)

        features["SMA_5"] = df["Close"].rolling(5).mean()
        features["SMA_10"] = df["Close"].rolling(10).mean()
        features["Volume"] = df["Volume"]

        features["Target"] = df["Close"].shift(-1)

        dataset = features.dropna()

        feature_columns = [
            "Lag_1", "Lag_2", "Lag_3",
            "Lag_4", "Lag_5",
            "SMA_5", "SMA_10", "Volume"
        ]

        X = dataset[feature_columns]
        y = dataset["Target"]

        # CHRONOLOGICAL TRAIN-TEST SPLIT

        split = int(len(dataset) * 0.8)

        X_train = X.iloc[:split]
        X_test = X.iloc[split:]

        y_train = y.iloc[:split]
        y_test = y.iloc[split:]

        # TRAIN MACHINE LEARNING MODEL

        model = LinearRegression()
        model.fit(X_train, y_train)

        predictions = model.predict(X_test)

        # MODEL EVALUATION

        mae = mean_absolute_error(y_test, predictions)

        rmse = np.sqrt(
            mean_squared_error(y_test, predictions)
        )

        r2 = r2_score(y_test, predictions)

        # NEXT SESSION ESTIMATE

        latest_features = features[
            feature_columns
        ].dropna().iloc[[-1]]

        next_prediction = model.predict(
            latest_features
        )[0]

        latest_price = df["Close"].iloc[-1]

        change = (
            (next_prediction - latest_price)
            / latest_price
        ) * 100

        # PREDICTION METRICS

        st.markdown("---")
        st.subheader("Prediction Overview")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Latest Closing Price",
            f"₹{latest_price:,.2f}"
        )

        c2.metric(
            "Predicted Next Session",
            f"₹{next_prediction:,.2f}",
            f"{change:+.2f}%"
        )

        c3.metric(
            "Model R² Score",
            f"{r2:.3f}"
        )

        st.markdown("---")
        st.subheader("Model Performance")

        m1, m2, m3 = st.columns(3)

        m1.metric("MAE", f"₹{mae:.2f}")
        m2.metric("RMSE", f"₹{rmse:.2f}")
        m3.metric("Training Samples", len(X_train))

        # ACTUAL VS PREDICTED CHART

        st.markdown("---")
        st.subheader("Actual vs Predicted Prices")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=y_test.index,
                y=y_test,
                mode="lines",
                name="Actual Price",
                line=dict(color="#16C784", width=2)
            )
        )

        fig.add_trace(
            go.Scatter(
                x=y_test.index,
                y=predictions,
                mode="lines",
                name="Predicted Price",
                line=dict(
                    color="#4DA3FF",
                    width=2,
                    dash="dash"
                )
            )
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0D1B2A",
            plot_bgcolor="#102238",
            font=dict(color="#DCE7F2"),
            height=450,
            hovermode="x unified",
            xaxis_title="Date",
            yaxis_title="Stock Price (INR)",
            legend=dict(
                orientation="h",
                y=1.12
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # MODEL INFORMATION

        st.markdown("---")
        st.subheader("About the Prediction Model")

        st.write("""
        StockSense uses Linear Regression to estimate
        the next trading session's closing price.

        Input features include:
        - Previous five closing prices
        - 5-day moving average
        - 10-day moving average
        - Trading volume

        The model is trained on historical data and
        evaluated using a chronological test dataset.
        """)

        st.info(
            "This is an experimental educational prediction. "
            "It is not a guaranteed forecast or investment advice."
        )

    else:
        st.warning(
            "Insufficient historical data to train the model. "
            "Please select another stock or time period."
        )

# ---------------- STOCK WATCHLIST ----------------

elif page == "Watchlist":
    import sqlite3

    st.title("⭐ My Stock Watchlist")
    st.caption("Keep track of your favourite stocks.")

    stock_options = {
        "TCS": "TCS.NS",
        "Infosys": "INFY.NS",
        "Reliance Industries": "RELIANCE.NS",
        "HDFC Bank": "HDFCBANK.NS",
        "ICICI Bank": "ICICIBANK.NS",
        "Wipro": "WIPRO.NS",
        "Tata Motors": "TATAMOTORS.NS",
        "ITC": "ITC.NS"
    }

    conn = sqlite3.connect("stocksense.db")
    cursor = conn.cursor()

    st.subheader("➕ Add Stock")

    selected_stock = st.selectbox(
        "Choose a stock",
        list(stock_options.keys()),
        key="watchlist_stock"
    )

    if st.button("Add to Watchlist"):
        cursor.execute(
            "SELECT id FROM watchlist WHERE stock = ?",
            (selected_stock,)
        )

        if cursor.fetchone():
            st.warning("This stock is already in your watchlist.")
        else:
            cursor.execute(
                "INSERT INTO watchlist (stock, symbol) VALUES (?, ?)",
                (selected_stock, stock_options[selected_stock])
            )
            conn.commit()
            st.success(f"{selected_stock} added successfully!")
            st.rerun()

    st.divider()
    st.subheader("📊 Your Watchlist")

    cursor.execute("SELECT id, stock, symbol FROM watchlist")
    watchlist_items = cursor.fetchall()
    conn.close()

    if watchlist_items:
        for item_id, stock, symbol in watchlist_items:
            st.markdown(f"### 📈 {stock}")

            try:
                data = get_stock_data(symbol, "5d")

                if not data.empty:
                    current_price = float(data["Close"].iloc[-1])

                    if len(data) >= 2:
                        previous_price = float(data["Close"].iloc[-2])
                    else:
                        previous_price = current_price

                    change = current_price - previous_price
                    percent = (
                        change / previous_price * 100
                        if previous_price else 0
                    )

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Current Price", f"₹{current_price:,.2f}")
                    col2.metric("Daily Change", f"₹{change:,.2f}")
                    col3.metric("Change %", f"{percent:.2f}%")
                else:
                    st.warning("Stock price data is unavailable.")

            except Exception:
                st.warning("Unable to fetch stock price right now.")

            if st.button("Remove Stock", key=f"remove_watch_{item_id}"):
                conn = sqlite3.connect("stocksense.db")
                conn.execute(
                    "DELETE FROM watchlist WHERE id = ?",
                    (item_id,)
                )
                conn.commit()
                conn.close()
                st.rerun()

            st.divider()

    else:
        st.info("Your watchlist is empty. Add your first stock!")

elif page != "Dashboard":

    st.title(page)

    st.info(
        f"The {page} workspace will be developed in our next module."
    )

    st.stop()

st.markdown("""
<div class="hero">
    <div class="hero-title">
        Welcome to StockSense
    </div>
    <div class="hero-subtitle">
        Intelligent insights for smarter market decisions.
        Explore Indian equities with interactive analytics.
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- MARKET OVERVIEW ----------------

st.markdown('<div class="section-title">Market Overview</div>',
            unsafe_allow_html=True)

indices = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK"
}

market_cols = st.columns(3)

for col, (name, symbol) in zip(market_cols, indices.items()):
    with col:
        result = get_market_info(symbol)

        if result:
            current, change, pct = result
            st.metric(
                name,
                f"{current:,.2f}",
                f"{change:+,.2f} ({pct:+.2f}%)"
            )
        else:
            st.metric(name, "Unavailable")

st.markdown("---")

# ---------------- STOCK CHART ----------------

st.markdown('<div class="section-title">Market Analytics</div>',
            unsafe_allow_html=True)

chart_col, summary_col = st.columns([2.3, 1])

stock_options = {
    "TCS": "TCS.NS",
    "Reliance Industries": "RELIANCE.NS",
    "Infosys": "INFY.NS"
}

with chart_col:

    selected = st.selectbox(
        "SELECT STOCK",
        list(stock_options.keys())
    )

    period_options = {
        "1 Month": "1mo",
        "3 Months": "3mo",
        "6 Months": "6mo",
        "1 Year": "1y",
        "5 Years": "5y"
    }

    selected_period = st.selectbox(
        "TIME PERIOD",
        list(period_options.keys())
    )

    try:
        df = get_stock_data(
            stock_options[selected],
            period_options[selected_period]
        )

        if not df.empty:

            candle_colors = [
                "#16C784" if c >= o else "#EA3943"
                for o, c in zip(df["Open"], df["Close"])
            ]

            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.04,
                row_heights=[0.75, 0.25]
            )

            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    increasing_line_color="#16C784",
                    decreasing_line_color="#EA3943",
                    name="Price"
                ),
                row=1,
                col=1
            )

            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df["Volume"],
                    marker_color=candle_colors,
                    opacity=0.65,
                    name="Volume"
                ),
                row=2,
                col=1
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0D1B2A",
                plot_bgcolor="#102238",
                font=dict(
                    family="Arial",
                    color="#DCE7F2",
                    size=12
                ),
                height=580,
                margin=dict(l=15, r=15, t=25, b=15),
                showlegend=False,
                xaxis_rangeslider_visible=False,
                hovermode="x unified"
            )

            fig.update_xaxes(
                showgrid=False,
                rangeslider_visible=False
            )

            fig.update_yaxes(
                title_text="Price (INR)",
                gridcolor="#24394F",
                row=1,
                col=1
            )

            fig.update_yaxes(
                title_text="Volume",
                gridcolor="#24394F",
                row=2,
                col=1
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:
            st.warning("No market data available.")

    except Exception as error:
        st.error(f"Chart error: {error}")

# ---------------- STOCK SUMMARY ----------------

with summary_col:

    st.markdown("### Stock Summary")

    if 'df' in locals() and not df.empty:

        latest = df.iloc[-1]

        current = float(latest["Close"])
        opening = float(latest["Open"])
        high = float(latest["High"])
        low = float(latest["Low"])
        volume = float(latest["Volume"])

        st.metric("Latest Close", f"₹{current:,.2f}")
        st.metric("Opening Price", f"₹{opening:,.2f}")
        st.metric("Day High", f"₹{high:,.2f}")
        st.metric("Day Low", f"₹{low:,.2f}")
        st.metric("Trading Volume", f"{volume:,.0f}")

        st.markdown("""
        <div style="
            background:#14283D;
            border:1px solid #24425C;
            border-radius:12px;
            padding:15px;
            color:#AFC4D4;
            font-size:12px;">
            Data provided through Yahoo Finance.
            Prices may be delayed and are not guaranteed
            to represent live exchange quotes.
        </div>
        """, unsafe_allow_html=True)

    else:
        st.warning("Stock summary unavailable.")

# ---------------- WATCHLIST ----------------

st.markdown("---")
st.markdown('<div class="section-title">Market Watchlist</div>',
            unsafe_allow_html=True)

watch_cols = st.columns(3)

for col, (name, symbol) in zip(
    watch_cols,
    stock_options.items()
):
    with col:
        result = get_market_info(symbol)

        if result:
            price, change, pct = result

            st.metric(
                name,
                f"₹{price:,.2f}",
                f"{pct:+.2f}%"
            )
        else:
            st.metric(name, "Unavailable")

# ---------------- FOOTER ----------------

st.markdown("---")

st.markdown("""
<div style="text-align:center;padding:15px;">
    <div style="font-size:18px;font-weight:750;color:#16C784;">
        ◈ StockSense
    </div>
    <div style="color:#8295AA;font-size:12px;">
        Smart Market Analytics &nbsp; | &nbsp; Built with Python
    </div>
    <div style="color:#64788D;font-size:11px;margin-top:8px;">
        Educational project. Not investment advice.
    </div>
</div>
""", unsafe_allow_html=True)
