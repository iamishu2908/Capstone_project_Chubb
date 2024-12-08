from flask import Flask, render_template
import pyodbc
import pandas as pd
import plotly.express as px

app = Flask(__name__)

# SQL Server Connection
server = 'ISHUDELL'
database = 'health'
username = 'inf_dev_new'
password = 'inf_dev_new'
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

@app.route('/')
def index():
    # Connect to the database
    conn = pyodbc.connect(connection_string)
    
    # Query 1: Total Claim Amount by Category
    query1 = """
    SELECT dim_category.CATEGORY_NAME, SUM(fact.CLAIM_AMOUNT) AS Total_Claim_Amount
    FROM fact
    join dim_category on fact.CATEGORY_ID = dim_category.CATEGORY_ID
    GROUP BY dim_category.CATEGORY_NAME
    """
    df1 = pd.read_sql_query(query1, conn)
    
    # Visualization 1: Bar Chart
    fig1 = px.bar(df1, x='CATEGORY_NAME', y='Total_Claim_Amount', title="Total Claim Amount by Category")
    plot1 = fig1.to_html(full_html=False)
    
    # Query 2: Average Preauth Amount by Surgery
    query2 = """
    SELECT s.SURGERY, AVG(f.PREAUTH_AMT) AS Avg_Preauth_Amount
    FROM fact as f
    JOIN DIM_SURGERY as s ON f.SURGERY_ID=s.SURGERY_ID
    GROUP BY s.SURGERY
    """
    df2 = pd.read_sql_query(query2, conn)
    
    # Visualization 2: Line Chart
    fig2 = px.line(df2, x='SURGERY', y='Avg_Preauth_Amount', title="Average Preauth Amount by Surgery")
    plot2 = fig2.to_html(full_html=False)
    
    # Query 3: Gender-Based Analysis
    query3 = """
    SELECT DIM_SEX.SEX, SUM(fact.CLAIM_AMOUNT) AS Total_Claim_Amount
    FROM fact
    JOIN DIM_SEX ON fact.SEX_ID=DIM_SEX.SEX_ID
    GROUP BY DIM_SEX.SEX
    """
    df3 = pd.read_sql_query(query3, conn)
    
    # Visualization 3: Pie Chart
    fig3 = px.pie(df3, names='SEX', values='Total_Claim_Amount', title="Claim Amount Distribution by Gender")
    plot3 = fig3.to_html(full_html=False)

     
    # Query 4: AGE-Based Analysis
    query4 = """
    SELECT DIM_AGE.AGE, SUM(fact.CLAIM_AMOUNT) AS Average_Claim_Amount
    FROM fact
    JOIN DIM_AGE ON fact.AGE_ID=DIM_AGE.AGE_ID
    GROUP BY DIM_AGE.AGE
    """
    df4 = pd.read_sql_query(query4, conn)
    
    # Visualization 4: Line Chart
    fig4 =  px.line(df4, x='AGE', y='Average_Claim_Amount', title="Average Claim mount Distribution by AGE")
    plot4 = fig4.to_html(full_html=False)
    
    conn.close()
    
    return render_template('index.html', plot1=plot1, plot2=plot2, plot3=plot3,plot4=plot4)

if __name__ == "__main__":
    app.run(debug=True)
