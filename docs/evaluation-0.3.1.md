# Évaluation de la version 0.3.1 sous Claude Code — 2026-11-06

Complète [`evaluation-0.2.0.md`](evaluation-0.2.0.md), qui portait sur Codex. Cette
évaluation répond à une question : le skill fonctionne-t-il aussi sous Claude Code ?

## Méthode

Chaque essai est une session `claude -p` neuve (mode non interactif, sortie
`stream-json`), lancée sur une copie isolée d'une des trois fixtures synthétiques
(`tests/fixtures/case-a`, `case-b`, `case-c`) et sur un état isolé
(`PRODUCT_ADOPTION_REVIEW_STATE_DIR`). Le skill était installé par jonction dans
`~/.claude/skills/`. Les transcriptions ont été analysées par script : skill déclenché,
verdict rendu, refus d'outils, enregistrement du journal.

Les fixtures sont synthétiques ; ces essais ne comptent pas comme des usages réels.

## Résultats

| Mesure | Avant correction | Après correction (0.3.1) |
|---|---|---|
| Skill déclenché | 2 cas sur 3 | 3 cas sur 3 (un essai par cas) |
| Verdict conforme à l'attendu | 6 sur 6 (deux essais par cas) | 3 sur 3 : A `GO`, B `NO-GO`, C `GO` |
| Journal enregistré | 0 sur 9 essais | 1 sur 1 (cas B : 4 constats, `stable-release`) |

Défauts corrigés dans la 0.3.1, tous observés pendant ces essais :

- le skill ne s'activait pas sur une demande d'évaluation de diffusion : la description
  nomme maintenant les déclencheurs ;
- la commande `record` en longue ligne était refusée par le contrôle des commandes de
  Claude Code : `record --input fichier.json` est la voie recommandée ;
- `review_usage.py` échouait sous `python -I` (import de `usage_log`) ;
- les décisions `GO` et `GO conditionnel` n'étaient pas définies.

## Écart de verdict, tranché

Sur le cas A (pilote accompagné), Claude rend `GO` là où Codex rendait `GO conditionnel`
pour le même constat. Décision du mainteneur : `GO` est juste, l'étape 10 n'exige que des
signaux observables, sans seuil chiffré. Aucune règle n'a été ajoutée.

## Limites

- Un seul essai par cas dans l'état final ; les passages précédents n'avaient que deux
  répétitions sur certains cas. Aucune mesure de variance.
- L'enregistrement du journal n'est vérifié après correction que sur le cas B.
- Trois fixtures choisies, sans juge en aveugle ni comparaison à un autre skill.
- Le déclenchement et l'installation de la 0.3.1 sous Codex ne sont pas revérifiés.
- Un audit réel sous Claude (19e usage du journal) a ensuite confirmé le chemin complet
  sur un dépôt réel, sans mesure de répétabilité.
