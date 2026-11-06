# Contrat du journal local v2

Le script `usage_log.py record` construit l'événement JSON. Fournir uniquement ses
arguments ; ne pas inventer des champs tels que `artifact_type` ou `verdict`.
Le verdict et ses limites sont enregistrés dans `outcome` et `decision`.

Arguments obligatoires : `--project-root` (haché, non conservé en clair),
`--artifact-kind` (`repository`, `plugin`, `application`, `document`, `release`, `other`),
`--trigger`, `--audience`, `--channel`, `--target-stage` et `--outcome`.
Ajouter `--completed` uniquement pour un audit terminé.

Arguments répétables :

- `--finding 'issue-id|categorie|severite|preuve|version|reproductible|resume'` ;
- `--improvement 'issue-id|changement-minimal|test'` ;
- `--decision 'decision assainie'` ;
- `--verification 'controle et limites'`.

Utiliser `true` ou `false` pour la reproductibilité. Le script refuse plus de quatre
`--finding` et l'ancien format à trois champs ; les anciens événements du journal restent
lus par le bilan. Chaque identifiant figure une seule fois par audit ; chaque constat
possède une proposition correspondante. Le script
conserve les propositions dans `improvements`, séparément de `findings`.
Un audit sans défaut comporte zéro `--finding` et zéro `--improvement`.

## Identifiants entre projets

Avant d'enregistrer, exécuter `usage_log.py issues`. La commande liste le vocabulaire
partagé (avec sa description) puis les identifiants déjà présents dans le journal, avec
leurs occurrences et leur nombre de projets. Réutiliser un identifiant existant dès que
le problème est de même nature, sans modifier les anciens événements.

Un identifiant nomme la **nature** du problème, applicable à n'importe quel projet. Il ne
contient jamais le nom d'un projet, d'un produit, d'un service ou d'une version. Exemple :
`installation-lifecycle-incomplete`, pas `plugin-x-install-missing`.

`record` renvoie `new_issue_ids` lorsqu'un identifiant est inédit. Ce n'est pas un refus :
un problème réellement nouveau mérite un nouvel identifiant. Ne pas fusionner des
problèmes distincts pour atteindre un seuil.

## Validation isolée

Pour une fixture synthétique ou un test du schéma, définir
`PRODUCT_ADOPTION_REVIEW_STATE_DIR` vers un répertoire temporaire propre à ce test
avant d'exécuter les scripts. Vérifier que le compteur réel est inchangé après le test.
Une proposition JSON seule ne vaut pas un enregistrement validé.
