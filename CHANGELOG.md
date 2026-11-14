# Changelog

## Non publié

- Revue du bilan 0011-0020 acceptée. Étape 9 : avant une diffusion publique, vérifier
  les fichiers suivis et l'historique publié, auteurs de commits compris (motif
  `personal-data-in-public-repo`, 3 projets en un mois).
- Vocabulaire partagé enrichi : `personal-data-in-public-repo`,
  `install-prerequisite-unverified`, `docs-out-of-sync`, `distribution-status-ambiguity`.

## [0.3.1] - 2026-11-06

- Décisions `GO`, `GO conditionnel` et `NO-GO` définies dans la rubrique : toute action
  requise avant la diffusion rend la décision conditionnelle. Écart observé sous Claude,
  qui rendait GO là où Codex rendait GO conditionnel pour le même constat.
- Description du skill enrichie de déclencheurs explicites (évaluer une diffusion, une
  release, un lancement, verdict GO / NO-GO) : le skill ne s'activait pas dans un cas sur
  trois sous Claude.
- `usage_log.py record --input fichier.json` : voie recommandée pour journaliser. Sous
  Claude, la longue ligne de commande de `record` était refusée par le contrôle des
  commandes (0 enregistrement sur 9 essais). Le fichier refuse les champs inconnus.
- `review_usage.py` fonctionne en mode `python -I` : l'import de `usage_log` échouait,
  si bien que le bilan ne pouvait jamais être lancé par un agent qui isole Python.
- Évaluation sous Claude du cas A (pilote accompagné) : GO, là où Codex rendait GO
  conditionnel. Décision de Jo : GO est juste, l'étape 10 n'exige que des signaux
  observables, sans seuil chiffré. Aucune règle ajoutée.

## [0.3.0] - 2026-11-06

Corrections issues de la lecture des 14 usages réels du pilote.

**Migration (Windows, journal antérieur).** Copier le contenu de l'ancien dossier vers
`~/.local/share/product-adoption-review/`, fichier `install-id` compris pour conserver les
pseudonymes de projet. L'ancien dossier est l'un des deux suivants :

- `%LOCALAPPDATA%\Codex\product-adoption-review\` ;
- avec l'application Codex du Microsoft Store :
  `%LOCALAPPDATA%\Packages\OpenAI.Codex_<id>\LocalCache\Local\Codex\product-adoption-review\`.

Tant que la copie manque, `usage_log.py status` renvoie `legacy_state_dir` et le nombre
d'usages non migrés. Garder l'ancien dossier jusqu'à vérification des chiffres.

- **Emplacement d'état unique** `~/.local/share/product-adoption-review` (ou
  `$XDG_DATA_HOME`) sur tous les systèmes : l'application Codex du Microsoft Store
  virtualisait `%LOCALAPPDATA%`, rendant le journal introuvable et scindant le compteur.
  Le bilan est référencé en chemin relatif.
- Commande `usage_log.py issues` : vocabulaire partagé et identifiants du journal ;
  `record` signale un identifiant inédit. Un identifiant ne nomme jamais un projet.
- Seuils de promotion calculés sur tout l'historique, et non plus sur le seul lot.
- Décision humaine enregistrée par `review_usage.py --decide` ; `status` liste les bilans
  acceptés et non décidés.
- README : exemple de verdict ; CI sur Python 3.10 et 3.13.
- Premier bilan (0001-0010) accepté : ses cinq motifs récurrents confirment des étapes
  existantes, sans nouvelle règle ; identifiant `demo-missing` ajouté au vocabulaire.

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
