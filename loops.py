def Tayor_apprx(x, terms=5):
    result = 0
    for i in range(1,terms+1):
        result += (((-1)**(i-1))*(x-1)**i)/i
    return result

def Tayor_appr_while(x):
    result = 0
    i=0
    still_adding = True
    while still_adding:
        i += 1
        term = (((-1)**(i-1))*(x-1)**i)/i
        result += term
        if(abs(term) < 1e-7):
            still_adding = False
            break

    return result, i



x = 0.5

print("5 terms:")
print(f"f({x}) ~= {Tayor_apprx(x, 5):.9g} with 5 terms")
print("Within 10^-7:")
print(f"f({x}) ~= {Tayor_appr_while(x)[0]:.9g} with {Tayor_appr_while(x)[1]+1} terms")