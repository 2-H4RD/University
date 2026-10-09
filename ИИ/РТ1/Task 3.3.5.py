list = [0,1,2,3,4,5,6,7,8,9]
l1= list[0::2]
l1=l1[::-1]
mem=0
for i in range(0,len(list),2):
      list[i]=l1[mem]
      mem+=1
print(list)
