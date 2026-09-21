"""Privacy utilities for data desensitization"""


def mask_phone(phone: str) -> str:
    """Mask phone number: 138****8888"""
    if not phone:
        return phone
    phone = str(phone)
    if len(phone) >= 7:
        return phone[:3] + "****" + phone[-4:]
    return "****"


def mask_id_card(id_card: str) -> str:
    """Mask ID card number: 110101********1234"""
    if not id_card:
        return id_card
    id_card = str(id_card)
    if len(id_card) == 18:
        return id_card[:6] + "********" + id_card[-4:]
    if len(id_card) >= 4:
        return id_card[:2] + "****" + id_card[-2:]
    return "****"


def mask_name(name: str) -> str:
    """Mask name: 张**"""
    if not name:
        return name
    if len(name) <= 1:
        return "*"
    return name[0] + "*" * (len(name) - 1)


def mask_email(email: str) -> str:
    """Mask email: a***@example.com"""
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        masked_local = "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 1)
    return f"{masked_local}@{domain}"


def desensitize_dict(data: dict, sensitive_fields: dict = None) -> dict:
    """Desensitize sensitive fields in a dict.

    sensitive_fields: dict mapping field_name -> mask_function_name
    Default masks: phone -> mask_phone, id_card -> mask_id_card, mobile -> mask_phone,
                   idcard -> mask_id_card, telephone -> mask_phone, email -> mask_email
    """
    if data is None:
        return data
    if not isinstance(data, dict):
        return data

    default_masks = {
        "phone": mask_phone,
        "mobile": mask_phone,
        "telephone": mask_phone,
        "customer_phone": mask_phone,
        "supplier_contact": mask_phone,
        "id_card": mask_id_card,
        "idcard": mask_id_card,
        "id_number": mask_id_card,
        "email": mask_email,
    }
    masks = {**default_masks, **(sensitive_fields or {})}

    result = dict(data)
    for field, mask_fn in masks.items():
        if field in result and result[field] is not None:
            result[field] = mask_fn(result[field])
    return result
