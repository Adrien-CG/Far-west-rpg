#méthodes utilisé un peu partout

#filtrer des listes d'objet selon une valeur
def object_filter(class_, list_, attribut, valeur):
    return [id_ for id_ in list_ if id_ in list_ and getattr(class_[id_], attribut) == valeur]

#trier des listes d'objet selon un attribut