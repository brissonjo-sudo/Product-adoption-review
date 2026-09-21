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

1. Fixer le périmètre avant de conclure : artefact réellement disponible, audience,
   canal et niveau visé (`assisted-pilot`, `closed-beta`, `public-beta` ou
   `stable-release`). Rendre le verdict pour ce niveau précis.
2. Identifier le problème concret que l'audience reconnaît déjà.
3. Formuler une promesse testable en une phrase, centrée sur le résultat utilisateur.
4. Montrer le changement avant d'expliquer le système : démonstration, avant/après ou
   parcours court.
5. Vérifier qu'un nom, un dépôt et un appel à l'action désignent clairement le produit.
6. Réduire l'installation au chemin le plus court sûr, puis documenter vérification,
   mise à jour et désinstallation.
7. Distinguer plateformes annoncées et plateformes réellement testées.
8. Renseigner description, topics, langues, licence et métadonnées de découverte.
9. Préparer les canaux de diffusion sans publier ni contacter de tiers sans autorisation.
10. Définir des signaux observables à J+7 et J+30 sans télémétrie implicite.
11. Qualifier chaque preuve comme `observed`, `declared`, `unverified` ou
    `contradictory`, et préciser si elle porte sur la version `current`, `earlier`,
    `unspecified` ou `not-applicable`.
12. Séparer dans le rapport : validation statique, preuve comportementale et adoption.

L'absence de preuve d'adoption n'interdit pas à elle seule un pilote dont le but est de
la recueillir. Elle bloque un niveau seulement si cette preuve est nécessaire pour
accéder sans danger à ce niveau. Distinguer une preuve absente d'un échec observé.

Lire [references/review-rubric.md](references/review-rubric.md) pour les niveaux de
sévérité et les critères de promotion d'un apprentissage.

## Journal local obligatoire

Après livraison d'un audit terminé, exécuter `scripts/usage_log.py record` avec des
métadonnées assainies. Ne jamais enregistrer prompt, réponse, chemin absolu, secret,
donnée personnelle ou contenu métier. Signaler si l'écriture échoue ; ne pas utiliser
un fichier suivi par Git comme repli.

Chaque constat reçoit un `issue-id` stable en kebab-case, réutilisé lorsque le même
problème apparaît dans un autre projet, même si le résumé change de langue ou de
formulation. Le format courant est :

`issue-id|catégorie|sévérité|preuve|version|reproductible|résumé`

Ajouter pour chaque constat :

`issue-id|changement-minimal|test-de-non-régression`

Renseigner aussi l'audience, le canal et le niveau de diffusion cible. Limiter le journal
à deux à quatre constats décisifs ; les agrégats du bilan décrivent cette sélection et
ne constituent pas un taux d'échec des projets.

Exécuter ensuite `scripts/review_usage.py`. Le script produit un bilan local lorsqu'un
nouveau lot de dix usages terminés est disponible. Mentionner le chemin du bilan, mais
ne modifier aucune règle officielle sans validation explicite de l'utilisateur.

## Promotion d'un apprentissage

Une règle est candidate après trois occurrences dans au moins deux projets distincts.
Un défaut bloquant peut être candidat dès la première occurrence uniquement si sa
reproductibilité est établie.
Le bilan propose un changement minimal et les tests associés. Après accord seulement,
créer une branche, modifier le dépôt officiel, valider, puis ouvrir une PR sans fusion
automatique.

## Résultat attendu

Rendre une décision `GO`, `GO conditionnel` ou `NO-GO` pour le niveau de diffusion
évalué. Rendre en priorité les blocages d'adoption, puis les corrections à fort effet. Ne pas
recommander une nouvelle plateforme, un rebranding ou une publication externe sans lien
avec les preuves collectées et le périmètre demandé.
