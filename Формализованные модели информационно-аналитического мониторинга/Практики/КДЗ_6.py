import numpy as np
# Матрица выигрышей
A=np.array([
    [7, 8, 10, 9],
    [5, 6, 7, 14],
    [11, 7, 6, 12],
    [10, 11, 9, 4],
    [1, 2, 1, 2],
    [2, 1, 2, 4],
    [3, 3, 2, 2],
    [4, 1, 3, 3],
    [7, 4, 10, 6],
    [4, 5, 6, 14],
    [10, 7, 5, 12],
    [3, 6, 4, 10],
    [5, 3, 8, 4],
    [2, 4, 5, 12],
    [8, 6, 3, 11],
    [1, 5, 2, 10]
])
vald=np.empty((16,2),dtype="object")
sevidg=np.empty((16,2),dtype="object")
gurviz=np.empty((16,2),dtype="object")
baies=np.empty((16,2),dtype="object")
laplas=np.empty((16,2),dtype="object")
vouting = np.empty((17,7),dtype="object")
pi=np.array([0.1,0.4,0.4,0.1],dtype="float")
bi= np.array([0,0,0,0])
for i in range(len(A)):
    baies_sum = 0
    laplas_sum = 0
    for j in range(len(A[i])):
        if A[i][j]>bi[j]:
            bi[j]= A[i][j]
        baies_sum+=A[i][j]*pi[j]
        laplas_sum+=A[i][j]*0.25
    vald[i][0],vald[i][1]=f"x{i+1}",str(min(A[i]))
    gurviz[i][0], gurviz[i][1] = f"x{i + 1}", str(round((0.6*min(A[i])+0.4*max(A[i])),2))
    baies[i][0], baies[i][1] = f"x{i + 1}", str(round(baies_sum,2))
    laplas[i][0], laplas[i][1] = f"x{i + 1}", str(round(laplas_sum,2))
B = np.empty((16,4),dtype="int")
for i in range(len(A)):
    r_max = 0
    for j in range(len(A[i])):
        B[i][j]= bi[j]- A[i][j]
        if B[i][j] >r_max:
            r_max= B[i][j]
    sevidg[i][0], sevidg[i][1] = f"x{i + 1}", str(r_max)
vald=dict(vald)
sevidg=dict(sevidg)
gurviz=dict(gurviz)
baies=dict(baies)
laplas=dict(laplas)
for i in range(len(vouting)):
    if i == 0:
        head = ['Проект', 'Вальд', 'Сэвидж', 'Гурвиц', 'Байес', 'Лаплас', 'Итог']
        for j in range(len(vouting[i])):
            vouting[i][j]= head[j]
    else:
        for j in range(len(vouting[i])):
            if j ==0:
                vouting[i][j]= f"x{i}"
            if j ==1:
                if vouting[i][0] in max(vald,key=vald.get):
                    vouting[i][j]= '1'
                else:
                    vouting[i][j] = '0'
            if j ==2:
                if vouting[i][0] in min(sevidg,key=sevidg.get):
                    vouting[i][j]= '1'
                else:
                    vouting[i][j] = '0'
            if j ==3:
                if vouting[i][0] in max(gurviz,key=gurviz.get):
                    vouting[i][j]= '1'
                else:
                    vouting[i][j] = '0'
            if j ==4:
                if vouting[i][0] in max(baies,key=baies.get):
                    vouting[i][j]= '1'
                else:
                    vouting[i][j] = '0'
            if j ==5:
                if vouting[i][0] in max(laplas,key=laplas.get):
                    vouting[i][j]= '1'
                else:
                    vouting[i][j] = '0'
            if j ==6:
                summ=0
                for k in range (1,6):
                    if vouting[i][k]=='1':
                        summ +=1
                vouting[i][j]= str(summ)
print(vouting)
