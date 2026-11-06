# Pilote privé — dix usages

## Sortie attendue de chaque usage

1. Audit livré sur une diffusion externe réelle.
2. Verdict rattaché à un artefact, une audience, un canal et un niveau de diffusion.
3. Preuves qualifiées par état et portée de version.
4. Entrée locale assainie et pseudonymisée, avec identifiants stables des problèmes.
5. Statut du compteur annoncé si l'écriture a réussi.

## Revue du dixième usage

Le rapport généré regroupe les motifs par identifiant stable, présente les étapes de
diffusion et les états de preuve, puis propose un changement minimal et son test. Les
comptages décrivent les constats sélectionnés pour le journal ; ils ne mesurent pas un
taux d'échec des projets. Les seuils de promotion se calculent sur tout l'historique : un
motif réparti sur plusieurs lots reste promouvable. La revue humaine décide pour chaque
motif : conserver, documenter, proposer une règle ou rejeter. La décision sur le bilan est
enregistrée par `review_usage.py --decide <lot> --status accepted|rejected --note "…"` ;
`usage_log.py status` liste alors le lot dans `accepted_reviews`.

Une modification approuvée reçoit une branche, un test de non-régression et une PR sans
fusion automatique. La publication du dépôt et la version `1.0.0` restent bloquées tant
que cette première revue n'est pas acceptée.

L'évaluation ciblée du candidat 0.2.0 et ses limites sont détaillées dans
[`evaluation-0.2.0.md`](evaluation-0.2.0.md). Les fixtures synthétiques utilisent un état
isolé et ne comptent pas comme de nouveaux usages produit.
