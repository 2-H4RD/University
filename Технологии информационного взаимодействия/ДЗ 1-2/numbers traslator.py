from tkinter import *
from tkinter import messagebox
NUMBERS = {
    "and":0,"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90
}

def error_form(text):
    messagebox.showinfo("Ошибка ввода", text)

def convert(words):
    words = words.lower().split()
    result = 0
    correct = True
    current = 0
    units_count = 0
    tens_count = 0
    hundreds_count = 0
    if not words:
        error_form("Ввод не должен быть пустым.")
        correct = False
    else:
        has_hundred = False
        previous_number_type = None
        for word in words:
            if word not in NUMBERS and word != "hundred":
                error_form(f"Некорректное слово: {word}")
                correct = False
                break
            if word == "hundred":
                if current == 0 or has_hundred:
                    error_form(f"Некорректное использование 'hundred'.")
                    correct = False
                    break
                current *= 100
                has_hundred = True
                hundreds_count += 1
                if hundreds_count > 1:
                    error_form(f"В числе не может быть более одного числа из разряда сотен ('{word}').")
                    correct = False
                    break
                result += current
                current = 0
                previous_number_type = "hundred"
                continue
            number = NUMBERS[word]
            if previous_number_type == "units" and number < 10:
                error_form(f"Два числа единичного формата ('{word}') не могут идти подряд.")
                correct = False
                break
            if previous_number_type == "teens" and number < 10:
                error_form(f"Единицы ('{word}') не могут идти после чисел 10-19.")
                correct = False
                break
            if previous_number_type == "units" and number >=20:
                error_form(f"Десятки('{word}') не могут идти после единиц.")
                correct = False
                break
            if previous_number_type == "units" and 10<=number<=19:
                error_form(f"Числа 10-19 ('{word}') не могут идти после единиц.")
                correct = False
                break
            if previous_number_type == "teens" and 10 <= number <= 19:
                error_form(f"Два числа из диапазона 10-19 ('{word}') не могут идти подряд.")
                correct = False
                break
            if previous_number_type == "teens" and number >= 20:
                error_form(f"Десятки ('{word}') не могут следовать за числом из диапазона 10-19.")
                correct = False
                break
            if previous_number_type == "units" and number >= 20:
                error_form(f"Десятки ('{word}') не могут следовать за единичными числами ('{words[words.index(word) - 1]}').")
                correct = False
                break
            if previous_number_type == "tens" and number >= 20:
                error_form(f"Два десятичных числа ('{word}') не могут идти подряд.")
                correct = False
                break
            if previous_number_type == "tens" and 10<=number<=19:
                error_form(f"Число 10-19 ('{word}') не может идти после десятков.")
                correct = False
                break
            if number >= 20:
                tens_count += 1
                if tens_count > 1:
                    error_form(f"В числе не может быть более одного числа из разряда десятков ('{word}').")
                    correct = False
                    break
                current += number
                previous_number_type = "tens"
            elif 10 <= number <= 19:
                current += number
                previous_number_type = "teens"
            else:
                units_count += 1
                if units_count > 2:
                    error_form(f"В числе не может быть более двух чисел из разряда единиц ('{word}').")
                    correct = False
                    break
                current += number
                previous_number_type = "units"
        if correct:
            result += current
            if result >= 0 and result <= 999:
                label3.config(text=result)
            else:
                error_form('Число не включено в интервал 0-999')
        else:
            label3.config(text='Введите слово')
form=Tk()
form.title('Дз 1 Зубарев')
w,h=600,150
l,t=(form.winfo_screenwidth()-w)//2,(form.winfo_screenheight()-h)//2
form.geometry(f"{w}x{h}+{l}+{t}")
label1=Label(master=form,text='Введите запись числа ->', font=(("Times New Roman"),14))
label1.grid(row=0,column=0,padx=10,pady=10)
entry=Entry(master=form,width=30,font=(("Times New Roman"),14))
entry.focus()
entry.grid(row=0,column=1,columnspan=2, pady=10,sticky=NSEW)
label2=Label(master=form,text='Число ->', font=(("Times New Roman"),14))
label2.grid(row=1,column=0,padx=10,pady=10)
label3=Label(master=form,text='Введите слово', font=(("Times New Roman"),14),justify=CENTER)
label3.grid(row=1,column=1,columnspan=2,padx=10,pady=10)
button1=Button(text='Перевод',font=(("Times New Roman"),14),command=lambda:convert(entry.get()))
button1.grid(row=2,column=0,pady=10,padx=10,sticky=SW)
button2=Button(text='Закрыть',font=(("Times New Roman"),14),command=form.destroy)
button2.grid(row=2,column=3,pady=10,padx=10,sticky=SE)
form.mainloop()

