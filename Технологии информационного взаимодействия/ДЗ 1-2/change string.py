from tkinter import *
from tkinter import messagebox
def error_form(text):
    messagebox.showinfo("Ошибка ввода", text)
def moution(string):
    words = string.split()
    if len(words) == 0:
        label5.config(text='Введите строку')
        return
    try:
        index1 = int(entry1.get())
    except ValueError:
        error_form('Не указан начальный индекс или он некорректен.')
        return
    try:
        index2 = int(entry2.get())
    except ValueError:
        error_form('Не указан конечный индекс или он некорректен.')
        return
    if index1 < 1:
        error_form('Начальный индекс должен быть минимум 1 (срез должен начинаться с первого слова).')
    elif index2 > len(words):
        error_form('Конечный индекс выходит за пределы массива слов.')
    elif index1 > len(words):
        error_form('Начальный индекс выходит за пределы массива слов.')
    elif index1 > index2:
        error_form('Начальный индекс не может быть больше конечного.')
    else:
        # Перемещаем слова между индексами в конец строки
        str_a, str_b = '', ''
        for i in range(len(words)):
            if i < index1 - 1 or i > index2 - 1:
                str_b += words[i] + ' '
            else:
                str_a += words[i] + ' '
        label5.config(text=(str_b + str_a).strip())

form = Tk()
form.title('Дз 2 Зубарев')
w, h = 620, 200
l, t = (form.winfo_screenwidth() - w) // 2, (form.winfo_screenheight() - h) // 2
form.geometry(f"{w}x{h}+{l}+{t}")
label1 = Label(master=form, text='Введите строку->', font=(("Times New Roman"), 14))
label1.grid(row=0, column=0, padx=10, pady=10)
entry = Entry(master=form, width=45, font=(("Times New Roman"), 14))
entry.focus()
entry.grid(row=0, column=1, columnspan=4, pady=10, sticky=NSEW)
label2 = Label(master=form, text='Начальный индекс->', font=(("Times New Roman"), 14))
label2.grid(row=1, column=0, padx=10, pady=10)
entry1 = Entry(master=form, width=3, font=(("Times New Roman"), 14))
entry1.grid(row=1, column=1, pady=10)
label3 = Label(master=form, text='Конечный индекс->', font=(("Times New Roman"), 14))
label3.grid(row=1, column=3, padx=10, pady=10)
entry2 = Entry(master=form, width=3, font=(("Times New Roman"), 14))
entry2.grid(row=1, column=4, pady=10)
label4 = Label(master=form, text='Полученная строка->', font=(("Times New Roman"), 14))
label4.grid(row=2, column=0, padx=10, pady=10)
label5 = Label(master=form, text='Введите строку', font=(("Times New Roman"), 14), justify=CENTER)
label5.grid(row=2, column=1, columnspan=4, padx=10, pady=10)
button1 = Button(text='Переместить', font=(("Times New Roman"), 14), command=lambda: moution(entry.get()))
button1.grid(row=3, column=0, pady=10, padx=10, sticky=SW)
button2 = Button(text='Закрыть', font=(("Times New Roman"), 14), command=form.destroy)
button2.grid(row=3, column=4, pady=10, padx=10, sticky=SE)
form.mainloop()
