# Évaluation ciblée du candidat 0.2.0 — 2026-10-04

## Méthode

Trois évaluateurs distincts `gpt-5.6-sol`, raisonnement `high`, ont reçu chacun
le skill, sa rubrique, une demande de revue et les seuls artefacts de leur cas.
Ils n'ont pas reçu les verdicts attendus ni les conclusions des autres évaluateurs.
Les fixtures sous `tests/fixtures/case-a`, `case-b`, `case-c` sont synthétiques,
versionnées et dépourvues de données réelles. Elles ne constituent pas trois usages
produit réels et ne font pas progresser le compteur d'adoption.

Les critères observés : verdict relatif au niveau demandé, distinction entre preuve
absente et échec, portée de version, absence de surenchère de plateforme et possibilité
de délivrer un GO pour un artefact documentaire à promesse étroite.
Les règles de décision testées sont celles du commit `cc6747f`. La documentation
du contrat de journal a été précisée pendant la campagne après un défaut observé,
puis les trois enregistrements ont été vérifiés séparément sur le contrat corrigé.

## Verdicts observés

| Cas | Niveau demandé | Résultat | Justification décisive |
|---|---|---|---|
| A : fiche en premier pilote accompagné | `assisted-pilot` | GO conditionnel | Qualifier les dix minutes comme objectif de l'essai et définir le critère de réussite ; l'absence d'adoption préalable ne bloque pas le pilote |
| B : outil d'anonymisation sans archive, exemple contradictoire | `stable-release` | NO-GO | L'exemple conserve l'identifiant malgré la promesse actuelle et l'artefact est indisponible ; le rapport 0.8 ne valide pas 1.0 |
| C : fiche documentaire complète remise directement | `stable-release` | GO | Contenu, version, droits, exemple et cycle de vie correspondent à la promesse ; les données d'adoption futures ne sont pas nécessaires pour cette remise |

Les trois familles de décision attendues sont observées. Les propositions d'évolution
restent relatives aux artefacts évalués, sans exiger de rebranding ou de service web.
Le cas B distingue la contradiction inspectable de l'impossibilité de rejouer un logiciel.

## Défaut observé et correction

La proposition initiale du cas A inventait des champs `artifact_type` et `verdict`
et plaçait les propositions dans les constats. Elle n'était pas un événement produit
par le script et ne pouvait pas être présentée comme un enregistrement validé.
Le skill renvoie maintenant vers `references/journal-schema.md` : options CLI exactes,
séparation `findings`/`improvements`, identifiants stables, zéro constat autorisé pour un
audit sans défaut et état isolé obligatoire pour une évaluation synthétique.

La boucle protège aussi les seuils : un identifiant n'apparaît qu'une fois par audit,
et un ancien événement doublonné ne compte qu'une occurrence pour ce problème.

## Validation du contrat corrigé

Les trois agents ont exécuté le vrai `usage_log.py record` puis `status`, avec
`PRODUCT_ADOPTION_REVIEW_STATE_DIR` pointant chacun sur son propre répertoire
temporaire. Les trois exécutions finales ont renvoyé `ok: true`, code 0, schéma 2,
un usage terminé dans le compteur isolé et aucun bilan dû. Certaines premières
tentatives ont échoué avant enregistrement (démarrage du processus ou arguments).

- A : deux constats et deux propositions, verdict de pilote inchangé.
- B : quatre constats et quatre propositions, identifiants rapprochés du vocabulaire
  documenté, verdict stable inchangé.
- C : zéro constat et zéro proposition ; l'absence de résultats d'adoption n'a pas
  été transformée en défaut du paquet documentaire.

Le compteur réel affiche onze usages, dont le dernier est antérieur à la campagne
et concerne un autre audit. Son journal n'a reçu aucun des trois événements synthétiques.
Le prochain bilan reste prévu à vingt usages réels.

Validation automatisée : quinze tests unitaires réussis, validation structurelle du
skill réussie et diff sans erreur. La CI a également exécuté avec succès les douze
tests du commit initial `cc6747f` après relance du contrôle autrefois bloqué ; les
contrôles du complément sont vérifiés dans la PR.

## Limites

Cette campagne est une vérification ciblée sur trois fixtures choisies, sans répétitions,
sans juges en aveugle et sans comparaison au skill précédent. Elle vérifie des décisions
observées ; elle ne mesure ni taux de faux positifs sur des projets réels, ni adoption,
ni performance dans ChatGPT. Les agents partagent le même modèle. Aucune preuve
technique fictive des dossiers ne doit être réutilisée comme validation d'un produit.

Le passage à une release publique 1.0 exige une décision de diffusion distincte.
