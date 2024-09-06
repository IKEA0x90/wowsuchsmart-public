import random
from services import command_parsing

async def roulette():
    command = "d36[s]"
    result = int(command_parsing.parse_command(command, used_by="number"))
    if not result:
        result = "0 (green)"
    elif result in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
        result = f"{result} (red)"
    else: result = f"{result} (black)"

    print(f"Rolled {result} on the roulette")
    return f"```{result}```"

async def randostats(AC, PRF, SPD, STR, DEX, CON, INT, WIS, CHA):
    d = {"ac": AC, "prf": PRF, "spd": SPD, "str": STR, "dex": DEX, "con": CON, "int": INT, "wis": WIS, "cha": CHA}

    keys = list(d.keys())
    values = list(d.values())

    random.shuffle(values)
    new_dict = dict(zip(keys, values))

    return new_dict