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

Les prompts, réponses, chemins de projet, secrets et données personnelles sont refusés.
Chaque lot de dix usages produit un bilan Markdown local. Le bilan peut proposer une
évolution, mais ne modifie jamais automatiquement le skill officiel.

## Gouvernance

- dépôt pilote privé en version `0.x` ;
- règle candidate après trois occurrences dans deux projets, sauf blocage reproductible ;
- validation humaine obligatoire ;
- branche, test de non-régression et PR sans fusion automatique ;
- publication `1.0.0` après le premier bilan accepté.

## Installation pilote

Installer `skills/product-adoption-review/` dans le profil de l'agent. Le skill est
découvrable automatiquement uniquement pour les travaux de diffusion externe.

## Confidentialité

Aucune télémétrie et aucun appel réseau. Les scripts utilisent uniquement la bibliothèque
standard Python et échouent explicitement si le journal local ne peut pas être écrit.
