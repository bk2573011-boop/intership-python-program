print("===== Student Marks Calculator =====")

name = input("Enter Student Name: ")

subject1 = float(input("Enter marks for Subject 1: "))
subject2 = float(input("Enter marks for Subject 2: "))
subject3 = float(input("Enter marks for Subject 3: "))
subject4 = float(input("Enter marks for Subject 4: "))
subject5 = float(input("Enter marks for Subject 5: "))

total = subject1 + subject2 + subject3 + subject4 + subject5
percentage = total / 5

if percentage >= 90:
    grade = "A+"
elif percentage >= 80:
    grade = "A"
elif percentage >= 70:
    grade = "B"
elif percentage >= 60:
    grade = "C"
elif percentage >= 50:
    grade = "D"
else:
    grade = "F"

print("\n===== Result =====")
print("Student Name :", name)
print("Total Marks  :", total, "/500")
print("Percentage   :", percentage, "%")
print("Grade        :", grade)

if grade == "F":
    print("Result       : Fail")
else:
    print("Result       : Pass")