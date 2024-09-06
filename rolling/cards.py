import interactions
from services import persistence, command_parsing

path_to_cards = f"img/cards"

class Card:
    class TYPES:
        PLAYING = "playing"
        MANYTHINGS = "many_things"
        MAJOR = "major"
        MINOR = "minor"
        OTHER = "other"
        
    def __init__(self, card_type, value, color = None, orientation = True):
        self.card_type = card_type
        self.value = value
        self.color = color
        self.orientation = orientation

    def __str__(self):
        if self.card_type == Card.TYPES.MINOR or self.card_type == Card.TYPES.PLAYING:
            if self.color:
                return f"{self.value} of {self.color}"
            else:
                return f"{self.value}"
            
        if self.card_type == Card.TYPES.MAJOR:
            name = self.value
            
            if not self.orientation:
                if name.startswith("The"):
                    name = name[4:]
                name = "Reversed " + name

            return name
        
        else:
            return f"{self.value}"
        
    def __repr__(self):
        return str(self)
    
    def to_dict(self):
        return {
            'card_type': self.card_type,
            'value': self.value,
            'color': self.color,
        }
    
    @staticmethod
    def from_dict(jsonDict):
        return Card(jsonDict['card_type'], jsonDict['value'], jsonDict['color'])

    def get_embed(self):
        path = self.get_path()
        file = interactions.File(path)
        embed = interactions.Embed(title=f"{str(self)}")
        embed.set_image(url=f"attachment://{self.get_path()}")

        return embed, file

    def get_path(self):
        if self.card_type == Card.TYPES.MAJOR:
            if self.orientation:
                return f"{path_to_cards}/tarot/major/straight/{self.value.replace(' ', '')}.png"
            else:
                return f"{path_to_cards}/tarot/major/reversed/{self.value.replace(' ', '')}.png"
        
        if self.card_type == Card.TYPES.MINOR:
            if self.value in range(2,10):
                return f"{path_to_cards}/tarot/minor/{self.color}/{self.color}0{self.value}.jpg" 
            elif self.value == 10:
                return f"{path_to_cards}/tarot/minor/{self.color}/{self.color}{self.value}.jpg"
            elif self.value == "Page":
                return f"{path_to_cards}/tarot/minor/{self.color}/{self.color}11.jpg"
            elif self.value == "Knight":
                return f"{path_to_cards}/tarot/minor/{self.color}/{self.color}12.jpg"
            elif self.value == "Queen":
                return f"{path_to_cards}/tarot/minor/{self.color}/{self.color}13.jpg"
            elif self.value == "King":
                return f"{path_to_cards}/tarot/minor/{self.color}/{self.color}14.png"
            else:
                return f"{path_to_cards}/tarot/minor/{self.color}/{self.color}01.jpg"
            
        if self.card_type == Card.TYPES.MANYTHINGS:
            return f"{path_to_cards}/deck_of_many_things/{self.value.replace(' ', '')}.png"
        
        if self.card_type == Card.TYPES.PLAYING:
            name = str(self).lower().replace(' ', '_')
            return f"{path_to_cards}/playing/{name}.png"
        
        if self.card_type == Card.TYPES.OTHER:
            return f"{path_to_cards}/other/{self.value.replace(' ', '')}.png"

    TAROT_COLORS = ["Cups", "Pentacles", "Swords", "Wands"]
    PLAYING_COLORS = ['hearts', 'diamonds', 'spades', 'clubs']

class Deck:
    class DECKNAMES:
        FULL = "full"
        MANYTHINGSPARTIAL = "all_things_partial"
        MANYTHINGSFULL = "all_things_full"
        TAROTMAJOR = "tarot_major"
        TAROT = "tarot"

    def __init__(self, name, id, cards):
        self.name = name
        self.id = id
        self.cards = cards

    def __str__(self):
        return str(self.cards)
    
    def __len__(self):
        return len(self.cards)
    
    def to_dict(self):
        return {
            'name': self.name,
            'id': self.id,
            'cards': [card.to_dict() for card in self.cards]
        }
    
    @staticmethod
    def from_dict(jsonDict):
        return Deck(jsonDict['name'], jsonDict['id'], [Card.from_dict(card_dict) for card_dict in jsonDict['cards']])
    
    @staticmethod
    def from_dict_global(jsonDict):
        return {key: Deck.from_dict(value) for key, value in jsonDict.items()}
    
    @staticmethod
    def get_name(name):
        if name == Deck.DECKNAMES.FULL:
            return "Full deck of playing cards"
        if name == Deck.DECKNAMES.MANYTHINGSPARTIAL:
            return "Partial deck of arcana cards"
        if name == Deck.DECKNAMES.MANYTHINGSFULL:
            return "Full deck of arcana cards"
        if name == Deck.DECKNAMES.TAROTMAJOR:
            return "Major tarot cards"
        if name == Deck.DECKNAMES.TAROT:
            return "Full deck of tarot cards"
        return

    @staticmethod
    def generate_deck(name):
        deck = []

        if name == Deck.DECKNAMES.FULL:
            deck = [Card(Card.TYPES.PLAYING, value, color) for value in range(2, 11) for color in Card.PLAYING_COLORS]
            deck += [Card(Card.TYPES.PLAYING, value, color) for value in ["Jack", "Queen", "King"] for color in Card.PLAYING_COLORS]
            deck += [Card(Card.TYPES.PLAYING, "Ace", color) for color in Card.PLAYING_COLORS]
            deck += [Card(Card.TYPES.PLAYING, "Red Joker")]
            deck += [Card(Card.TYPES.PLAYING, "Black Joker")]

        if name == Deck.DECKNAMES.MANYTHINGSPARTIAL:
            deck = [Card(Card.TYPES.MANYTHINGS, value) for value in ["Sun", "Moon", "Star", "Throne", "Key", "Knight", "The Void", "Flames", "Skull", "Ruin", "Euryale", "Rogue", "Jester"]]

        if name == Deck.DECKNAMES.MANYTHINGSFULL:
            deck = [Card(Card.TYPES.MANYTHINGS, value) for value in ["Sun", "Moon", "Star", "Throne", "Key", "Knight", "The Void", "Flames", "Skull", "Ruin", "Euryale", "Rogue", "Jester"]]
            deck += [Card(Card.TYPES.MANYTHINGS, value) for value in ["Vizier", "Comet", "The Fates", "Gem", "Talons", "Idiot", "Donjon", "Balance", "Fool"]]

        if name == Deck.DECKNAMES.TAROTMAJOR:
            deck = [Card(Card.TYPES.MAJOR, name) for name in ["The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor", "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit", "Wheel Of Fortune",
                                                                        "Justice", "The Hanged Man", "Death", "Temperance", "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World"]]
            
        if name == Deck.DECKNAMES.TAROT:
            deck = [Card(Card.TYPES.MAJOR, name) for name in ["The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor", "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit", "Wheel Of Fortune",
                                                                        "Justice", "The Hanged Man", "Death", "Temperance", "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World"]]
            deck += [Card(Card.TYPES.MINOR, value, color) for value in range(2,11) for color in Card.TAROT_COLORS]
            deck += [Card(Card.TYPES.MINOR, value, color) for value in ["Page", "Knight", "Queen", "King"] for color in Card.TAROT_COLORS]
            deck += [Card(Card.TYPES.MINOR, "Ace", color) for color in Card.TAROT_COLORS]

        return deck

    def pull_card(self, number):
        cards = []

        for _ in range(0, number if number < len(self.cards) else len(self.cards)):
            command = "d" + str(len(self.cards) - 1) + "[s]"
            card = int(command_parsing.parse_command(command, used_by="number"))
            is_valid = card < len(self.cards)
            if is_valid:
                card = self.cards.pop(card)
            else:
                card = Card(Card.TYPES.OTHER, '404')

            if card.card_type == Card.TYPES.MAJOR:
                command = "d1[s]"
                orientation = int(command_parsing.parse_command(command, used_by="number"))
                card.orientation = orientation

            cards.append(card)
        
        print(f"Pulled {cards} out of deck {self.id}")
        return cards

async def save(deck):
    current_data = {}
    deleted = False

    data = persistence.load()
    current_data = data.get_decks()

    if (len(deck)):
        deck_dict = deck.to_dict()
        current_data[deck.id] = deck_dict
    else:
        if deck.id in current_data:
            del current_data[deck.id]
            deleted = True

    persistence.save(data)

    return deleted

async def load(id):
    data = persistence.load().get_decks()
    if id in data:
        return data[id]
    else:
        return