# Simple calculator supporting addition, subtraction, multiplication, division
# Enter two numbers and choose an operation.

def calculator():
    print('Simple calculator')
    try:
        a = float(input('Enter first number: '))
        b = float(input('Enter second number: '))
    except ValueError:
        print('Invalid number')
        return

    print('Choose operation:')
    print('1) Add')
    print('2) Subtract')
    print('3) Multiply')
    print('4) Divide')

    op = input('Enter 1/2/3/4: ').strip()
    if op == '1':
        print(f'{a} + {b} = {a + b}')
    elif op == '2':
        print(f'{a} - {b} = {a - b}')
    elif op == '3':
        print(f'{a} * {b} = {a * b}')
    elif op == '4':
        if b == 0:
            print('Error: division by zero')
        else:
            print(f'{a} / {b} = {a / b}')
    else:
        print('Unknown operation')

if __name__ == '__main__':
    calculator()
