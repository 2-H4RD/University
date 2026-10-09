class Rational:
    @staticmethod
    def gcd(a,b):
        while (b != 0):
            (a,b) = (b, a%b)
        return a

    @staticmethod
    def sgn(x):
        if x>0:
            return 1
        elif x<0:
            return -1
        else:
            return 0

    def __init__(self,n,d):
        if n==0:
            self.num=0
            self.den=1
        else:
            z=self.sgn(n)*self.sgn(d)
            n=abs(n)
            d=abs(d)
            k=self.gcd(n, d)
            self.num=z*n//k
            self.den=d//k

    def __str__(self):
        if self.num==0:
            return "0"
        else:
            return str(self.num)+"/"+str(self.den)

    def __add__(self,o):
        n1=self.num
        d1=self. den
        if type(o)==int:
            n2=0
            d2=1
        else:
            n2=o.num
            d2=o.den
        n=n1*d2+n2*d1
        d=d1*d2
        return Rational(n,d)

    def __radd__(self,o):
        n1=self.num
        d1=self.den
        if type(o)==int:
            n2=0
            d2=1
        else:
            n2=o.num
            d2=o.den
        n=n1*d2+n2*d1
        d=d1*d2
        return Rational(n, d)

    def __sub__(self,o):
        n1=self.num
        d1=self. den
        n2=o.num
        d2=o.den
        n=n1*d2-n2*d1
        d=d1*d2
        return Rational(n, d)

    def __mul__(self,o):
        n1=self.num
        d1=self.den
        n2=o.num
        d2=o.den
        n=n1*n2
        d=d1*d2
        return Rational(n, d)

    def __floordiv__(self,o):
        n1=self.num
        d1=self.den
        n2=o.num
        d2=o.den
        n=n1*d2
        d=d1*n2
        return Rational(n, d)

d1=Rational(1,2)
d2=Rational(1,3)
d3=d1+d2
print(d3)
d4=d1-d2
print(d4)
d5=d1*d2
print(d5)
d6=d1*d2
print(d6)
d7=d1//d2
print(d7)
d8=6+d1
print(d8)