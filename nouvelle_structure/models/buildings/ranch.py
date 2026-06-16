#exemple de fiche batiment avec le ranch

#valeurs par défaut du ranch
RANCH = {
    'family' : 'economic',
    'name' : 'Ranch',
    'production' : { 'cattle_drive' : [0,[],[],[],0]},
    'stock' : {'cow' : 0, 'bull' : []},
    'housing' : {'bedroom' : 1, 'house1' : 1},
    'jobs' : {'cowboy' : 1},
    'accounting' : {

    },
    'location' : 1
}

#méthode de création du ranch
def ranch_build():

    return

def ranch_conditions(owner_id):
    return

def ranch_price():
    return 36

#liste des améliorations du ranch
RANCH_UPGRADES = {}

#méthode gérant les améliorations du ranch
def ranch_upgrade(ranch_id, upgrade):
    return

#ratio utilisé pour l'exploitation du ranch
RANCH_RATIO = {}

#méthode gérant l'exploitation du ranch
def ranch_exploitation(ranch_id):
    offer = []
    demand = []
    return [offer,demand]

def cattle_drive(ranch_id):
    return