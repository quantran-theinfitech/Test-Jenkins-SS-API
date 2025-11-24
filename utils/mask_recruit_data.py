def mask_recruit_data(recruit, recruits_ids_downloaded):

    mask_fields = ["recruit_tels", "recruit_mails"]
    available_fields = []
    if recruit["corporate_number"] not in recruits_ids_downloaded:
        for field in mask_fields:
            if recruit.get(field):
                available_fields.append(field)
                recruit[field] = None
    recruit["available_fields"] = available_fields
    return recruit
