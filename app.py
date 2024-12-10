from flask import Flask, render_template, request
import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import io
import base64

app = Flask(__name__)

def get_db_connection():
    conn = pyodbc.connect(
        'Driver={ODBC Driver 17 for SQL Server};'
        'Server=ISHUDELL;'
        'Database=health;'
        'Trusted_Connection=yes;'
    )
    return conn

@app.route('/', methods=['GET', 'POST'])
def home():
    tables = []
    table_data = {}
    conn = get_db_connection()

    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = cursor.fetchall()
        
        if 'table_name' in request.form:
            table_name = request.form['table_name']
            cursor.execute(f"SELECT * FROM {table_name}")
            column_names = [desc[0] for desc in cursor.description]
            table_data[table_name] = [dict(zip(column_names, row)) for row in cursor.fetchall()]
        
        cursor.close()
    else:

        cursor = conn.cursor()
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = cursor.fetchall()
        cursor.close()

    conn.close()

    return render_template('index.html', tables=tables, table_data=table_data)

@app.route('/sample-plots')
def sample_plots():
  
    conn = get_db_connection()
    query1 = """
    SELECT dim_category.CATEGORY_NAME, SUM(fact.CLAIM_AMOUNT) AS Total_Claim_Amount
    FROM fact
    JOIN dim_category ON fact.CATEGORY_ID = dim_category.CATEGORY_ID
    GROUP BY dim_category.CATEGORY_NAME
    """
    df1 = pd.read_sql_query(query1, conn)
    fig1 = px.bar(df1, x='CATEGORY_NAME', y='Total_Claim_Amount', title="Total Claim Amount by Category")
    plot1 = fig1.to_html(full_html=False)

    query2 = """
    SELECT s.SURGERY, AVG(f.PREAUTH_AMT) AS Avg_Preauth_Amount
    FROM fact as f
    JOIN DIM_SURGERY as s ON f.SURGERY_ID = s.SURGERY_ID
    GROUP BY s.SURGERY
    """
    df2 = pd.read_sql_query(query2, conn)
    fig2 = px.line(df2, x='SURGERY', y='Avg_Preauth_Amount', title="Average Preauth Amount by Surgery")
    plot2 = fig2.to_html(full_html=False)
    
    query3 = """
    SELECT DIM_SEX.SEX, SUM(fact.CLAIM_AMOUNT) AS Total_Claim_Amount
    FROM fact
    JOIN DIM_SEX ON fact.SEX_ID = DIM_SEX.SEX_ID
    GROUP BY DIM_SEX.SEX
    """
    df3 = pd.read_sql_query(query3, conn)
    fig3 = px.pie(df3, names='SEX', values='Total_Claim_Amount', title="Claim Amount Distribution by Gender")
    plot3 = fig3.to_html(full_html=False)
    
    query4 = """
    SELECT DIM_AGE.AGE, SUM(fact.CLAIM_AMOUNT) AS Average_Claim_Amount
    FROM fact
    JOIN DIM_AGE ON fact.AGE_ID = DIM_AGE.AGE_ID
    GROUP BY DIM_AGE.AGE
    """
    df4 = pd.read_sql_query(query4, conn)
    fig4 = px.line(df4, x='AGE', y='Average_Claim_Amount', title="Average Claim Amount Distribution by AGE")
    plot4 = fig4.to_html(full_html=False)
    
    conn.close()
    
    return render_template('sample_plots.html', plot1=plot1, plot2=plot2, plot3=plot3, plot4=plot4)

@app.route('/query', methods=['POST'])
def query():
    user_query = request.form.get('query')
    plot_type = request.form.get('plot_type')
    
    conn = get_db_connection()
    try:
        data = pd.read_sql_query(user_query, conn)
    except Exception as e:
        return f"Error executing query: {str(e)}"
    finally:
        conn.close()
    
    if data.empty:
        return "No data returned from the query."

    if len(data.columns) < 2:
        return "Query must return at least two columns for plotting."
    img = io.BytesIO()
    plt.figure(figsize=(10, 6))

    if plot_type == 'Bar':
        data.plot(kind='bar', x=data.columns[0], y=data.columns[1], legend=False)
        plt.ylabel('Value')
    elif plot_type == 'Pie':
        data.set_index(data.columns[0], inplace=True)
        data[data.columns[0]].plot(kind='pie', autopct='%1.1f%%', legend=False)
    elif plot_type == 'Line':
        data.plot(kind='line', x=data.columns[0], y=data.columns[1])
        plt.ylabel('Value')
    else:
        return "Unsupported plot type selected."

    plt.title(f'{plot_type} Plot of Query Results')
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    data.reset_index(inplace=True)
    table_html = data.to_html(classes='table table-bordered', index=False )
    
    return render_template('results.html', table=table_html, plot_url=plot_url)


if __name__ == '__main__':
    app.run(debug=True)
