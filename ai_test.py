from ai_query import generate_sql, run_query

question = input("Ask: ")

sql = generate_sql(question)
print("Generated SQL:", sql)

result = run_query(sql)
print("Result:", result)