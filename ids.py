def slugify(text):
    return (
        text.lower()
        .replace(" ", "_")
        .replace("'", "_")
        .replace("-", "_")
    )


def make_building_id(building_type, existing_ids):
    prefix = slugify(building_type)
    index = 1

    while True:
        building_id = f"{prefix}_{index:03d}"
        if building_id not in existing_ids:
            return building_id

        index += 1
