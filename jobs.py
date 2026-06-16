"""Catalogue central des metiers.

Plan du fichier:
01 - JOB_CATALOG: donnees communes des emplois.
02 - job_definition: lecture sure d'un metier.
03 - job_salary_coefficient: coefficient applique au salaire median local.
04 - job_base_salary: salaire calcule avec un median local par defaut de 7.

Les batiments restent responsables de dire quels postes ils proposent. Ce
catalogue evite seulement de disperser les salaires et prerequis communs.
"""


JOB_CATALOG = {
    "Barman": {
        "salary_coefficient": 1.5,
        "main_stat": "social",
        "skill": "Charisme",
        "skilled_only": False
              },
    "Cuisinier": {
        "salary_coefficient": 1.5,
        "main_stat": "physique",
        "skill": "Cuisine", 
        "skilled_only": False},
    "Hotesse": {
        "salary_coefficient": 1, 
        "main_stat": "social", 
        "skill": "Charisme", 
        "skilled_only": False,
        "sex": "Femme", 
        "unmarried_only": True},
    "Cowboy": {
        "salary_coefficient": 1,
          "main_stat": "physique",
         "skill": "Élevage", "skilled_only": False, "sex": "Homme", "unmarried_only": True, "min_stat": 8, "included_board": True, "included_lodging": True},
    "Infirmière": {"salary_coefficient": 2, "main_stat": "intelligence", "skill": "Médecine", "skilled_only": True, "sex": "Femme"},
    "Adjoint du sherif": {"salary_coefficient": 1.5, "main_stat": "physique", "skill": "Jugement", "skilled_only": False, "sex": "Homme"},
    "Employe du Post Office": {"salary_coefficient": 2, "main_stat": "intelligence", "skill": "Télégraphiste", "skilled_only": True, "sex": "Homme"},
    "Commis": {"salary_coefficient": 1.5, "main_stat": "Intelligence", "skill": "", "skilled_only": False, "sex": "Homme"},
    "Bonne": {"salary_coefficient": 0.8, "main_stat": "social", "skill": "Cuisine", "skilled_only": True, "sex": "Femme"},
    "Mineur": {"salary_coefficient": 1, "main_stat": "physique", "skill": "Artificier", "skilled_only": False, "sex": "Homme"},
    "Garde": {"salary_coefficient": 1.5, "main_stat": "physique", "skill": "Jugement", "skilled_only": False, "sex": "Homme"},
    "Ingénieur": {"salary_coefficient": 4, "main_stat": "intelligence", "skill": "Ingénieurie",  "skilled_only": True, "sex": "Homme"},
    "Bucheron": {"salary_coefficient": 1, "main_stat": "physique", "skill": "", "skilled_only": False, "sex": "Homme", "min_stat": 8, "included_board": True, "included_lodging": True}
}


def job_definition(role):
    return JOB_CATALOG.get(role, {"salary_coefficient": 1})


def job_salary_coefficient(role):
    return job_definition(role).get("salary_coefficient", 1)


def job_base_salary(role, median_wage=7):
    return round(median_wage * job_salary_coefficient(role), 1)
