import random

chosen = []
names = [
    "Sky", "John", "Hephaestus",
    "Artemis", "Apollo", "Athena",
    "Hera", "Hestia", "Levi", 
    "Noe", "cockroach", "Abel",
    "Axel", "reeses pieces", "Sam"
]

def get_rand_name():
    while True:
        choice = random.choice(names)
        if choice in chosen:
            continue
        
        chosen.append(choice)
        return choice
    
while True:
    print(get_rand_name())