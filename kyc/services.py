def calculate_kyc_risk(profile):
    score = 0
    flags = []

    document_types = set(profile.documents.values_list("document_type", flat=True))

    if "front_id" not in document_types:
        score += 40
        flags.append("Missing front ID")

    if "back_id" not in document_types:
        score += 40
        flags.append("Missing back ID")

    if "selfie" not in document_types:
        score += 50
        flags.append("Missing selfie verification photo")

    if profile.id_number_hash:
        duplicate_exists = profile.__class__.objects.filter(
            id_number_hash=profile.id_number_hash
        ).exclude(id=profile.id).exists()

        if duplicate_exists:
            score += 30
            flags.append("Possible duplicate ID number")

    if score >= 70:
        risk_level = "high"
    elif score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    profile.risk_score = score
    profile.risk_level = risk_level
    profile.risk_flags = flags
    profile.save(update_fields=["risk_score", "risk_level", "risk_flags"])

    return score, risk_level, flags