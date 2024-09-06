import re
import random

if __name__ == "__main__":
    import statistics
    import pandas as pd
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import persistence

def roll_dice(dice_string, log = ""):

    data = persistence.load()

    forced_roll = data.get_forced_roll()
    if forced_roll:
        log += f"\n{forced_roll}"
        data.add_forced_roll(None)
        persistence.save(data)
        return forced_roll, log

    replacements = data.get_replacements()
    replacements = {str(k): str(v) for k, v in replacements.items()}
    if not data.get_replacements_active():
        replacements = {}

    percentage = "100"
    for k, v in replacements.items():
        percentage = percentage.replace(k, v)
    percentage = int(percentage)
    counts = "2"
    for k, v in replacements.items():
        counts = counts.replace(k, v)
    counts = int(counts)
    zeros = "0"
    for k, v in replacements.items():
        zeros = zeros.replace(k, v)
    zeros = int(zeros)
    ones = "1"
    for k, v in replacements.items():
        ones = ones.replace(k, v)
    ones = int(ones)

    for k, v in replacements.items():
        dice_string = dice_string.replace(k, v)

    defaults = {'percentage': percentage, 'counts': counts, 'zeros': zeros, 'ones': ones}

    # Check for parenthesis and evaluate them first
    dice_string, log = evaluate_parenthesis(dice_string, log, defaults)
        
    # Check if the string starts with a number or 'd'
    if dice_string[0].isdigit() or dice_string[0] == '.' or dice_string[0] == '-':
        if 'd' in dice_string:
            n, dice_string = re.split(r'd', dice_string, maxsplit=1)
            n, big_parameters = check_parameters(n, defaults)
            n = float(n)
        else:
            return float(dice_string) if '.' in dice_string else int(dice_string), log + f'\n{dice_string}'
    else:
        n = ones
        _, big_parameters = check_parameters("", defaults)
        dice_string = dice_string[1:] if dice_string.startswith('d') else dice_string

    # Check for multiple 'd's
    if dice_string.startswith('d'):
        d_count = len(re.findall(r'^d+', dice_string)[0])
        dice_string = dice_string[d_count:]
        dice_string, small_parameters = check_parameters(dice_string, defaults)
        result, log = roll_dice(dice_string=f'd{dice_string}', log=log) # Roll 1d{dice_string}
        step = ""
        parameters = ""
        for p in small_parameters["strings"]:
            parameters += p

        for _ in range(d_count - 1): # Apply step to all d's
            result, log = roll_dice(dice_string=f'd{result}{parameters}', log=log)

        return roll_dice(dice_string=f'{int(n)}d{result}{"[" + str(step) + "]" if step else ""}', log=log)
    
    # Get n and x if only one d
    elif 'd' in dice_string:
        x, dice_string = re.split(r'd', dice_string, maxsplit=1)

    # No d's means we reached the final number
    else:
        x = dice_string
        dice_string = ""

    # Handle special cases for x
    x, small_parameters = check_parameters(x, defaults)

    if x and float(x) == zeros:
        result = zeros
        log += f"\n{int(n)}d{x}: "
        for _ in range(int(n)): log += f"{zeros}, "
        log = log[:-2]
        return result, log
    
    if str(n) and float(n) == zeros:
        result = zeros
        log += f"\n{int(n)}d{x}: {zeros}"
        return result, log

    possible_small_rolls = list(range(1, int(float(x)) + 1))
    #possible_big_rolls = list(range(int(float(x)), int(float(x) * float(n)) + 1))

    for i in range(len(possible_small_rolls)):
        roll = str(possible_small_rolls[i])
        for k, v in replacements.items():
            roll = roll.replace(k, v)
        possible_small_rolls[i] = float(roll)

    '''
    for i in range(len(possible_big_rolls)):
            roll = str(possible_big_rolls[i])
            for k, v in replacements.items():
                roll = roll.replace(k, v)
            possible_big_rolls[i] = float(roll)
    '''

    if all(val in small_parameters["explode"] for val in possible_small_rolls):
        log += f'∞'
        result = float("inf")
        return result, log
    
    '''
    if all(val in big_parameters["explode"] for val in possible_big_rolls) and big_parameters["explode_chance"] >= percentage:
        log += f'∞'
        result = float("inf")
        return result, log
    '''

    # If x is 1
    if (isinstance(x, int) and int(x) == ones):
        return ones * n, log + f'\n{n}d{ones}: {ones * n}'
    
    # If step exists
    # TODO Step doesn't work for partial n
    if small_parameters["step"] != ones or small_parameters["include"]:
        if small_parameters["step"] != ones:
            # If step is 0, the result can be 0 / 1 or x
            if small_parameters["step"] == zeros:
                step = zeros
                faces = [small_parameters["start_with"], float(x)]
            else:
                faces = []
                decimal_places = len(str(small_parameters["step"]).split('.')[1]) if '.' in str(small_parameters["step"]) and not small_parameters["step"].is_integer() else zeros
                step = int(small_parameters["step"]) if small_parameters["step"].is_integer() else small_parameters["step"]
                i = small_parameters["start_with"]
                while i <= float(x):
                    faces.append(round(i, decimal_places))
                    i += step
        elif small_parameters["include"]:
            faces = small_parameters["include"]
            step = []

        # If there are no faces, return 0
        if not len(faces):
            return zeros, log + f'\n{n}d{x}[{step if step else faces}]: {zeros}'
        
        # If there is one face, return it
        if len(faces) == 1:
            return faces[(len(faces) - 1)], log + f'\n{n}d{x}[{step if step else faces}]: {faces[(len(faces) - 1)]}'
        
        result, log = roll_faces(n, x, faces, step if step else faces, big_parameters, small_parameters, log, defaults, replacements)
    
    elif '.' in x:
        result, log = roll_float(n, x, big_parameters, small_parameters, log, defaults, replacements)

    else:
        whole_part = int(n)
        fractional_part = n - whole_part

        result, log = roll_default(whole_part, x, big_parameters, small_parameters, log, defaults, replacements)

        if '.' in str(x):
            decimal_places = len(str(x).split('.')[1])
        else:
            decimal_places = ones
        if fractional_part:
            new_fraction = float(x) * fractional_part
            if new_fraction.is_integer():
                new_fraction = int(new_fraction)
            else:
                new_fraction = round(new_fraction, decimal_places)
            fractional_string = f'd{new_fraction}'

            for p in big_parameters["strings"]:
                fractional_string += p

            fractional_string = f'{ones}' + fractional_string
            fractional_roll, log = roll_dice(dice_string=fractional_string, log=log)
            result = result + fractional_roll

    '''
    elif '-' in x:
        result, log = roll_default(n, x, big_parameters, small_parameters, log, True, defaults, replacements)
    '''

    if dice_string:
        return roll_dice(dice_string=f"{result}d{dice_string}", log=log)
    else:
        return result, log

def evaluate_parenthesis(dice_string, log, defaults = {'percentage': 100, 'counts': 2, 'zeros': 0, 'ones': 1}):
    while '(' in dice_string:
            parenthesis = re.search(r'\(.*?\)', dice_string).group()
            inner = parenthesis[1:-1]

            if "s" in inner and not "sd" in inner:
                chance = re.match(r'(\d*)s(\d*)', inner)
                chance_mode = int(chance.group(2))
                substitute = int(chance.group(1))

                if chance_mode == None:
                    chance_mode = defaults['percentage']
                if not substitute:
                    substitute = 0

                chance = random.randint(defaults['zeros'], defaults['percentage'])
                if chance < chance_mode:
                    dice_string = dice_string.replace(parenthesis, str(substitute))
                else:
                    dice_string = dice_string.replace(parenthesis, "")

            elif "sd" in inner:
                chance = re.match(r'(\d*)sd(\d*)', inner)
                chance_mode = int(chance.group(2))
                substitute = int(chance.group(1))
                if chance_mode == None:
                    chance_mode = defaults['percentage']
                if not substitute:
                    substitute = 0
                chance = random.randint(defaults['zeros'], defaults['percentage'])
                if chance < chance_mode:
                    dice_string = dice_string.replace(parenthesis, str(substitute))
                else:
                    dice_string = dice_string.replace(parenthesis, defaults['ones'])

            else:
                result, log = roll_dice(dice_string=inner, log=log)
                dice_string = dice_string.replace(parenthesis, str(result))

    return dice_string, log
            
def check_parameters(dice_string, defaults = {'percentage': 100, 'counts': 2, 'zeros': 0, 'ones': 1}):
    parameters = {}
    parameters["reroll_chance"] = defaults['zeros']
    parameters["reroll_count"] = defaults['ones']
    parameters["reroll_direction"] = 1
    parameters["explode"] = []
    parameters["explode_chance"] = defaults['percentage']
    parameters["step"] = defaults['ones']
    parameters["start_with"] = defaults['ones']
    parameters["strings"] = []
    parameters["include"] = []

    PARAMETER_COUNT = len(parameters)
    
    regex = r'(-?\d+\.?\d*)'
    for _ in range(PARAMETER_COUNT): regex += r'(?:\[(.*?)\])?' 
    c = re.match(regex, dice_string)
    content = []

    if not dice_string:
        parameters["explode"] = []
        return None, parameters

    n = c.group(1)
    for i in range(PARAMETER_COUNT):
        content.append(c.group(i + 2))
    content = [i for i in content if i != None]

    for i in content:
        parameters["strings"].append(f"[{i}]")
        if 'm' in i:
            if i == "m":
                parameters["reroll_chance"] = defaults['percentage']
                parameters["reroll_count"] = defaults['counts']

            elif i == "-m":
                parameters["reroll_chance"] = defaults['percentage']
                parameters["reroll_count"] = defaults['counts']
                parameters["reroll_direction"] = defaults['zeros']

            else:
                matches = re.match(r"(-?\d*\.?\d*)m(\d*)", i)
                if matches.group(1):
                    parameters["reroll_count"] = float(matches.group(1))
                else:
                    parameters["reroll_count"] = defaults['counts']

                if matches.group(2):
                    reroll_chance = float(matches.group(2))
                    if reroll_chance < defaults['zeros']:
                        reroll_chance = abs(reroll_chance)
                        parameters["reroll_direction"]
                    parameters["reroll_chance"] = reroll_chance
                else:
                    parameters["reroll_chance"] = defaults['percentage']
                    
        elif 'e' in i:
            if i == "e":
                parameters["explode"] = [abs(float(n))]
            else:   
                match = re.match(r"((\d+\.\d+)|\d+)?e(.*)", i)
                if match.group(1):
                    parameters["explode_chance"] = float(match.group(1))
                if match.group(3):
                    parameters["explode"] = parse_number_range(match.group(3))
                else:
                    parameters["explode"] = [abs(float(n))]

        elif 's' in i:
            if i == 's':
                parameters["start_with"] = defaults['zeros']
            elif i == '-s':
                parameters["start_with"] = defaults['ones'] * -1
            else:
                start_with = i[1:]
                if '.' in start_with:
                    start_with = float(start_with)
                else:
                    start_with = int(start_with)
                parameters["start_with"] = start_with

        elif 'i' in i:
            if i == 'i':
                parameters["include"] = []
            else:
                if i.startswith("i"):
                    parameters["include"] = parse_number_range(i[1:])
                else:
                    pass

        else:
            parameters["step"] = float(i)
                
    return n, parameters

def parse_number_range(s):
    s = s.strip().replace(' ', '')
    parts = s.split(',')
    output = []

    try:
        for part in parts:
            if '-' in part:
                range_parts = part.split('-')
                if len(range_parts) != 2:
                    raise ValueError
                output.extend(list(range(int(range_parts[0]), int(range_parts[1]) + 1)))
            else:
                output.append(int(part))
    except ValueError:
        return []

    output = sorted(list(set(output)))

    return output

def roll_placeholder(n, x, big_parameters, small_parameters, log, is_float, roll_method, defaults = {'percentage': 100, 'counts': 2, 'zeros': 0, 'ones': 1}, replacements = []):
    all_rolls = []
    chosen_roll = 0
    result = 0

    '''
        local_result is equal to explode rolls
            and result is 0 (to guarantee rolling once)
                or big explode can happen
        and local_result is not 0 (to guarantee rolling once)
    '''
    while 1:
        chance = random.randint(defaults['zeros'], defaults['percentage'])
        
        if chance < big_parameters["reroll_chance"]:
            big_rolls = [roll_big(n, x, small_parameters, is_float, roll_method, defaults, replacements) for _ in range(big_parameters["reroll_count"])]
        else:
            big_rolls = [roll_big(n, x, small_parameters, is_float, roll_method, defaults, replacements)]

        big_numeric_rolls = []
        for v in big_rolls:
            roll, _ = v
            big_numeric_rolls.append(roll)

        if big_parameters["reroll_direction"] == 1:
            chosen_roll = max(big_numeric_rolls)
        else:
            chosen_roll = min(big_numeric_rolls)

        all_rolls.append((chosen_roll, big_rolls))

        local_result = chosen_roll
        result += chosen_roll

        chance = random.randint(defaults['zeros'], defaults['percentage'])

        if local_result not in big_parameters["explode"] or chance >= big_parameters["explode_chance"]:
            break
    
    for v in all_rolls:
        chosen_roll, big_rolls = v
        if chosen_roll.is_integer():
            chosen_roll = int(chosen_roll)
        log += f'{chosen_roll}'

        if len(big_rolls) > 1:
            return result, log

        for v2 in big_rolls:
            _, small_rolls = v2

            if len(small_rolls) > 1 or (len(small_rolls) > 1 and len(small_rolls[0]) > 1):
                log += f' = ['

            for v3 in small_rolls:
                for v4 in v3:
                    chosen_small_roll, smol_rols = v4

                    if len(big_rolls) > 1 or len(smol_rols) > 1:
                        log += f'('
                    
                    if len(small_rolls) > 1 or len(small_rolls[0]) > 1 or len(smol_rols) > 1 or len(big_rolls) > 1:
                        smol_rols =  [str(i) for i in smol_rols]
                        small_string = ', '.join(smol_rols)
                        log += f'{small_string}, '

                if len(small_rolls) > 1 or len(small_rolls[0]) > 1 or len(smol_rols) > 1:
                    log = log[:-2]

                if len(smol_rols) > 1:  
                    log += f'), '
                else:
                    log += ', '
                

            if len(small_rolls) > 1 or (len(small_rolls) > 1 and len(small_rolls[0]) > 1):
                log = log[:-2]
                log += f'], '

    if result != 0:                
        log = log[:-2]

    if result.is_integer():
        result = int(result)
    
    return result, log

def roll_big(n, x, small_parameters, is_float, roll_method, defaults = {'percentage': 100, 'counts': 2, 'zeros': 0, 'ones': 1}, replacements = []):
    small_rolls = []
    for _ in range(abs(int(n))):
        roll = roll_small(x, small_parameters, is_float, roll_method, defaults, replacements)
        small_rolls.append(roll)

    big_roll = 0
    for e in small_rolls:
        for r in e:
            k, v = r
            big_roll += k
    if n < 0:
        big_roll *= -1

    big_roll = str(big_roll)
    for k, v in replacements.items():
        big_roll = big_roll.replace(k, v)
    big_roll = float(big_roll)

    if big_roll.is_integer():
        result = int(big_roll)
        
    return (big_roll, small_rolls)

def roll_small(x, small_parameters, is_float, roll_method, defaults = {'percentage': 100, 'counts': 2, 'zeros': 0, 'ones': 1}, replacements = []):
    chosen_roll = 0
    all_rolls = []
    #for _ in range(int(n)):
    local_result = check_condition(1, x, is_float)
    result = 0

    if not isinstance(x, list) and float(x) < 0 and (small_parameters["start_with"] == defaults['ones'] or small_parameters["start_with"] == defaults['zeros']):
        small_parameters["start_with"] *= -1
        x, small_parameters["start_with"] = small_parameters["start_with"], x

    '''
        local_result_2 is equal to explode conditions
    '''
    while 1:
        chance = random.randint(defaults['zeros'], defaults['percentage'])
        
        if chance < small_parameters["reroll_chance"]:
            small_rolls = [roll_method(x, small_parameters["start_with"]) for _ in range(small_parameters["reroll_count"])]
        else:
            small_rolls = [roll_method(x, small_parameters["start_with"])]

        for i in range(len(small_rolls)):
            roll = str(small_rolls[i])
            for k, v in replacements.items():
                roll = roll.replace(k, v)
            small_rolls[i] = float(roll)
            if small_rolls[i].is_integer():
                small_rolls[i] = int(small_rolls[i])

        if small_parameters["reroll_direction"] == 1:
            chosen_roll = max(small_rolls)
        else:
            chosen_roll = min(small_rolls)
        
        all_rolls.append((chosen_roll, small_rolls))

        local_result = chosen_roll
        result += chosen_roll
        
        chance = random.randint(defaults['zeros'], defaults['percentage'])

        if local_result not in small_parameters["explode"] or chance >= small_parameters["explode_chance"]:
            break

    return all_rolls

def check_condition(n = 0, x = 0, is_float = 0):
    if type(x) is list:
        return x[len(x) - 1]
    if is_float:
        return float(x) * int(n)
    else:
        return int(x) * int(n)

def roll_default(n, x, big_parameters, small_parameters, log, defaults = {'percentage': 100, 'counts': 2, 'zeros': 0, 'ones': 1}, replacements = []):
    log += f'\n{int(n)}d{int(x)}: '
    result, log = roll_placeholder(n, x, big_parameters, small_parameters, log, 0, default_roll, defaults, replacements)
    return result, log

def roll_faces(n, x, faces, step, big_parameters, small_parameters, log, defaults = {'percentage': 100, 'counts': 2, 'zeros': 0, 'ones': 1}, replacements = []):
    log += f"\n{int(n)}d{x}[{step}]: "
    result, log = roll_placeholder(n, faces, big_parameters, small_parameters, log, False, face_roll, defaults, replacements)

    return result, log

def roll_float(n, x, big_parameters, small_parameters, log, defaults = {'percentage': 100, 'counts': 2, 'zeros': 0, 'ones': 1}, replacements = []):
    log += f"\n{int(float(n)) if float(n).is_integer() else float(n)}d{int(float(x)) if float(x).is_integer() else float(x)}: "
    result, log = roll_placeholder(n, x, big_parameters, small_parameters, log, True, float_roll, defaults, replacements)

    return result, log

def default_roll(x, start):
    return random.randint(int(start), int(x))

def face_roll(faces, start):
    return random.choice(faces)

def float_roll(x, start):
    decimal_places = len(str(x).split('.')[1])
    return round(random.uniform(start, float(x)), decimal_places)

def trials(dice, n, print_log = False):
    rolls = []
    for i in range(int(n)):
        result, log = roll_dice(dice)
        rolls.append(result)
    
    rolls.sort()

    mean = statistics.mean(rolls)
    for decimal_place in range(4, 0, -1):
        mean = round(mean, decimal_place)

    s = re.sub(r'\[.*?\]', '', dice)
    numbers = [int(e) for e in re.findall(r'\d+', s)]
    maximum = 1
    for n in numbers:
        if n:
            maximum *= float(n)

    if print_log:
        print_str = ""
        print_str += f"{dice}: "
        print_str += f"Mean value is: {mean}; "
        print_str += f"Median value is: {statistics.median(rolls)}; "
        print_str += f"Min value is: {rolls[0]}; "
        print_str += f"Max value is: {maximum}\n"

    return (dice, mean, statistics.median(rolls), rolls[0], maximum)

def find(): 
    while(1):
        v1 = float(input("Mean - "))
        v2 = int(input("Median - "))

        df = pd.read_csv('wowsuchsmart.local/storage/Jokushker.data', dtype={'median': float, 'max': int})

        tolerance_column1 = 0.2
        #tolerance_column1 = 0.1 * v1
        #tolerance_column2 = v2 // 10

        filtered_df = df[(abs(df['mean'] - v1) <= tolerance_column1) & (df['max'] == v2)]

        if filtered_df.values:
            for v in filtered_df.values:
                print(v)
        else:
            print("Nothing was found")

def user_trials(dice, count = 1000000, print_log = False):
        roll = trials(dice, count, print_log)
        die, mean, median, min, max = roll
        return {"die": die, "mean": mean, "median": median, "min": min, "max": max}

def main():
    while True:
        try:
            dice_string = input("Enter the dice string: ")
            result, log = roll_dice(dice_string)
            print(log.strip())
        except Exception as e:
            print(e)

if __name__ == "__main__":
    print(f"Select mode:\n1 - Trials\n2 - Find\n3 - Main")
    mode = int(input())
    if mode == 1:
        count = input("Enter count - ")
        while 1:
            dice = input("Enter the dice string: ")
            result = user_trials(dice, int(float(count)), True)
            print(f"{result['die']}: Mean - {result['mean']}; Median - {result['median']}; Min - {result['min']}; Max - {result['max']}")

    if mode == 2: find()
    if mode == 3: main()
