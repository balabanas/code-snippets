# math, list comprehensions, typing, filter
import math


def power_numbers(*args):
    """
    Takes n integers, returns list of squares
    > power_numbers(1, 2, 5, 7)
    < [1, 4, 25, 49]
    """
    return [x ** 2 for x in args]


# filter types
ODD = "odd"
EVEN = "even"
PRIME = "prime"


# def ensure_positive_int_gt_1(f):
#     def inner(n):
#         if type(n) == int and n > 1:
#             return f(n)
#         else:
#             raise TypeError(f'Got value which is not int and > 1: {n}')
#     return inner


# @ensure_positive_int_gt_1
def is_prime(n: int) -> bool:
    """Takes integer, returns True if integer is prime"""
    if n <= 1:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if (n % i) == 0:
            return False
    return True

"""

Requirements:
 - Create function filter_numbers that takes list of integers and returns list of even/odd/primes, depending on mode
  argument:
    > filter_numbers([1, 2, 3], ODD)
    < [1, 3]
    > filter_numbers([2, 3, 4, 5], EVEN)
    < [2, 4]
 - create and use constants ODD/EVEN/PRIME to check mode type, i.e. not 
   if filter_type == 'odd', but 
   if filter_type == ODD and so on.
 - use builtin function `filter`
 - create separate function is_prime in the global scope (out of filter_numbers function) to check a if a number
 is prime, and call it from filter_numbers
 - do not create is_prime to take a list and return a list. Istead, let it take an integer and return True/False
"""

def filter_numbers(nlist, mode):
    """
    Takes list of integers,
    returns evens/odds/primes, depending on mode argument
    > filter_numbers([1, 2, 3], ODD)
    < [1, 3]
    > filter_numbers([2, 3, 4, 5], EVEN)
    < [2, 4]
    """
    if mode == ODD:
        return [x for x in nlist if x % 2 != 0]
    elif mode == EVEN:
        # return [x for x in nlist if x % 2 == 0]
        return list(filter(lambda x: x % 2 == 0, nlist))
    elif mode == PRIME:
        return list(filter(is_prime, nlist))
    else:
        raise AttributeError("Wrong mode. Only ODD, EVEN, PRIME are allowed!")


if __name__ == "__main__":
    pass
