# Marketing Campaign Analytics
> An end-to-end suite from raw CSV to SQL modeling and dual-dashboard (Streamlit & Superset) visualization.

## Project Overview
This project transforms raw marketing data into actionable business intelligence. It covers the full lifecycle:
1.  **Exploratory Data Analysis (EDA):** Performed in Jupyter with heavy feature engineering (Age, Spending, Segments).
2.  **Database Modeling:** Migration of cleaned data to **MySQL** for relational querying and View creation.
3.  **BI Dashboards:** 
    * **Streamlit:** Interactive Python app with an integrated **AI Data Explorer** (Ollama/Groq).
    * **Apache Superset:** Enterprise-grade reporting using SQL Lab and specialized views.

---

## Technology Stack
* **Data Science:** Python (Pandas, NumPy, Plotly)
* **Notebook:** Jupyter (EDA & Data Cleaning)
* **Database:** MySQL 8.0 (Relational Storage & Views)
* **Web App:** Streamlit (Dashboard + LLM Integration)
* **BI Tool:** Apache Superset
* **AI/LLM:** Ollama (Local) or Groq API (Cloud)

---

## Project Structure
```text
marketing_analytics/
├── Data/
│   ├── marketing_campaign_data.csv    # Raw Data
│   └── marketing_clean.csv            # Cleaned Data (Exported from Notebook)
├── sql/
│   ├── EDA_marketing.ipynb            # Cleaning & Feature Engineering Pipeline
│   └── analytics_queries_mysql.sql    # DDL, 6 Views, and 10 Business Queries
├── Outputs/
│   └── marketing_clean.csv            # Cleaned CSV for MySQL Import
├── app/  
│   ├── app.py                         # Streamlit Dashboard
│   └── .env                           # Database Credentials (Local only)
├── dashboard_apache_superset.zip  
└── README.md
```

---

## How to Run Locally

### 1. Data Preparation (Jupyter)
Open `sql/EDA_marketing.ipynb` and run all cells. This will:
* Perform outlier removal and normalization.
* Generate 17 new features (Segments, Age Bands, etc.).
* **Action:** Look for the generated `marketing_clean.csv` in your folder.

### 2. Database Setup (MySQL Workbench)
1.  **Create DB:** Run the `CREATE DATABASE marketing_analytics;` command.
2.  **Import Data:** Use the **Table Data Import Wizard** in MySQL Workbench to load `marketing_clean.csv` into a table named `customers`.
3.  **Run Scripts:** Execute `sql/analytics_queries_mysql.sql` to generate the 6 analytical views required for the dashboards.

### 3. Launch Streamlit App
```bash
# Install dependencies
pip install pandas sqlalchemy pymysql streamlit plotly python-dotenv

# Set up your .env file with MYSQL_USER, MYSQL_PASSWORD, etc.

# Run the app
cd app
streamlit run app.py
```

### 4. Connect Apache Superset
1.  Point Superset to your MySQL URI: `mysql://user:pass@localhost/marketing_analytics`.
2.  Add the **Views** (starting with `v_`) as Datasets.
3.  Import or build charts using the pre-aggregated SQL views.

---