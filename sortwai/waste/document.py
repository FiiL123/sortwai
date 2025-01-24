from urllib.parse import urljoin

import requests
from django.conf import settings

from sortwai.waste.models import Category, Target


def get_categories_by_document(document_id: str) -> list[dict]:
    """
    Returns all categories from the LLM API referenced by a given document.
    """
    res = requests.get(
        urljoin(settings.SORTWAI_LLM_API, "/categories"),
        params={"document": document_id},
    )
    res.raise_for_status()

    return res.json()


def get_category(category_id: str) -> dict:
    """
    Returns a category info from the LLM API.
    """
    res = requests.get(urljoin(settings.SORTWAI_LLM_API, f"/categories/{category_id}"))
    res.raise_for_status()
    return res.json()


def _set_category_frontend_id(category_id: str, frontend_id: str) -> None:
    """
    Stores a frontend_id in the LLM API database.
    """
    res = requests.post(
        urljoin(settings.SORTWAI_LLM_API, f"/categories/{category_id}/frontend_id"),
        json={"frontend_id": frontend_id},
    )
    res.raise_for_status()


def create_objects_from_document(document_id: str, municipality_id: int):
    categories = get_categories_by_document(document_id)

    for category in categories:
        if category["frontend_id"]:
            continue

        category_detail = get_category(category["id"])
        if not category_detail["bins"]:
            # TODO: log error
            continue

        do = ("\n".join([w.lower().capitalize() for w in category_detail["waste_ok"]]),)
        dont = (
            "\n".join([w.lower().capitalize() for w in category_detail["waste_not"]]),
        )

        category_object = Category.objects.filter(
            municipality_id=municipality_id, name=category["id"]
        ).first()
        if category_object:
            # TODO: better merging?
            category_object.do += f"\n{do}"
            category_object.dont += f"\n{dont}"
            category_object.save()
        else:
            target, _ = Target.objects.update_or_create(
                municipality_id=municipality_id,
                name=category_detail["bins"][0],
                # TODO: handle multiple bins returned by LLM
            )

            category_object = Category.objects.create(
                municipality_id=municipality_id,
                name=category["id"],
                do="\n".join(category_detail["waste_ok"]),
                dont="\n".join(category_detail["waste_not"]),
                target=target,
            )

        _set_category_frontend_id(category["id"], str(category_object.id))
