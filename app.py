import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
import os

warnings.filterwarnings("ignore")
sns.set_style("whitegrid")

st.set_page_config(
    page_title="Netflix Movies Market Research",
    page_icon="🎬",
    layout="wide"
)

DEFAULT_FILE_PATH = "netflix_top500_global_movies_2025_2026.csv"

# -----------------------------
# Helper Functions
# -----------------------------
def clean_movie_titles(series):
    return (
        series.astype(str)
        .str.replace("鈥檚", "'s", regex=False)
        .str.replace("鈥檝e", "'ve", regex=False)
        .str.replace("鈥檙e", "'re", regex=False)
        .str.replace("鈥檒l", "'ll", regex=False)
        .str.replace("鈥檓", "'m", regex=False)
        .str.replace("I鈥檝e", "I've", regex=False)
        .str.replace("鈥", "'", regex=False)
        .str.replace("谩", "á", regex=False)
        .str.replace("艒", "ō", regex=False)
    )

def min_max_scale(series):
    s = pd.Series(series).astype(float)
    if len(s) == 0:
        return s
    if s.max() == s.min():
        return pd.Series([50.0] * len(s), index=s.index)
    return (s - s.min()) / (s.max() - s.min()) * 100

def get_month_name(month_num):
    month_name_map = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }
    return month_name_map.get(month_num, str(month_num))

def format_million(x):
    return f"{x / 1e6:.1f}M"

def format_billion(x):
    return f"{x / 1e9:.2f}B"

@st.cache_data
def load_and_clean_data(file_source):
    if file_source is None or str(file_source).strip() == "":
        return None, "No file path was provided.", None

    if not os.path.exists(file_source):
        return None, f"File not found: {file_source}", None

    try:
        df = pd.read_csv(file_source)
    except Exception as e:
        return None, f"Failed to read CSV file: {e}", None

    original_columns = df.columns.tolist()
    df.columns = df.columns.astype(str).str.strip()

    required_columns = [
        "overall_rank",
        "movie_title",
        "total_hours_viewed",
        "weeks_in_top10",
        "best_rank",
        "first_appeared",
        "last_appeared"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return None, f"Missing required columns: {missing_columns}", original_columns

    numeric_columns = ["overall_rank", "total_hours_viewed", "weeks_in_top10", "best_rank"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # More robust datetime parsing
    df["first_appeared"] = pd.to_datetime(df["first_appeared"], errors="coerce", infer_datetime_format=True)
    df["last_appeared"] = pd.to_datetime(df["last_appeared"], errors="coerce", infer_datetime_format=True)

    df["movie_title"] = clean_movie_titles(df["movie_title"])

    before_drop = len(df)
    df = df.dropna(subset=required_columns).copy()
    after_drop = len(df)

    if len(df) == 0:
        return None, (
            "No valid rows remain after cleaning. "
            "Possible causes: invalid dates, missing numeric values, or missing required fields."
        ), original_columns

    df["overall_rank"] = df["overall_rank"].astype(int)
    df["weeks_in_top10"] = df["weeks_in_top10"].astype(int)
    df["best_rank"] = df["best_rank"].astype(int)

    df["release_month"] = df["first_appeared"].dt.month
    df["release_year"] = df["first_appeared"].dt.year
    df["lifespan_days"] = (df["last_appeared"] - df["first_appeared"]).dt.days.clip(lower=0)
    df["log_total_hours"] = np.log1p(df["total_hours_viewed"])

    # Drop invalid release month just in case
    df = df[df["release_month"].between(1, 12, inclusive="both")].copy()

    if len(df) == 0:
        return None, "All rows were removed because release_month became invalid after date parsing.", original_columns

    clean_info = {
        "original_rows": before_drop,
        "valid_rows_after_cleaning": after_drop,
        "final_rows": len(df)
    }

    return df, None, {"original_columns": original_columns, "clean_info": clean_info}

# -----------------------------
# Title
# -----------------------------
st.title("🎬 Netflix Movies Market Research (2025–2026)")
st.markdown("Interactive dashboard for exploring Netflix Top 500 global movies data and generating future investment suggestions.")

# -----------------------------
# Load Local CSV
# -----------------------------
st.header("1. Load Local CSV File")

file_path = st.text_input("CSV file path", value=DEFAULT_FILE_PATH)

if not file_path.strip():
    st.warning("Please enter a valid CSV file path.")
    st.stop()

df, error_message, debug_info = load_and_clean_data(file_path)

if error_message is not None:
    st.error(error_message)
    if debug_info is not None:
        st.write("Detected columns in your CSV:")
        st.write(debug_info)
    st.stop()

st.success(f"Dataset loaded successfully. Total valid records: {len(df):,}")

with st.expander("Debug Info: Loaded Columns and Cleaning Summary"):
    if debug_info is not None:
        st.write("Original columns:")
        st.write(debug_info.get("original_columns", []))
        st.write("Cleaning summary:")
        st.write(debug_info.get("clean_info", {}))
    st.write("Preview of cleaned data:")
    st.dataframe(df.head(), use_container_width=True)

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")

rank_min = int(df["overall_rank"].min())
rank_max = int(df["overall_rank"].max())
rank_range = st.sidebar.slider(
    "Overall Rank Range",
    min_value=rank_min,
    max_value=rank_max,
    value=(rank_min, rank_max)
)

weeks_min = int(df["weeks_in_top10"].min())
weeks_max = int(df["weeks_in_top10"].max())
weeks_range = st.sidebar.slider(
    "Weeks in Top 10",
    min_value=weeks_min,
    max_value=weeks_max,
    value=(weeks_min, weeks_max)
)

best_rank_options = sorted(df["best_rank"].dropna().unique().tolist())
selected_best_ranks = st.sidebar.multiselect(
    "Best Rank",
    options=best_rank_options,
    default=best_rank_options
)

month_options = sorted(df["release_month"].dropna().unique().tolist())
selected_months = st.sidebar.multiselect(
    "Release Month",
    options=month_options,
    default=month_options,
    format_func=lambda x: get_month_name(x)
)

title_keyword = st.sidebar.text_input("Search Movie Title (keyword)", value="").strip()

filtered_df = df[
    (df["overall_rank"] >= rank_range[0]) &
    (df["overall_rank"] <= rank_range[1]) &
    (df["weeks_in_top10"] >= weeks_range[0]) &
    (df["weeks_in_top10"] <= weeks_range[1]) &
    (df["best_rank"].isin(selected_best_ranks)) &
    (df["release_month"].isin(selected_months))
].copy()

if title_keyword:
    filtered_df = filtered_df[
        filtered_df["movie_title"].str.contains(title_keyword, case=False, na=False)
    ].copy()

if filtered_df.empty:
    st.warning("No records match the current filters. Please widen the filter conditions.")
    st.stop()

# -----------------------------
# Data Preview
# -----------------------------
st.header("2. Filtered Dataset")
st.write(f"Filtered records: {len(filtered_df):,}")
st.dataframe(filtered_df, use_container_width=True)

# -----------------------------
# Summary Metrics
# -----------------------------
st.header("3. Summary Metrics")

total_movies = len(filtered_df)
total_viewing_hours = filtered_df["total_hours_viewed"].sum()
average_viewing_hours = filtered_df["total_hours_viewed"].mean()
median_viewing_hours = filtered_df["total_hours_viewed"].median()
average_weeks = filtered_df["weeks_in_top10"].mean()
average_lifespan = filtered_df["lifespan_days"].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Total Movies", f"{total_movies:,}")
col2.metric("Total Viewing Hours", format_billion(total_viewing_hours))
col3.metric("Average Viewing Hours", format_million(average_viewing_hours))

col4, col5, col6 = st.columns(3)
col4.metric("Median Viewing Hours", format_million(median_viewing_hours))
col5.metric("Avg Weeks in Top 10", f"{average_weeks:.2f}")
col6.metric("Avg Lifespan (Days)", f"{average_lifespan:.1f}")

# -----------------------------
# Statistical Analysis
# -----------------------------
st.header("4. Statistical Analysis")

def safe_corr(series1, series2):
    if len(series1.dropna()) < 2 or len(series2.dropna()) < 2:
        return np.nan
    return series1.corr(series2)

correlation_weeks_hours = safe_corr(filtered_df["weeks_in_top10"], filtered_df["total_hours_viewed"])
correlation_weeks_loghours = safe_corr(filtered_df["weeks_in_top10"], filtered_df["log_total_hours"])
correlation_lifespan_hours = safe_corr(filtered_df["lifespan_days"], filtered_df["total_hours_viewed"])
correlation_best_rank_hours = safe_corr(filtered_df["best_rank"], filtered_df["total_hours_viewed"])

corr_df = pd.DataFrame({
    "Metric": [
        "Weeks in Top 10 vs Total Hours",
        "Weeks in Top 10 vs Log Total Hours",
        "Lifespan Days vs Total Hours",
        "Best Rank vs Total Hours"
    ],
    "Correlation": [
        correlation_weeks_hours,
        correlation_weeks_loghours,
        correlation_lifespan_hours,
        correlation_best_rank_hours
    ]
})

st.subheader("Correlation Table")
st.dataframe(corr_df, use_container_width=True)

st.subheader("Long-running vs Short-term Hits")

long_running_movies = filtered_df[filtered_df["weeks_in_top10"] >= 8]
short_term_movies = filtered_df[filtered_df["weeks_in_top10"] <= 3]

if len(long_running_movies) > 1 and len(short_term_movies) > 1:
    t_stat_1, p_value_1 = stats.ttest_ind(
        long_running_movies["total_hours_viewed"],
        short_term_movies["total_hours_viewed"],
        equal_var=False,
        nan_policy="omit"
    )

    result_df_1 = pd.DataFrame({
        "Group": ["Long-running Hits (>=8 weeks)", "Short-term Hits (<=3 weeks)"],
        "Count": [len(long_running_movies), len(short_term_movies)],
        "Average Viewing Hours (Million)": [
            long_running_movies["total_hours_viewed"].mean() / 1e6,
            short_term_movies["total_hours_viewed"].mean() / 1e6
        ]
    })

    st.dataframe(result_df_1, use_container_width=True)
    st.write(f"**T-test p-value:** {p_value_1:.4f}")
else:
    st.info("Not enough data for long-running vs short-term t-test.")

st.subheader("Reached #1 vs Did Not Reach #1")

rank1_movies = filtered_df[filtered_df["best_rank"] == 1]
non_rank1_movies = filtered_df[filtered_df["best_rank"] != 1]

if len(rank1_movies) > 1 and len(non_rank1_movies) > 1:
    t_stat_2, p_value_2 = stats.ttest_ind(
        rank1_movies["total_hours_viewed"],
        non_rank1_movies["total_hours_viewed"],
        equal_var=False,
        nan_policy="omit"
    )

    result_df_2 = pd.DataFrame({
        "Group": ["Reached #1", "Did Not Reach #1"],
        "Count": [len(rank1_movies), len(non_rank1_movies)],
        "Average Viewing Hours (Million)": [
            rank1_movies["total_hours_viewed"].mean() / 1e6,
            non_rank1_movies["total_hours_viewed"].mean() / 1e6
        ]
    })

    st.dataframe(result_df_2, use_container_width=True)
    st.write(f"**T-test p-value:** {p_value_2:.4f}")
else:
    st.info("Not enough data for #1 vs non-#1 t-test.")

# -----------------------------
# Top Movies
# -----------------------------
st.header("5. Top Movies")

top_n = st.slider("Select number of top movies to display", min_value=5, max_value=50, value=10)

top_movies = filtered_df.nlargest(min(top_n, len(filtered_df)), "total_hours_viewed")[
    ["overall_rank", "movie_title", "total_hours_viewed", "weeks_in_top10", "best_rank"]
].copy()

top_movies["total_hours_viewed"] = (top_movies["total_hours_viewed"] / 1e6).round(1)
top_movies.columns = [
    "Overall Rank",
    "Movie Title",
    "Viewing Hours (Million)",
    "Weeks in Top 10",
    "Best Rank"
]

st.dataframe(top_movies, use_container_width=True)

# -----------------------------
# Charts
# -----------------------------
st.header("6. Interactive Charts")

chart_option = st.selectbox(
    "Choose a chart",
    [
        "Viewing Hours Distribution",
        "Weeks in Top 10 Distribution",
        "Weeks in Top 10 vs Viewing Hours",
        "Best Rank vs Viewing Hours",
        "Performance by Release Month"
    ]
)

fig, ax = plt.subplots(figsize=(10, 6))

if chart_option == "Viewing Hours Distribution":
    ax.hist(
        filtered_df["total_hours_viewed"] / 1e6,
        bins=min(30, max(5, len(filtered_df) // 2)),
        color="steelblue",
        edgecolor="black",
        alpha=0.75
    )
    ax.axvline(
        filtered_df["total_hours_viewed"].median() / 1e6,
        color="red",
        linestyle="--",
        label=f"Median = {filtered_df['total_hours_viewed'].median() / 1e6:.1f}M"
    )
    ax.set_xlabel("Viewing Hours (Million)")
    ax.set_ylabel("Number of Movies")
    ax.set_title("Distribution of Viewing Hours")
    ax.legend()

elif chart_option == "Weeks in Top 10 Distribution":
    week_counts = filtered_df["weeks_in_top10"].value_counts().sort_index()
    ax.bar(week_counts.index, week_counts.values, color="coral", edgecolor="black")
    ax.set_xlabel("Weeks in Top 10")
    ax.set_ylabel("Number of Movies")
    ax.set_title("Distribution of Weeks in Top 10")

elif chart_option == "Weeks in Top 10 vs Viewing Hours":
    x = filtered_df["weeks_in_top10"]
    y = filtered_df["total_hours_viewed"] / 1e6
    ax.scatter(x, y, alpha=0.6, color="steelblue")

    if len(filtered_df) > 1 and x.nunique() > 1:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        x_sorted = np.sort(x)
        ax.plot(x_sorted, p(x_sorted), "r--", linewidth=2)

    ax.set_xlabel("Weeks in Top 10")
    ax.set_ylabel("Viewing Hours (Million)")
    ax.set_title(f"Weeks in Top 10 vs Viewing Hours (r = {correlation_weeks_hours:.3f})" if pd.notna(correlation_weeks_hours) else "Weeks in Top 10 vs Viewing Hours")

elif chart_option == "Best Rank vs Viewing Hours":
    x = filtered_df["best_rank"]
    y = filtered_df["total_hours_viewed"] / 1e6
    ax.scatter(x, y, alpha=0.6, color="purple")
    ax.set_xlabel("Best Rank")
    ax.set_ylabel("Viewing Hours (Million)")
    ax.set_title(f"Best Rank vs Viewing Hours (r = {correlation_best_rank_hours:.3f})" if pd.notna(correlation_best_rank_hours) else "Best Rank vs Viewing Hours")
    ax.invert_xaxis()

elif chart_option == "Performance by Release Month":
    monthly_avg = filtered_df.groupby("release_month")["total_hours_viewed"].mean() / 1e6
    monthly_avg = monthly_avg.reindex(range(1, 13))
    best_month_chart = monthly_avg.idxmax() if monthly_avg.notna().any() else None
    colors = ["red" if best_month_chart is not None and m == best_month_chart else "steelblue" for m in monthly_avg.index]

    ax.bar(monthly_avg.index, monthly_avg.fillna(0), color=colors, edgecolor="black")
    ax.set_xlabel("Release Month")
    ax.set_ylabel("Average Viewing Hours (Million)")
    ax.set_title("Average Performance by Release Month")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

st.pyplot(fig)

# -----------------------------
# Monthly Summary
# -----------------------------
st.header("7. Monthly Performance Summary")

monthly_summary = filtered_df.groupby("release_month").agg(
    movie_count=("movie_title", "count"),
    average_hours=("total_hours_viewed", "mean"),
    median_hours=("total_hours_viewed", "median")
).reset_index()

if monthly_summary.empty:
    st.warning("Monthly summary cannot be generated under the current filters.")
else:
    monthly_summary["average_hours_million"] = (monthly_summary["average_hours"] / 1e6).round(2)
    monthly_summary["median_hours_million"] = (monthly_summary["median_hours"] / 1e6).round(2)
    monthly_summary["Release Month Name"] = monthly_summary["release_month"].apply(get_month_name)

    monthly_summary_display = monthly_summary[
        ["release_month", "Release Month Name", "movie_count", "average_hours_million", "median_hours_million"]
    ].copy()

    monthly_summary_display.columns = [
        "Release Month",
        "Month Name",
        "Movie Count",
        "Average Hours (Million)",
        "Median Hours (Million)"
    ]

    st.dataframe(monthly_summary_display, use_container_width=True)

# -----------------------------
# Executive Summary
# -----------------------------
st.header("8. Executive Summary")

if not filtered_df.empty:
    top_movie = filtered_df.loc[filtered_df["total_hours_viewed"].idxmax()]
    best_month_data = filtered_df.groupby("release_month")["total_hours_viewed"].mean()
    best_month = int(best_month_data.idxmax()) if len(best_month_data) > 0 else None

    summary_lines = [
        f"- Total movies analyzed: **{len(filtered_df)}**",
        f"- Total viewing hours: **{filtered_df['total_hours_viewed'].sum() / 1e9:.2f} billion**",
        f"- Average viewing hours per movie: **{filtered_df['total_hours_viewed'].mean() / 1e6:.1f} million**",
        f"- Median viewing hours per movie: **{filtered_df['total_hours_viewed'].median() / 1e6:.1f} million**",
        f"- Average weeks in Top 10: **{filtered_df['weeks_in_top10'].mean():.2f}**",
        f"- Top movie: **{top_movie['movie_title']}**",
        f"- Top movie viewing hours: **{top_movie['total_hours_viewed'] / 1e6:.1f} million**",
        f"- Best release month by average performance: **{get_month_name(best_month) if best_month is not None else 'N/A'}**"
    ]
    st.markdown("\n".join(summary_lines))
else:
    st.info("No data available for executive summary.")

# -----------------------------
# Future Investment Suggestions + Investment Score
# -----------------------------
st.header("9. Future Investment Suggestions")

st.markdown("This module turns historical analysis into decision support for future movie investment planning.")

col_a, col_b, col_c = st.columns(3)

with col_a:
    investment_goal = st.selectbox(
        "Investment Goal",
        [
            "Maximize Viewing Hours",
            "Maximize Top 10 Longevity",
            "Increase Chance of Reaching #1"
        ]
    )

with col_b:
    risk_preference = st.selectbox(
        "Risk Preference",
        [
            "Conservative",
            "Balanced",
            "Aggressive"
        ]
    )

with col_c:
    min_expected_weeks = st.slider(
        "Minimum Expected Weeks in Top 10",
        min_value=int(df["weeks_in_top10"].min()),
        max_value=int(df["weeks_in_top10"].max()),
        value=min(5, int(df["weeks_in_top10"].max()))
    )

prefer_best_months = st.checkbox("Prioritize historically strong release months", value=True)

monthly_investment = filtered_df.groupby("release_month").agg(
    movie_count=("movie_title", "count"),
    avg_hours=("total_hours_viewed", "mean"),
    median_hours=("total_hours_viewed", "median"),
    avg_weeks=("weeks_in_top10", "mean"),
    rank1_rate=("best_rank", lambda x: (x == 1).mean())
).reset_index()

if monthly_investment.empty:
    st.warning("No monthly investment data is available under the current filters.")
else:
    monthly_investment["month_name"] = monthly_investment["release_month"].apply(get_month_name)

    score_df = monthly_investment.copy()

    score_df["hours_score"] = min_max_scale(score_df["avg_hours"])
    score_df["weeks_score"] = min_max_scale(score_df["avg_weeks"])
    score_df["rank1_score"] = min_max_scale(score_df["rank1_rate"])
    score_df["sample_score"] = min_max_scale(score_df["movie_count"])
    score_df["median_score"] = min_max_scale(score_df["median_hours"])

    if investment_goal == "Maximize Viewing Hours":
        if risk_preference == "Conservative":
            w_hours, w_weeks, w_rank1, w_sample, w_median = 0.35, 0.15, 0.10, 0.25, 0.15
        elif risk_preference == "Balanced":
            w_hours, w_weeks, w_rank1, w_sample, w_median = 0.40, 0.20, 0.10, 0.15, 0.15
        else:
            w_hours, w_weeks, w_rank1, w_sample, w_median = 0.50, 0.20, 0.15, 0.05, 0.10

    elif investment_goal == "Maximize Top 10 Longevity":
        if risk_preference == "Conservative":
            w_hours, w_weeks, w_rank1, w_sample, w_median = 0.15, 0.35, 0.05, 0.25, 0.20
        elif risk_preference == "Balanced":
            w_hours, w_weeks, w_rank1, w_sample, w_median = 0.20, 0.40, 0.10, 0.15, 0.15
        else:
            w_hours, w_weeks, w_rank1, w_sample, w_median = 0.20, 0.50, 0.10, 0.05, 0.15

    else:
        if risk_preference == "Conservative":
            w_hours, w_weeks, w_rank1, w_sample, w_median = 0.15, 0.15, 0.30, 0.25, 0.15
        elif risk_preference == "Balanced":
            w_hours, w_weeks, w_rank1, w_sample, w_median = 0.20, 0.20, 0.35, 0.15, 0.10
        else:
            w_hours, w_weeks, w_rank1, w_sample, w_median = 0.20, 0.15, 0.45, 0.05, 0.15

    score_df["investment_score"] = (
        score_df["hours_score"] * w_hours +
        score_df["weeks_score"] * w_weeks +
        score_df["rank1_score"] * w_rank1 +
        score_df["sample_score"] * w_sample +
        score_df["median_score"] * w_median
    )

    if prefer_best_months:
        score_df_filtered = score_df[score_df["avg_weeks"] >= min_expected_weeks].copy()
        if not score_df_filtered.empty:
            score_df = score_df_filtered

    score_df = score_df.sort_values("investment_score", ascending=False).reset_index(drop=True)

    if score_df.empty:
        st.warning("No valid monthly data is available for investment scoring under the current filters.")
    else:
        recommended = score_df.iloc[0]

        st.subheader("Recommended Month Based on Investment Score")
        st.markdown(f"""
**Recommended Release Month:** {recommended['month_name']}  
**Investment Score:** {recommended['investment_score']:.2f} / 100  

### Why this month?
- Average viewing hours: **{recommended['avg_hours'] / 1e6:.2f} million**
- Median viewing hours: **{recommended['median_hours'] / 1e6:.2f} million**
- Average weeks in Top 10: **{recommended['avg_weeks']:.2f}**
- Rate of reaching #1: **{recommended['rank1_rate'] * 100:.2f}%**
- Historical sample size: **{int(recommended['movie_count'])} movies**
""")

        st.subheader("Strategic Interpretation")

        if investment_goal == "Maximize Viewing Hours":
            st.info("Recommendation focus: Choose months with stronger historical average and median viewing performance to maximize audience scale.")
        elif investment_goal == "Maximize Top 10 Longevity":
            st.info("Recommendation focus: Choose months with stronger staying power and more persistent Top 10 performance.")
        else:
            st.info("Recommendation focus: Choose months with a stronger historical ability to produce titles that reached #1.")

        if risk_preference == "Conservative":
            st.write("Risk profile: Conservative weighting places greater emphasis on stability, median performance, and sufficient sample size.")
        elif risk_preference == "Balanced":
            st.write("Risk profile: Balanced weighting combines performance upside with reasonable consistency.")
        else:
            st.write("Risk profile: Aggressive weighting favors breakout potential and peak success indicators over historical stability.")

        # Ranking table
        st.subheader("Investment Score Ranking by Month")

        score_display = score_df.copy()
        score_display["avg_hours_million"] = (score_display["avg_hours"] / 1e6).round(2)
        score_display["median_hours_million"] = (score_display["median_hours"] / 1e6).round(2)
        score_display["avg_weeks"] = score_display["avg_weeks"].round(2)
        score_display["rank1_rate_pct"] = (score_display["rank1_rate"] * 100).round(2)
        score_display["investment_score"] = score_display["investment_score"].round(2)

        score_display = score_display[
            [
                "release_month",
                "month_name",
                "movie_count",
                "avg_hours_million",
                "median_hours_million",
                "avg_weeks",
                "rank1_rate_pct",
                "investment_score"
            ]
        ].copy()

        score_display.columns = [
            "Release Month",
            "Month Name",
            "Movie Count",
            "Avg Viewing Hours (Million)",
            "Median Viewing Hours (Million)",
            "Avg Weeks in Top 10",
            "Reached #1 Rate (%)",
            "Investment Score"
        ]

        st.dataframe(score_display, use_container_width=True)

        # Chart
        st.subheader("Investment Support Chart")

        investment_chart = st.selectbox(
            "Choose investment chart",
            [
                "Investment Score by Month",
                "Average Viewing Hours by Month",
                "Average Weeks in Top 10 by Month",
                "Reached #1 Rate by Month"
            ]
        )

        fig2, ax2 = plt.subplots(figsize=(10, 5))

        plot_df = score_df.sort_values("release_month").copy()

        all_months = pd.DataFrame({"release_month": list(range(1, 13))})
        plot_df = all_months.merge(plot_df, on="release_month", how="left")
        plot_df["month_name"] = plot_df["release_month"].apply(get_month_name)

        recommended_month = int(recommended["release_month"])

        if investment_chart == "Investment Score by Month":
            y = plot_df["investment_score"].fillna(0)
            title = "Investment Score by Release Month"
            ylabel = "Investment Score"
            colors = ["red" if m == recommended_month else "steelblue" for m in plot_df["release_month"]]

        elif investment_chart == "Average Viewing Hours by Month":
            y = (plot_df["avg_hours"].fillna(0) / 1e6)
            title = "Average Viewing Hours by Release Month"
            ylabel = "Average Viewing Hours (Million)"
            colors = ["red" if m == recommended_month else "seagreen" for m in plot_df["release_month"]]

        elif investment_chart == "Average Weeks in Top 10 by Month":
            y = plot_df["avg_weeks"].fillna(0)
            title = "Average Weeks in Top 10 by Release Month"
            ylabel = "Average Weeks in Top 10"
            colors = ["red" if m == recommended_month else "orange" for m in plot_df["release_month"]]

        else:
            y = (plot_df["rank1_rate"].fillna(0) * 100)
            title = "Reached #1 Rate by Release Month"
            ylabel = "Reached #1 Rate (%)"
            colors = ["red" if m == recommended_month else "purple" for m in plot_df["release_month"]]

        ax2.bar(plot_df["release_month"], y, color=colors, edgecolor="black")
        ax2.set_title(title)
        ax2.set_xlabel("Release Month")
        ax2.set_ylabel(ylabel)
        ax2.set_xticks(range(1, 13))
        ax2.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

        st.pyplot(fig2)

# -----------------------------
# Download Filtered Data
# -----------------------------
st.header("10. Download Filtered Data")

csv_data = filtered_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="Download filtered dataset as CSV",
    data=csv_data,
    file_name="filtered_netflix_movies.csv",
    mime="text/csv"
)