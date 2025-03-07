import itertools
def sum_range(start, end):
    if start > end:
        end, start = start, end
    return sum(range(start, end + 1))
print(sum_range(2, 12))
print(sum_range(-4, 4))
print(sum_range(3, 2))