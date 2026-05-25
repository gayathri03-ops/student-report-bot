from ai_query import generate_sql, run_query
from tabulate import tabulate

question = input("Ask: ")

sql = generate_sql(question)
print("Generated SQL:", sql)

result, columns = run_query(sql)

if isinstance(result, str) and result.startswith("Error"):
    print(result)
elif not result:
    print("No records found.")
else:
    print("\nResult:")
    print(tabulate(result, headers=columns, tablefmt="grid"))
