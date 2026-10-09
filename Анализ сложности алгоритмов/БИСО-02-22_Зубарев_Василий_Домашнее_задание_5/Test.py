import codecs
import random
import  pandas
import xlsxwriter
import matplotlib.pyplot as plt
import numpy
def KPM_poisk(string):
    temp=random.randint(0,992)
    my_word=string[temp:temp+8:1]
    f = 1;  # счетчик трудоемкости
    for i in range(992):
        f+=2#проверка условия и инкремент
        if(my_word[0]==string[i]):
            f+=3#два обращения по индексу и сравнение
            f+=1#инициализация счетчика второго цикла
            is_found = True;f += 1
            for g in range(1,8,1):
                f += 2#проверка условия и инкремент
                if(my_word[g]!=string[i+g]):
                    f+=4#сравнение, два обращения по индексу, сложение
                    is_found = False;f+=1
                    i=i+g;f+=2
                    break;f+=1
            f+=1
            if(is_found==True):
                return f+1;
    f+=1
    return f
l=20000
with codecs.open("ДЗ_5.txt",encoding='utf-8') as q:
    string=q.read(1000)
attempt=[]
A=[]
for p in range(l):
    A.append(KPM_poisk(string))
    attempt.append(p+1)
A= numpy.sort(A)
A_50=A[:50]
B1=A_50[::2]
B2=A_50[1::2]
C=[]
for i in range(50):
    if A[i]%2==0:
        C.append(A[i])
data_set={'Попытка': attempt, 'Трудоемкость': A}
df=pandas.DataFrame(data_set)
with pandas.ExcelWriter('ДЗ-5.xlsx', engine='xlsxwriter') as writer:
    df.to_excel(writer,sheet_name='Лист 2')
    sheet = writer.sheets['Лист 2']
    sheet.set_column('A:C', 15)
print("Минимальное значение массива A =", numpy.min(A))
print("Максимальное значение массива A =", numpy.max(A))
print("Размерность Массива А = ", numpy.array(A).shape)
print("Количество размерностей массива А = ", numpy.array(A).ndim)
print("Массив А[50]\n", A_50)
print("Масив B1\n", B1)
print("Массив B2\n", B2)
print("Склеенные масивы B1 и B2\n", numpy.vstack((B1,B2)))
print("Массив С\n", C)
print("Среднее значение массива А = ", numpy.average(A))
print("Медина  массива А = ", numpy.median(A))
print("Дисперсия массива A = ", numpy.var(A))
print("Среднее квадратичное отклонение массива А = ", numpy.std(A))
fig, axs = plt.subplots(2, 3, figsize=(20, 7))
axs = axs.flatten()
for i in range(5):
    axs[i].hist(A, bins=(i+1)*10)
    axs[i].set_title(f"{(i+1)*10} интервалов")
plt.tight_layout()
plt.show()
print("Квантиль 0.1 = ", numpy.quantile(A, 0.1))
print("Квантиль 0.1 = ", numpy.quantile(A, 0.3))
print("Квантиль 0.1 = ", numpy.quantile(A, 0.5))
print("Квантиль 0.1 = ", numpy.quantile(A, 0.9))
plt.boxplot(A)
plt.title("Ящик с усами массива А")
plt.show()
