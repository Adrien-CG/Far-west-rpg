from dataclasses import asdict, dataclass, field
import random

from population import FEMALE_FIRST_NAMES, LAST_NAMES, MALE_FIRST_NAMES

try:
    import questionary
except ImportError:
    questionary = None


@dataclass
class Character:
    first_name: str
    last_name: str
    name: str
    sex: str
    age: int
    origin: str
    strength: int
    sociability: int
    intelligence: int
    health: int
    max_health: int
    income: int
    money: int
    skills: list[str] = field(default_factory=list)
    inventory: dict[str, int] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def ask_text(question):
    while True:
        if questionary:
            answer = questionary.text(question).ask()
            if answer is None:
                raise KeyboardInterrupt
        else:
            answer = input(question).strip()

        answer = answer.strip()
        if answer:
            return answer
        print("Reponse obligatoire.")


def ask_text_with_default(question, default_value):
    if questionary:
        answer = questionary.text(question, default=default_value).ask()
        if answer is None:
            raise KeyboardInterrupt

        answer = answer.strip()
        return answer or default_value

    answer = input(f"{question} [{default_value}] : ").strip()
    return answer or default_value


def ask_choice(question, choices):
    if not questionary:
        print(f"\n{question}")

        for index, choice in enumerate(choices, start=1):
            print(f"{index}. {choice['label']}")

        while True:
            answer = input("Ton choix : ").strip()

            if answer.isdigit():
                selected_index = int(answer) - 1
                if 0 <= selected_index < len(choices):
                    return choices[selected_index]

            print("Choix invalide. Entre le numero correspondant.")

    labels = [choice["label"] for choice in choices]
    selected_label = questionary.select(question, choices=labels).ask()

    if selected_label is None:
        raise KeyboardInterrupt

    for choice in choices:
        if choice["label"] == selected_label:
            return choice

    raise ValueError(f"Choix inconnu : {selected_label}")


CHARACTER_QUESTIONS = [
    # Ajoute/modifie ici les questions de creation du personnage.
    # Chaque reponse sert surtout a ajouter des competences.
    # Elle peut aussi donner des stats, de l'argent, et eventuellement
    # definir une origine narrative.
    {
        "id": "question_1",
        "question": "D'où venez-vous ?",
        "choices": [
            {
                "label": "D'une grande ville de l'Est",
                "stats": {"strength": 0, "sociability": 1, "intelligence": 1},
                "skills": [],
                "money": 0,
                # "origin": "Nom de l'origine si cette reponse doit la definir",
                # "next": "question_3",
            },
            {
                "label": "D'une petite ville du Sud",
                "stats": {"strength": 1, "sociability": 1, "intelligence": 0},
                "skills": [],
                "money": 0,
            },
            {
                "label": "Du soleil de Californie",
                "stats": {"strength": 1, "sociability": 1, "intelligence": 0},
                "skills": [],
                "money": 0,
            },
        ],
    },
    {
        "id": "question_2",
        "question": "Template question 2 : que savez-vous faire quand les choses tournent mal ?",
        "choices": [
            {
                "label": "Template reponse A",
                "stats": {"strength": 1, "sociability": 0, "intelligence": 0},
                "skills": ["competence_d_remplacer"],
                "money": 0,
            },
            {
                "label": "Template reponse B",
                "stats": {"strength": 0, "sociability": 1, "intelligence": 0},
                "skills": ["competence_e_remplacer"],
                "money": 0,
            },
            {
                "label": "Template reponse C",
                "stats": {"strength": 0, "sociability": 0, "intelligence": 1},
                "skills": ["competence_f_remplacer"],
                "money": 0,
            },
        ],
    },
    {
        "id": "question_3",
        "question": "Template question 3 : question atteignable directement depuis une autre reponse",
        "choices": [
            {
                "label": "Template reponse A",
                "stats": {"strength": 0, "sociability": 0, "intelligence": 0},
                "skills": ["competence_g_remplacer"],
                "money": 0,
            },
            {
                "label": "Template reponse B",
                "stats": {"strength": 0, "sociability": 0, "intelligence": 0},
                "skills": ["competence_h_remplacer"],
                "money": 0,
            },
        ],
    },
]


def create_character():
    print("Bonjour...")
    title = ask_choice(
        "Comment dois-je vous appeler ?",
        [
            {"label": "Monsieur", "sex": "Homme"},
            {"label": "Madame", "sex": "Femme"},
        ],
    )
    sex = title["sex"]
    random_first_name = random.choice(MALE_FIRST_NAMES if sex == "Homme" else FEMALE_FIRST_NAMES)
    first_name = ask_text_with_default(f"Bonjour {title['label']} ?", random_first_name)

    random_last_name = random.choice(LAST_NAMES)
    last_name = ask_text_with_default(f"{first_name} comment ?", random_last_name)

    name = f"{first_name} {last_name}"
    age = ask_age()
    answers = ask_character_questions()
    strength = answers["strength"]
    sociability = answers["sociability"]
    intelligence = answers["intelligence"]
    health = 80 + strength * 5
    max_health = health
    money = answers["money"]

    return Character(
        first_name=first_name,
        last_name=last_name,
        name=name,
        sex=sex,
        age=age,
        origin=answers["origin"],
        strength=strength,
        sociability=sociability,
        intelligence=intelligence,
        health=health,
        max_health=max_health,
        income=0,
        money=money,
        skills=answers["skills"],
    )


def ask_character_questions():
    result = {
        "origin": None,
        "strength": 4,
        "sociability": 4,
        "intelligence": 4,
        "money": 500,
        "skills": [],
    }

    question_by_id = {
        question_data["id"]: question_data
        for question_data in CHARACTER_QUESTIONS
    }
    current_question_id = CHARACTER_QUESTIONS[0]["id"]
    answered_question_ids = set()

    while current_question_id:
        question_data = question_by_id[current_question_id]
        answered_question_ids.add(current_question_id)
        selected = ask_choice(question_data["question"], question_data["choices"])

        for stat_name, bonus in selected.get("stats", {}).items():
            result[stat_name] += bonus

        result["money"] += selected.get("money", 0)

        for skill in selected.get("skills", []):
            if skill not in result["skills"]:
                result["skills"].append(skill)

        if selected.get("origin"):
            result["origin"] = selected["origin"]

        current_question_id = next_question_id(
            current_question_id,
            selected,
            answered_question_ids,
        )

    if result["origin"] is None:
        result["origin"] = "Nouvel arrivant"

    return result


def next_question_id(current_question_id, selected_answer, answered_question_ids):
    if "next" in selected_answer:
        return selected_answer["next"]

    question_ids = [question_data["id"] for question_data in CHARACTER_QUESTIONS]
    current_index = question_ids.index(current_question_id)

    for question_id in question_ids[current_index + 1:]:
        if question_id not in answered_question_ids:
            return question_id

    return None


def ask_age():
    while True:
        answer = ask_text("Age du personnage : ")

        if answer.isdigit():
            age = int(answer)
            if 12 <= age <= 90:
                return age

        print("Entre un age entre 12 et 90.")
