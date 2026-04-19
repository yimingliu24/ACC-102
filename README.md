# ACC-102
# Netflix Movies Market Research (2025–2026)

An interactive **Streamlit dashboard** for exploring Netflix Top 500 global movie performance, conducting statistical analysis, and generating future investment suggestions.

---

##1. Problem & User
This project investigates how Netflix Top 500 global movies perform in terms of **viewing hours, Top 10 longevity, ranking, and release timing**.  
It is designed for **business analysts, content planners, students, and researchers** who want to explore streaming performance patterns and support future release or investment decisions through an interactive dashboard.

---

## 2. Data
- **Source:** Kaggle  
- **File Used:** `netflix_top500_global_movies_2025_2026.csv`  
- **Access Date:** `[Please replace with your actual access date]`  
- **Key Fields Used:**
  - `overall_rank`
  - `movie_title`
  - `total_hours_viewed`
  - `weeks_in_top10`
  - `best_rank`
  - `first_appeared`
  - `last_appeared`

The dataset is loaded from a **local CSV file** and cleaned in Python before analysis.

---

## 3. Methods
This project is implemented in **Python** using the following libraries:
- **Streamlit** for dashboard development
- **Pandas** and **NumPy** for data handling and preprocessing
- **Matplotlib** and **Seaborn** for visualization
- **SciPy** for statistical testing

### Main workflow
1. Load the local CSV dataset.
2. Validate file existence and check required columns.
3. Clean and preprocess the data:
   - standardize column names
   - convert numeric columns
   - parse date columns
   - fix encoding issues in movie titles
   - remove rows with missing required values
4. Generate derived variables:
   - `release_month`
   - `release_year`
   - `lifespan_days`
   - `log_total_hours`
5. Build an interactive Streamlit dashboard with:
   - sidebar filters
   - data preview
   - summary metrics
   - statistical analysis
   - top movie ranking table
   - interactive charts
   - monthly performance summary
   - executive summary
6. Create a **Future Investment Suggestions** module that recommends release months based on:
   - investment goal
   - risk preference
   - historical monthly performance

---

## 4. Key Findings
- Movies that stay longer in the **Top 10** generally show stronger viewing performance.
- Release timing may influence performance, with some months showing higher average viewing hours than others.
- Movies that reached **#1** tend to have different viewing patterns compared with those that never reached the top position.
- Monthly historical performance can be used to support **future release timing recommendations**.
- The dashboard transforms raw streaming data into a more accessible **market research and decision-support tool**.

---

## 5. How to Run

### Requirements
Install the required Python packages:

```bash
pip install streamlit pandas numpy matplotlib seaborn scipy

run: streamlit run app.py

## 6. Product Link / Demo
Netflix Movies Market Research

## 7. Limitations & Next Steps
Limitations
•	The analysis depends on the structure and quality of the Kaggle dataset.
•	The current workflow mainly focuses on ranking, viewing hours, Top 10 duration, and release dates.
•	Important additional features such as genre, country, budget, language, or production company are not included in this version.
•	The investment recommendation is based on historical monthly patterns and should be interpreted as decision support rather than prediction.
•	Results may vary depending on filter conditions and future dataset updates.
Next Steps
•	Add more metadata such as genre, country, and language for richer analysis.
•	Introduce predictive methods such as regression or forecasting models.
•	Improve visual design and chart interactivity.
•	Add file upload support instead of requiring only a local file path.
•	Deploy the dashboard online for easier public access.
