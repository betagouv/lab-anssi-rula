# ADR 0004 — Réduire RULA à la pseudonymisation de PDF

Statut : accepté

## Contexte

Le prototype RULA est recentré sur la pseudonymisation humaine de PDF d’entretiens Produit et de retours BizDev pour MSS et MSC. Les parcours d’analyse, de projets et de collecte de fonctionnalités ne font plus partie du produit. Les données déjà stockées incluent des lignes historiques `ux` et des lignes Produit/BizDev non confirmées; le fait qu’une ancienne ligne soit marquée confirmée ne suffit pas à la conserver.

## Décision

L’application ne conserve que les produits MSS et MSC et les transcripts PDF confirmés dont le type est `produit` ou `bizdev`, en préservant leurs identifiants, contenu, contexte, locuteurs, date de source et dates de création/modification. Les autres tables et parcours sont retirés. La migration versionnée laisse intactes les migrations historiques et n’est jamais rejouée sur le volume actif pendant la construction de l’image.

L’import, la préparation avec progression et reprise, la relecture corrigible, la confirmation, la consultation, le téléchargement PDF et la suppression forment le parcours du produit. Le PDF original et les données provisoires ne sont pas persistés; seul le résultat explicitement confirmé est conservé. Les noms d’affichage de la liste et du PDF commencent par `pseudonymiser_`, sans préfixe répété.

La migration `002_pseudonymisation_seule.sql` s’exécute dans la transaction du runner de migrations. En production, le hook post-build l’exécute avant le nouveau runtime : l’opération destructive requiert donc une fenêtre de maintenance coordonnée, une sauvegarde opérationnelle préalable et l’arrêt des anciennes instances avant le build. Les sauvegardes Clever Cloud restent hors périmètre.

## Conséquences

- Une migration en base vide commence par l’ancien schéma `001`, puis réduit ce schéma au modèle de pseudonymisation.
- Une base existante ne conserve que les lignes satisfaisant simultanément les conditions de type, confirmation et rattachement MSS/MSC; les identifiants des lignes retenues restent inchangés.
- Toute donnée hors périmètre dans les tables applicatives supprimées est perdue après validation de la transaction.
- Le rollback sûr est une restauration de la sauvegarde opérationnelle, avec l’ancienne application arrêtée; les données effacées ne peuvent pas être reconstruites depuis la migration.
- Aucune migration ne cible les sauvegardes Clever Cloud.
