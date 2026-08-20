import pandas as pd
from groq import Groq

def get_groq_client(api_key_path="groq-api.key"):
    """Loads the API key and initializes the Groq client."""
    try:
        with open(api_key_path) as f:
            api_key = f.read().strip()
        return Groq(api_key=api_key)
    except FileNotFoundError:
        return None

def process_query(client, df, user_query):
    """
    Sends the schema and query to Groq, generates code, and executes it.
    Returns: (generated_code, result_data, error_message)
    """
    llm_prompt = f"""
    You are an expert Python data analyst.
    A pandas dataframe called df is already loaded.
    
    Columns: {list(df.columns)}
    Data Types: {df.dtypes.to_dict()}
    
    Generate ONLY executable Python Pandas code.
    
    Rules:
    1. Return ONLY Python code. No markdown formatting like ```python.
    2. No explanation.
    3. Store final output in a variable named `result`.
    4. Use dataframe `df`.
    
    Question: {user_query}
    """
    
    try:
        # Call Groq API
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": llm_prompt}],
            temperature=0,
        )
        
        # Clean up markdown
        code = response.choices[0].message.content.strip()
        code = code.replace("```python", "").replace("```", "").strip()
        
        # Execute the code locally
        local_vars = {"df": df}
        exec(code, {}, local_vars)
        
        execution_result = local_vars.get("result", "Error: Variable 'result' not found.")
        return code, execution_result, None
        
    except Exception as e:
        failed_code = code if 'code' in locals() else "None generated"
        return failed_code, None, str(e)

def generate_insights(client, df):
    """
    Generates business insights based on the dataframe schema and basic statistics.
    """
    try:
        # Get basic statistics (limit to avoid token overflow)
        stats = df.describe(include='all').to_string()
        if len(stats) > 2000:
            stats = stats[:2000] + "... (truncated)"
        
        llm_prompt = f"""
        You are an expert business analyst.
        Analyze the following dataset and provide 3-5 key business insights or interesting observations.
        Format your response as a clean, readable markdown list.
        Do not include any code, just the business insights.
        IMPORTANT: Do NOT use the '$' symbol (use 'USD' instead) to prevent markdown math formatting errors.
        
        Columns: {list(df.columns)}
        Data Types: {df.dtypes.to_dict()}
        
        Summary Statistics:
        {stats}
        """
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": llm_prompt}],
            temperature=0.3,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate insights: {str(e)}"