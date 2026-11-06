# Changelog

## [0.2.0] - 2026-09-22

- Verdicts rattachés à un niveau de diffusion explicite.
- Preuves qualifiées par état et portée de version.
- Regroupement des constats par identifiant stable, avec compatibilité des anciens journaux.
- Candidats d'amélioration enrichis d'un changement minimal et d'un test de non-régression.
- Promotion immédiate d'un blocage limitée aux défauts reproductibles.
- Évaluation ciblée Sol/élevé sur trois fixtures synthétiques de diffusion contrastées.
- Contrat CLI du journal documenté après un défaut de sortie observé ; aucune inflation
  du compteur réel par les fixtures ni par les constats doublonnés d'un même audit.
- Journal : une écriture interrompue ne fait plus perdre l'événement suivant ni ne rend
  le journal illisible ; un verrou orphelin de plus de 60 s est levé.
- Filtre de sensibilité étendu aux clés `sk-`/`AKIA`, e-mails et chemins Unix, `~` et UNC ;
  les URL publiques sans paramètres sont acceptées.
- Le script refuse plus de quatre constats, l'ancien format à trois champs à l'écriture
  et un seuil non positif.
- Manifeste Claude aligné sur 0.2.0 ; CI sous Ubuntu et Windows, jeton en lecture seule.
- Installation documentée : emplacements, vérification, mise à jour, désinstallation.

## [0.1.0] - 2026-09-21

- Pilote privé : audit transverse, journal local assaini et bilan par lots de dix usages.
