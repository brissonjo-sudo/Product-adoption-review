# Revue demandée

Évaluer la diffusion stable publique de Nettoie-tableau, version 1.0.
Audience : utilisateurs bureautiques. Canal annoncé : téléchargement libre de l'archive
1.0 depuis la page de release. Promesse commerciale actuelle : « transforme un tableau
en texte anonyme prêt à partager et retire tous les identifiants ».

Cette fixture est synthétique ; aucune donnée personnelle réelle n'est utilisée.

## Artefact et résultats fournis

Aucune archive n'est disponible. La page de release dit « le téléchargement arrivera
plus tard », malgré le bouton Télécharger maintenant. Le seul extrait de sortie fourni
pour la version 1.0 conserve la colonne identifiant et sa valeur TEST-001 :

Entrée : `identifiant,texte` puis `TEST-001,exemple fictif`.
Sortie publiée : `identifiant: TEST-001; texte: exemple fictif`.

Le document `preuve.md` conserve cet exemple pour contrôle. Aucun exécutable n'est
fourni pour rejouer la transformation. La reproduction comportementale indépendante
est donc indisponible. La contradiction entre promesse et exemple est inspectable.
Licence, mise à jour, désinstallation et canal de retour ne sont pas documentés.

## Historique

Un ancien rapport version 0.8 dit qu'une transformation fonctionnait sur un tableau
sans colonne identifiant. Il ne valide pas la version 1.0 ni la promesse actuelle.
Un questionnaire J+7/J+30 est prévu mais aucun pilote n'a commencé.
