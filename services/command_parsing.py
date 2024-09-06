from rolling import Jokushker

def parse_command(command: str, caller = None, modes = {"normal": 1, "mean": 0, "random_sides": 0, "random_start": 0, "random_step": 0}, used_by = None):
    command = command.lower().replace(" ", "")

    if not used_by:
        selected_return = format_log
    else:
        selected_return = format_roll

    if modes["normal"]:
        try:
            roll, log = Jokushker.roll_dice(command)
        except Exception as e:
            print(e)
            return

        if caller:
            print(f'{caller.display_name}, {command}: {log}')
        else:
            print(f'{command}: {log}')

        return selected_return(roll, log)
        
    else:
        if modes["random_sides"]:
            sides, log = Jokushker.roll_dice("d100[i100]")
            command = f"d{sides}"

        if modes["random_start"]:
            start, log = Jokushker.roll_dice(command + "[s]")
            command += f"[s{start}]"
        
        if modes["random_step"]:
            step, log = Jokushker.roll_dice(command)
            command += f"[{step}]"

        test, log = Jokushker.roll_dice(command)
        print(log)

        if modes["mean"]:
            try:
                results = Jokushker.user_trials(command, 2e4, False)
                roll = int(results["mean"])
            except Exception as e:
                print(e)
                return
            
            if caller:
                print(f'{caller.display_name}, {command}')
            else:
                print(f'{command}')

            return selected_return(roll, None)
        
def paginate(message, chars=2000):
  messages = []
  m = ""
  for char in message:
      if len(m) >= chars:
          messages.append(m)
          m = ""
      m = m + char
  messages.append(m)
  return messages

def format_log(roll, log):
    string = f'```{roll}```'
    if log:
        string += f'```{log}```'
    if len(string) < 2000:
        return string
    else:
        return roll

def format_roll(roll, log):
    return roll