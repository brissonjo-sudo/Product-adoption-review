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

Consulter les identifiants existants du journal avant d'en créer un nouveau, sans
modifier les anciens événements. Ces identifiants désignent des problèmes précis :

| Identifiant suggéré | Problème |
|---|---|
| `release-evidence-mismatch` | La preuve ne porte pas sur la version distribuée |
| `release-version-mismatch` | Le numéro du paquet diverge de celui de son contenu |
| `installation-lifecycle-incomplete` | Acquisition, vérification, mise à jour ou retrait manquent |
| `artifact-unavailable` | L'artefact demandé ne peut pas être obtenu |
| `claim-evidence-mismatch` | Une affirmation actuelle dépasse ou contredit la preuve |
| `adoption-feedback-missing` | Aucun retour volontaire n'est organisé |

Ce sont des exemples, pas une obligation de fusionner des problèmes distincts.

## Validation isolée

Pour une fixture synthétique ou un test du schéma, définir
`PRODUCT_ADOPTION_REVIEW_STATE_DIR` vers un répertoire temporaire propre à ce test
avant d'exécuter les scripts. Vérifier que le compteur réel est inchangé après le test.
Une proposition JSON seule ne vaut pas un enregistrement validé.
