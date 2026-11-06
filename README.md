# Product Adoption Review

Skill transverse pour éviter qu'un projet techniquement solide soit publié sans promesse
claire, démonstration, installation vérifiable ou stratégie de diffusion.

## Périmètre

Le skill s'active lors d'une diffusion externe : release, README public, plugin,
marketplace, application, document utilisateur ou lancement. Il reste inactif pendant
le développement interne ordinaire.

## Boucle d'amélioration locale

Après chaque audit terminé, le skill écrit une entrée minimale et pseudonymisée dans :

```text
%LOCALAPPDATA%\Codex\product-adoption-review\usage.jsonl
```

Le chemin du projet est haché, jamais conservé. Le script refuse les formats connus de
chemins, de secrets (clés `sk-`, `ghp_`, `AKIA`…) et d'adresses e-mail, mais ce filtre ne
détecte pas tout : l'agent reste responsable de n'enregistrer ni prompt, ni réponse, ni
donnée personnelle.
Chaque lot de dix usages produit un bilan Markdown local. Le bilan peut proposer une
évolution, mais ne modifie jamais automatiquement le skill officiel.

Depuis la version 0.2.0, chaque audit précise le niveau de diffusion évalué, l'état des
preuves et leur portée de version. Les problèmes équivalents partagent un identifiant
stable : le bilan peut ainsi les regrouper malgré des résumés ou des langues différents.
Chaque candidat contient le changement minimal et le test de non-régression proposés.

## Gouvernance

- dépôt pilote privé en version `0.x` ;
- règle candidate après trois occurrences dans deux projets, sauf blocage reproductible ;
- validation humaine obligatoire ;
- branche, test de non-régression et PR sans fusion automatique ;
- publication `1.0.0` après le premier bilan accepté.

Un verdict porte toujours sur un niveau explicite : pilote accompagné, bêta fermée,
bêta publique ou diffusion stable. L'absence de preuve d'adoption ne suffit pas à
refuser un pilote destiné à recueillir cette preuve.

## Installation pilote

Installer `skills/product-adoption-review/` dans le profil de l'agent. Le skill est
découvrable automatiquement uniquement pour les travaux de diffusion externe.

## Confidentialité

Aucune télémétrie et aucun appel réseau. Les scripts utilisent uniquement la bibliothèque
standard Python et échouent explicitement si le journal local ne peut pas être écrit.

Le déroulé de la première série de dix usages est détaillé dans [`docs/pilot.md`](docs/pilot.md).
