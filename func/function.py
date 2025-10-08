
# Problem 1

def between(value, low=0, high=0.3):
    return value >= low and value <= high

print(f"\nis 6 between 10 and 20? {between(6, 10, 20)}\n")
print(f"is 6 between 0 and 10? {between(6,0,10)}\n")
print(f"is 0.1 between 0 and 0.3? {between(0.1)}\n")

# Problem 2 

def rangef(max,step):
    i = 0
    arr = []
    while i <= max:
        arr.append(i)
        i += step
    return arr
print("\nresult: ", end='')
for i in rangef(5,0.5): print(i, end=' ')

# Problem 3

alist = rangef(1,0.25)
print("\nalist:", alist)

alist = alist + alist[::-1] 

print("\nalist:", alist)

alist.sort(key=between)

print("\nalist: ", alist)

# Problem 4

mylist = [x for x in range(0,16) if x%2 == 0 or x%3 == 0]
print("\nmylist:", mylist)


