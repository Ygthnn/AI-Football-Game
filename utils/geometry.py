import math

def distance(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return (dx**2 + dy**2) ** 0.5

def direction_vector(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dist = distance(a, b)
    if dist == 0:
        return 0, 0
    return dx / dist, dy / dist

def angle_between(a, b):
    dot = a[0] * b[0] + a[1] * b[1]
    mag_a = (a[0]**2 + a[1]**2) ** 0.5
    mag_b = (b[0]**2 + b[1]**2) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0
    return math.acos(dot / (mag_a * mag_b))
