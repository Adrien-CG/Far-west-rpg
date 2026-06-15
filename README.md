# Jeu Python

Prototype de jeu de gestion/RPG dans une ville far west.

La ville contient plusieurs familles de batiments :

- `Ranch` : batiment economique constructible et gerable par le joueur.
- `Saloon` : batiment economique constructible et gerable par le joueur.
- `General Store` : commerce tenu par un PNJ, achat et vente d'objets.
- `Bureau du sherif` : batiment public gere par la ville.
- `Post Office` : batiment public gere par la ville.

Les batiments economiques ont des documents financiers, des ameliorations, des
employes, des stocks, et des caracteristiques cachees utilisees dans les
resultats de fin de journee.

La ville genere aussi une population initiale de PNJ avec prenom, nom, sexe,
age, origine, statistiques, revenu, argent en poche, competences, inventaire,
emploi et liens de mariage simples. Certains PNJ sortent du lot, comme le
sherif, le tenancier du General Store et le proprietaire du ranch etabli.

La generation de nouveaux arrivants a chaque fin de tour est volontairement
gardee pour plus tard, quand la mecanique de fin de tour sera plus complete.

## Lancer le programme

Installe d'abord les dependances du projet :

```powershell
pip install -r requirements.txt
```

```powershell
python main.py
```

Si tu utilises le lanceur Python Windows :

```powershell
py main.py
```

## Organisation

- `main.py` lance le programme.
- `tk_ui.py` contient l'interface cliquable en Tkinter.
  Elle contient le menu principal, la creation de personnage, le chargement,
  la suppression de sauvegarde, la vue ville, les batiments et la gestion.
  Une seule fenetre est ouverte : chaque menu remplace simplement l'ecran
  precedent.
- `character.py` contient la creation du personnage.
- `game_state.py` contient l'etat global de la partie.
- `buildings.py` contient le modele commun des batiments et le catalogue.
- `population.py` genere les PNJ de la ville.
- `city_actions.py` contient encore l'ancien menu texte de la ville.
- `building_actions/` contient les actions propres a chaque type de batiment.
- `action_system.py` contient le moteur commun pour declarer, filtrer et
  executer les actions.
- `building_management/` contient les menus de gestion des batiments
  economiques : comptabilite, ameliorations et employes.
- `ids.py` genere les identifiants stables des batiments.
- `saves.py` gere l'enregistrement dans le dossier `saves`.
- `saves/*.json` contient les sauvegardes creees par le jeu.
- `requirements.txt` liste les bibliotheques externes utilisees.
