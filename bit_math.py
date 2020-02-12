def add(num_bits, x, y):
    mask = (2 ** num_bits) - 1
    return (x + y) & mask, (x + y) > mask

def sub(num_bits, x, y):
    mask = (2 ** num_bits) - 1
    return (x - y) & mask, (x - y) >= 0

def extract_bit(place, val):
    mask = (2 ** (place + 1)) - 1
    return (val & mask) >> place
