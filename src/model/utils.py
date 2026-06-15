
import random


suffix_registry = []

def rand_gen():
    return random.randint(1000, 9999)

def suffix_generator():
    suffix = rand_gen()
    while suffix in suffix_registry:
        suffix = rand_gen()
    suffix_registry.append(suffix)
    return suffix
