---
name: product-adoption-review
description: "Audite la mise en produit lorsqu'un projet, dépôt, plugin, application, document ou autre livrable doit être diffusé à des utilisateurs externes. Vérifie promesse, démonstration, installation, découvrabilité, distribution et mesure, puis journalise localement les constats assainis. Ne pas activer pour le développement interne ordinaire."
license: MIT
metadata:
  category: productivity
  tags: "productization, launch, adoption, release"
---

# Product Adoption Review

Évaluer si un livrable externe est compréhensible, essayable, distribuable et mesurable,
sans confondre qualité technique et adoption.

## Périmètre

Activer ce skill pour un lancement, une release, un README public, un plugin, une
marketplace, une documentation utilisateur ou une stratégie d'adoption. Ne pas
l'appliquer aux tâches internes sans diffusion externe.

## Audit

1. Identifier l'audience et le problème concret qu'elle reconnaît déjà.
2. Formuler une promesse testable en une phrase, centrée sur le résultat utilisateur.
3. Montrer le changement avant d'expliquer le système : démonstration, avant/après ou
   parcours court.
4. Vérifier qu'un nom, un dépôt et un appel à l'action désignent clairement le produit.
5. Réduire l'installation au chemin le plus court sûr, puis documenter vérification,
   mise à jour et désinstallation.
6. Distinguer plateformes annoncées et plateformes réellement testées.
7. Renseigner description, topics, langues, licence et métadonnées de découverte.
8. Préparer les canaux de diffusion sans publier ni contacter de tiers sans autorisation.
9. Définir des signaux observables à J+7 et J+30 sans télémétrie implicite.
10. Séparer dans le rapport : validation statique, preuve comportementale et adoption.

Lire [references/review-rubric.md](references/review-rubric.md) pour les niveaux de
sévérité et les critères de promotion d'un apprentissage.

## Journal local obligatoire

Après livraison d'un audit terminé, exécuter `scripts/usage_log.py record` avec des
métadonnées assainies. Ne jamais enregistrer prompt, réponse, chemin absolu, secret,
donnée personnelle ou contenu métier. Signaler si l'écriture échoue ; ne pas utiliser
un fichier suivi par Git comme repli.

Exécuter ensuite `scripts/review_usage.py`. Le script produit un bilan local lorsqu'un
nouveau lot de dix usages terminés est disponible. Mentionner le chemin du bilan, mais
ne modifier aucune règle officielle sans validation explicite de l'utilisateur.

## Promotion d'un apprentissage

Une règle est candidate après trois occurrences dans au moins deux projets distincts.
Un défaut bloquant reproductible peut être candidat dès la première occurrence.
Le bilan propose un changement minimal et les tests associés. Après accord seulement,
créer une branche, modifier le dépôt officiel, valider, puis ouvrir une PR sans fusion
automatique.

## Résultat attendu

Rendre en priorité les blocages d'adoption, puis les corrections à fort effet. Ne pas
recommander une nouvelle plateforme, un rebranding ou une publication externe sans lien
avec les preuves collectées et le périmètre demandé.
