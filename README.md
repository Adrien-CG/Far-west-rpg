# Jeu Far West

Prototype de jeu de gestion/RPG dans une ville de l'Ouest americain.

Le joueur cree un personnage, s'installe a Dusty Creek, entre dans les
batiments, gere ses proprietes, recrute des employes, construit des
ameliorations et passe les saisons. Le coeur du jeu est maintenant structure
autour d'une simulation de fin de tour : exploitation des proprietes, offres,
revenus, demande, consommation, demographie, sante, comptabilite et changement
de saison.

## Lancer le jeu

Installe les dependances :

```powershell
pip install -r requirements.txt
```

Puis lance l'interface :

```powershell
python main.py
```

Si Windows utilise le lanceur Python :

```powershell
py main.py
```

## Structure actuelle

- `main.py` lance l'application.
- `ui/app.py` contient l'interface Tkinter. Elle affiche les menus, la ville,
  les batiments, les profils, le debug et les onglets de gestion.
- `tk_ui.py` garde seulement une compatibilite temporaire vers `ui/app.py`.
- `game_state.py` contient l'etat general de la partie : carte, ville,
  population, batiments, prix de marche, climat, saison, joueur, revenu global
  de la ville, changement de saison et vieillissement annuel.
- `turn_system.py` orchestre la fin de tour dans l'ordre officiel. Il doit
  rester court : preparation, appels d'etapes, passage de saison, puis retour a
  l'interface.
- `turn_phases.py` est un adaptateur temporaire pendant la refonte. Il expose
  les grandes etapes de tour sous forme de fonctions, meme si certaines
  s'appuient encore sur l'ancien code de l'interface.
- `demography.py` gere les voyageurs, les arrivees de colons, les departs de
  colons et les etats de sante.
- `accounting.py` gere les bilans, comptes de resultat, variations de stock,
  capital, reserves et clotures de saison/annee.
- `economy.py` regroupe les fonctions economiques communes : offre locale,
  revenus, liste de preferences/demande, consommation en cours de construction
  et transactions commerciales generales.
- `events.py` gere les evenements de saison et la fluctuation des prix.
- `jobs.py` centralise les donnees communes des metiers : salaire de base,
  prerequis et contraintes generales. Les batiments gardent la liste des postes
  qu'ils debloquent.
- `character.py` gere le personnage joueur, les PNJ, les voyageurs, les noms,
  les preferences et les questions de creation.
- `buildings.py` contient le modele commun des batiments, la creation initiale
  de Dusty Creek et les contrats d'employes.
- `building_types/` contient les modules propres aux types de batiments
  (`ranch`, `saloon`, `general_store`, `mine`, `medical_office`, etc.).
- `actions/` contient les grosses actions hors batiment, comme la prospection,
  et les actions generales de la vue ville.
- `goods_services.py` reste un pont de compatibilite pour les anciens imports.
- `items/goods.py`, `items/services.py`, `items/animals.py` et
  `items/housing.py` contiennent les catalogues par nature.
- `housing.py` contient les types de logements et batiments de logement.
- `housing_rules.py` contient les regles communes de logement : choix de
  residence, tentes provisoires et helpers d'affichage. Les logements generes
  par un batiment sont definis dans le fichier de ce batiment.
- `achievements.py` gere les succes de partie et les succes globaux.
- `saves.py` charge, sauvegarde et supprime les parties.

## Ordre de fin de tour

`turn_system.py` lance les etapes suivantes :

1. Logements provisoires.
2. Occupation choisie par le joueur pour la saison.
3. Gestion IA.
4. Accidents et maladies.
5. Exploitation des batiments et creation de l'offre.
6. Revenus.
7. Demande et consommation.
8. Voyageurs, arrivees de colons et departs de colons.
9. Resolution des etats de sante.
10. Cloture comptable.
11. Avancement de la saison et de l'annee.
12. Evenements de la nouvelle saison.
13. Nettoyage, sauvegarde et retour a l'interface.

L'ecran noir de transition est encore declenche par `ui/app.py`, juste avant
l'appel a `turn_system.py`. Le calcul du tour se fait ensuite en arriere-plan,
puis l'interface revient sur la ville.

## Notes de developpement

Le projet est en refonte progressive. L'objectif est de sortir la logique metier
de l'interface pour que chaque fichier ait un role clair :

- les regles de demographie vont dans `demography.py`;
- les regles propres a un batiment vont dans `building_types/`;
- les transactions et calculs economiques communs vont dans `economy.py`;
- les biens, services, animaux et logements vivent dans `items/`;
- l'interface doit surtout afficher et appeler les fonctions existantes.
- `turn_phases.py` doit disparaitre progressivement quand chaque etape aura sa
  vraie fonction metier dans le bon module.

Migration deja faite dans cette refonte :

- offres du saloon, du general store, du barber shop et du cabinet medical dans
  leurs fichiers de batiment;
- premiers calculs ranch dans `building_types/ranch.py`;
- premiers calculs mine dans `building_types/mine.py`;
- evenements de saison dans `events.py`;
- catalogues separes par nature dans `items/`;
- vieillissement des animaux generalise dans `game_state.py`.
- classes et valeurs initiales preparees pour les nouveaux batiments prives :
  `Ferme`, `Camp de bucheron`, `Banque`, `Tailleur`, `Marechal ferrant`,
  `Charpentier`, `Hotel`, `Restaurant`, `Comptoir de trappeur`, `Journal`,
  `Bureau`;
- classes preparees pour les batiments publics : `Fort`, `County hall`,
  `Ecole`.

Les sauvegardes de test peuvent etre supprimees pendant les refontes : la
compatibilite avec les anciennes sauvegardes n'est pas prioritaire pour
l'instant.
