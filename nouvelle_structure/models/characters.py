#ensemble des méthodes et catalog pour la gestion des personnages

#liste des compétences
ALL_SKILLS = [
    ""
]

#listes pour création aléatoire
#liste prénom masculin
MALE_FIRST_NAMES = [
    "Abel", "Abraham", "Ambrose", "Amos", "Augustus", "Bartholomew",
    "Benjamin", "Caleb", "Cassius", "Clyde", "Cornelius", "Cyrus",
    "Darius", "Elias", "Elijah", "Emmett", "Ephraim", "Ezra",
    "Felix", "Gideon", "Grady", "Harlan", "Hiram", "Hollis",
    "Isaac", "Jedediah", "Jesse", "Jonah", "Josiah", "Levi",
    "Lucius", "Malachi", "Marshall", "Micah", "Nathaniel", "Orson",
    "Phineas", "Quentin", "Rufus", "Samuel", "Silas", "Solomon",
    "Thaddeus", "Thomas", "Tobias", "Virgil", "Walter", "Wyatt",
    "Albert", "Alfred", "Andrew", "Arthur", "Bennett", "Booker",
    "Chester", "Clarence", "Clayton", "Clifford", "Daniel", "Duncan",
    "Edgar", "Edwin", "Everett", "Franklin", "George", "Grant",
    "Harvey", "Henry", "Howard", "Irving", "Jackson", "James",
    "Lawrence", "Luther", "Martin", "Milton", "Morgan", "Nelson",
    "Oscar", "Percival", "Preston", "Randolph", "Raymond", "Roland",
    "Seth", "Theodore", "Wallace", "Warren", "Wesley", "William",
]

#liste prénom féminin
FEMALE_FIRST_NAMES = [
    "Abigail", "Ada", "Adelaide", "Agnes", "Alice", "Beatrice",
    "Clara", "Clementine", "Cora", "Dorothy", "Edith", "Eleanor",
    "Eliza", "Esther", "Florence", "Georgia", "Grace", "Harriet",
    "Ida", "Josephine", "Lillian", "Louisa", "Mabel", "Martha",
    "Matilda", "Nora", "Opal", "Pearl", "Prudence", "Rose",
    "Sadie", "Sarah", "Susannah", "Vera", "Violet", "Winifred",
    "Annabelle", "Belle", "Bessie", "Caroline", "Charlotte", "Daisy",
    "Delilah", "Etta", "Evelyn", "Fannie", "Frances", "Gertrude",
    "Helen", "Henrietta", "Irene", "Jane", "Julia", "Katherine",
    "Laura", "Lucille", "Maggie", "Mae", "Margaret", "Marion",
    "Minnie", "Nancy", "Olive", "Pauline", "Rebecca", "Ruby",
    "Ruth", "Stella", "Virginia", "Vivian", "Willie",
]

#liste nom
AST_NAMES = [
    "Abbott", "Bell", "Blackwood", "Boone", "Briggs", "Callahan",
    "Carver", "Cassidy", "Clay", "Cooper", "Crawford", "Dawson",
    "Doyle", "Drake", "Dunleavy", "Fletcher", "Garrett", "Graves",
    "Hale", "Harlow", "Hawkins", "Holliday", "Kincaid", "Langley",
    "McCoy", "Mercer", "Nolan", "Parker", "Pickett", "Reed",
    "Rourke", "Sawyer", "Slater", "Sullivan", "Turner", "Walker",
    "Whitmore", "Winchester", "Wolfe", "Wright", "Archer", "Barker",
    "Barlow", "Baxter", "Bishop", "Blevins", "Bradford", "Brennan",
    "Bridger", "Brooks", "Burke", "Caldwell", "Cannon", "Chambers",
    "Coleman", "Conway", "Dalton", "Ellis", "Foster", "Garrison",
    "Goodwin", "Hardin", "Harrington", "Hayes", "Henderson", "Houston",
    "Keller", "Laramie", "Lawson", "Maddox", "Mason", "Montgomery",
    "Owen", "Prescott", "Ramsey", "Remington", "Russell", "Sheridan",
    "Stafford", "Sterling", "Talbot", "Thornton", "Vaughn", "Watson",
    "Webster", "West", "Whitaker", "York",
]

#classe commune à tout les personnage y compris les joueurs
class Character:
    _id_counter = 0
    def __init__(self):
        Character._id_counter += 1
        #character information
        self.id: str = f"ch{Character._id_counter:06d}" #ch000001
        self.name: str = ""
        self.lastname: str = ""
        self.sex: str = "Homme"
        self.age: int = 25
        self.player: bool = False
        #stats
        self.phy: int = 5 
        self.soc: int = 5
        self.int: int = 5
        self.skills: list = [] 
        self.healthstate: str = "En forme"
        #economic
        self.income: float = 0
        self.money: float = 0
        self.job: str = ""
        self.property: list = []
        self.inventory: list = []
        self.horse: str = ""
        self.housings: str = ""
        self.claims: list = [{}]
        #consumtion
        self.preference: list = [{}]
        self.cunsumption: list = [{}]
        self.behavior: str = ""
        #social
        self.relation: list = [{}]
        self.respect: int = 0
        self.celebrity: int = 0
        self.politic: str = ""
        self.notable: bool = False