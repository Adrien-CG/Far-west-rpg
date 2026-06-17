from buildings_config import *
#exemple de fiche batiment avec le ranch

### PARTIE CREATION ###

#création du type de bâtiment ranch
def ranch_initialisation():
    ranch = Building_type ( )

#méthode de création du ranch
def ranch_build():
    return

#méthode vérifier si la construction et possible
def ranch_conditions(owner_id):
    for b in Character[owner_id].property:
        if Building[b].type_ == "ranch" :
            return False
        else :
            continue

#retourne le prix de construction du ranch
def ranch_price():
    return 36

### PARTIE AMELIORATION ###

#méthodes appliquant les modification du aux améliorations
def ranch_upgrade_barracks():
    return   

#liste des améliorations du ranch
RANCH_UPGRADES = {
    "Baraquements": {'price': '', 'limit': '', 'methode': ranch_upgrade_barracks, 'visible': True}
    
}

#méthode gérant les améliorations du ranch
def ranch_upgrade(ranch_id, upgrade):
    return

### PARTIE EXPLOITATION ###

#ratio utilisé pour l'exploitation du ranch
RANCH_RATIO = {}

#méthode gérant l'exploitation du ranch
def ranch_exploitation(ranch_id):
    offer = []
    demand = []
    return [offer,demand]

def cattle_drive(ranch_id):
    return