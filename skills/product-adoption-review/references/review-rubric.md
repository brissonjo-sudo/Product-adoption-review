# Rubrique de revue

## Sévérités

- `info` : amélioration optionnelle sans effet démontré sur l'essai du produit.
- `minor` : friction réelle mais contournable.
- `major` : empêche une partie importante de l'audience de comprendre, installer ou vérifier.
- `blocker` : installation dangereuse ou impossible, promesse trompeuse, fuite de données,
  publication non autorisée ou affirmation de validation contredite par les preuves.

La sévérité dépend du niveau de diffusion évalué. Un manque acceptable pour un
`assisted-pilot` peut devenir `major` ou `blocker` pour une `stable-release`.
L'absence de preuve n'est pas un échec observé et ne devient pas automatiquement un
`blocker`.

## Décisions

La décision porte sur le niveau de diffusion évalué, jamais sur un niveau supérieur.

- `GO` : aucune action n'est requise avant de diffuser à ce niveau. Les améliorations
  restantes sont facultatives (`info` ou `minor` sans effet sur l'essai).
- `GO conditionnel` : la diffusion à ce niveau est acceptable **après** au moins une
  action nommée, réalisable avant la diffusion et vérifiable. Une action présentée comme
  « à faire avant la séance », « avant le pilote » ou « avant la release » rend la décision
  conditionnelle, même si elle paraît mineure.
- `NO-GO` : au moins un `blocker` ne peut pas être levé par une action simple avant la
  diffusion, ou la promesse est contredite par une preuve disponible.

Lister chaque condition d'un `GO conditionnel` avec son critère de vérification.

## Catégories

Utiliser une catégorie courte et stable : `audience`, `promise`, `demo`, `identity`,
`install`, `compatibility`, `discovery`, `distribution`, `measurement`, `evidence`.

## État des preuves

- `observed` : vérifié directement sur l'artefact ou reproduit pendant l'audit ;
- `declared` : affirmé par le projet, sans vérification indépendante dans l'audit ;
- `unverified` : preuve nécessaire absente ou inaccessible dans le périmètre ;
- `contradictory` : une preuve disponible contredit l'affirmation examinée.

Préciser aussi la portée : `current`, `earlier`, `unspecified` ou `not-applicable`.

## Identifiants de problèmes

Attribuer un identifiant kebab-case fondé sur la nature du problème, par exemple
`release-evidence-mismatch`. Réutiliser cet identifiant entre projets pour un problème
équivalent. Le résumé reste spécifique au cas audité ; il ne sert pas au regroupement.

## Promotion

Promouvoir une observation en règle candidate seulement si elle apparaît trois fois
dans au moins deux projets pseudonymisés, ou s'il s'agit d'un blocage reproductible.
Une préférence isolée reste dans le journal. Une correction officielle exige une
validation humaine et un test de non-régression.
