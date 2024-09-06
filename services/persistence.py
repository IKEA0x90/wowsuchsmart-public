path_to_storage = "./storage/wowsuchdie.json"
import json
from rolling import cards

class Persistence:
    def __init__(self, decks, replacements, replacements_active, forced_roll):
        self.decks = decks
        self.replacements = replacements
        self.replacements_active = replacements_active
        self.forced_roll = forced_roll

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
                return {
                    'decks': {key: deck.to_dict() if isinstance(deck, cards.Deck) else deck for key, deck in self.decks.items()},
                    'replacements': self.replacements,
                    'replacements_active': self.replacements_active,
                    'forced_roll': self.forced_roll
                }
        
    @staticmethod
    def from_dict(jsonDict):
        return Persistence(cards.Deck.from_dict_global(jsonDict['decks']), {k: v for k, v in jsonDict['replacements'].items()}, jsonDict['replacements_active'], jsonDict['forced_roll'])
    
    def get_decks(self):
        return self.decks

    def get_deck(self, id):
        if id in self.decks:
            return self.decks[id]
        else:
            return cards.load(id)
        
    def update_deck(self, deck):
        if deck.id in self.decks:
            self.decks[deck.id] = deck
            if len(deck) == 0:
                self.decks.pop(deck.id)
                save(self)
        return

    def get_replacements(self):
        return self.replacements
    
    def get_forced_roll(self):
        return self.forced_roll
    
    def add_forced_roll(self, outcome):
        self.forced_roll = outcome
    
    def add_replacer(self, original, replacer):
        self.replacements[original] = replacer

    def remove_replacer(self, original):
        if original in self.replacements:
            self.replacements.pop(original)

    def get_replacements_active(self):
        return self.replacements_active
    
    def toggle_replacements(self):
        self.replacements_active = abs(self.replacements_active - 1)

def save(data):
    print(f"Saving...")
    jsonDict = data.to_dict()
    with open(path_to_storage, 'w') as file:
        json.dump(jsonDict, file)

def load():
    try:
        with open(path_to_storage, 'r') as file:
            data = json.load(file)
            return Persistence.from_dict(data)
    except KeyError as k:
        print(f"KeyError {k} @ persistence load()")
        return Persistence({}, {}, 0, None)
    except FileNotFoundError:
        with open(path_to_storage, 'w') as file:
            file.write("{}")