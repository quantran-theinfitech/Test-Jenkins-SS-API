def mask_person_data(persons, person_uuids_downloaded):
    display_fields = ["id", "uuid", "name", "address", "company_name", "role_name", "corporate_number"]

    for person in persons:
        mask_fields = [
            x for x in person.keys() if x not in display_fields and x != "id"
        ]
        available_fields = []
        if person["uuid"] not in person_uuids_downloaded:
            for field in mask_fields:
                if person[field]:
                    available_fields.append(field)
                    person[field] = None
            person["downloaded_flag"] = False

            if person["name"]:
                person["name"] = person["name"][: len(person["name"]) // 2]

        else:
            person["downloaded_flag"] = True
        person["available_fields"] = available_fields

    return persons


def mask_person_sql_data(persons, person_uuids_downloaded):
    display_fields = ["id", "uuid", "name", "address", "company_name", "role_name"]
    mask_persons = []
    for person in persons:
        person_dict = dict(person)

        mask_fields = [
            x for x in person_dict.keys() if x not in display_fields and x != "id"
        ]
        available_fields = []
        if person_dict["uuid"] not in person_uuids_downloaded:
            for field in mask_fields:
                if person_dict[field]:
                    available_fields.append(field)
                    person_dict[field] = None
            person_dict["downloaded_flag"] = False

            if person_dict.get("name"):
                person_dict["name"] = person_dict["name"][
                    : len(person_dict["name"]) // 2
                ]

        else:
            person_dict["downloaded_flag"] = True
        person_dict["available_fields"] = available_fields
        mask_persons.append(person_dict)

    return mask_persons
