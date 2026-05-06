from queries import *

print("All Students:")
print(get_all_students())

print("\nMarks of Gayathri:")
print(get_student_marks("Gayathri"))

print("\nHigh Scorers:")
print(get_high_scorers())

from queries import *

while True:
    question = input("Ask your question (or type exit): ")

    if question.lower() == "exit":
        break

    elif "all students" in question.lower():
        print(get_all_students())

    elif "marks of" in question.lower():
        name = question.split("marks of")[-1].strip().capitalize()
        print(get_student_marks(name))

    elif "high scorers" in question.lower():
        print(get_high_scorers())

    else:
        print("Sorry, I don't understand the question.")