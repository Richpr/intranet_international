from datetime import datetime
from rh.models import DocumentCounter
from django.db import transaction

def generer_reference_sequentielle(document_type, code_entite="NTC-G", code_departement="HR", code_document_prefix=""):
    """
    Génère une référence séquentielle unique pour un type de document donné,
    avec un reset annuel du compteur.
    """
    current_year = datetime.now().year
    with transaction.atomic():
        counter, created = DocumentCounter.objects.get_or_create(
            document_type=document_type,
            year=current_year,
            defaults={'last_number': 0}
        )
        counter.last_number += 1
        counter.save()

        numero_formate = str(counter.last_number).zfill(3)
        
        reference_complete = f"Réf : {code_entite}/{code_departement}/{code_document_prefix}/{numero_formate}/{current_year}"
        return reference_complete