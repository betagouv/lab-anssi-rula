# ADR 0005 : snapshot des termes noirs par préparation

Date : 2026-10-30

## Contexte

Les termes noirs doivent produire des masques obligatoires pour les nouvelles préparations. Une modification ultérieure de la liste ne doit ni réécrire les brouillons en cours ni changer les transcripts enregistrés.

## Décision

Capturer une fois la liste noire partagée avant la mise en file de chaque préparation et enregistrer ce tuple dans le transcript avec son contenu. Les objets antérieurs utilisent le snapshot vide. La relecture, la confirmation et toute modification utilisent seulement le snapshot de l’objet, jamais la liste courante.

## Conséquences

- Bénéfice : les règles d’une préparation restent stables à travers traitements asynchrones, reprise, confirmation et édition.
- Coût ou limite : le snapshot est conservé avec chaque transcript et ne change pas quand la liste globale est mise à jour.
- Alternatives écartées : consulter la liste courante dans le worker ou à chaque mutation, ce qui rendrait le résultat temporellement instable et pourrait altérer les objets historiques.
