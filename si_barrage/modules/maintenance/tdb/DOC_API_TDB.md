Documentation API — Dashboard Maintenance

1. Objectif de l’API 

Cette API permet d’afficher et de manipuler les données de maintenance d’un barrage hydroélectrique à travers un tableau de bord interactif.

Le dashboard permet notamment de :

- visualiser l’état global des équipements

- voir le nombre d’équipements Terminés, En cours ou En attente

- consulter un tableau récapitulatif des maintenances

- filtrer les équipements selon :

        * la première lettre de leur ID (nom de l'équipement)

        * leur statut

Les données sont stockées dans une base SQLite (barrage.db).

2. Structure générale des endpoints

Tous les endpoints du dashboard maintenance sont préfixés par : /maintenance/tdb

Par exemple : http://127.0.0.1:8000/maintenance/tdb/

3. Page principale du tableau de bord

Endpoint
GET /maintenance/tdb/
Rôle
(Cet endpoint affiche la page complète du dashboard maintenance)

Cette page contient :

le titre du tableau de bord, les KPI (indicateurs sur le statut des équipements recensés) les filtres, le tableau des maintenances

Cette page utilise la bibliothèque HTMX pour charger dynamiquement certaines parties du dashboard.


Exemple d’utilisation = Ouvrir directement dans un navigateur :

http://127.0.0.1:8000/maintenance/tdb/

***********************************ENDPOINTS*********************************

4. Endpoint des KPI

Endpoint
GET /maintenance/tdb/api/kpis
Rôle

Cet endpoint calcule et retourne les indicateurs principaux du dashboard :

nombre d’équipements Terminés, En cours et en attente

Ces indicateurs permettent d’avoir une vue globale rapide de la situation.

Paramètres: aucun paramètre n’est nécessaire.
Ces KPI sont automatiquement mis à jour toutes les 10 secondes grâce à HTMX.



5. Endpoint du tableau des maintenances
Endpoint
GET /maintenance/tdb/api/equipment-table

Rôle: cet endpoint renvoie le tableau récapitulatif des maintenances.

Le tableau contient les informations suivantes :

Colonne	Description
ID	Identifiant de l’équipement
Nom	Nom de l’équipement
Dernier statut	État actuel de la maintenance
Dernière MAJ	Date de la dernière mise à jour
Description	Description de la maintenance

Les lignes du tableau sont colorées selon le statut :

Statut	    Couleur
Terminé	    Vert
En cours	Orange
En attente	Rouge

Cela permet de repérer rapidement les équipements problématiques.

6. Paramètres de filtrage

L’endpoint du tableau accepte deux paramètres optionnels.

6.1 Filtrer par première lettre d’ID

Permet d’afficher uniquement les équipements dont l’ID commence par une lettre donnée.

Exemple
/maintenance/tdb/api/equipment-table?prefix=S

Cela affichera seulement les équipements dont l’ID commence par S


6.2 Filtrer par statut
Paramètre

Exemple: /maintenance/tdb/api/equipment-table?status=En%20cours

Cela affichera uniquement les maintenances En cours.

7. Combiner les filtres

Les deux filtres peuvent être utilisés simultanément.

Exemple : /maintenance/tdb/api/equipment-table?prefix=S&status=En%20cours

Cela affichera uniquement les équipements :

dont l’ID commence par S et dont le statut est En cours

8. Endpoint du filtre dynamique

Endpoint
GET /maintenance/tdb/api/id-prefix-filter


Rôle: Cet endpoint génère les menus de filtrage du dashboard.

Il retourne un bloc HTML contenant :

un filtre par première lettre d’ID

un filtre par statut

Ces filtres sont synchronisés avec le tableau grâce à HTMX.

Sortie: Fragment HTML contenant deux menus déroulants.

Exemple :

Filtre ID :      [ S ▼ ]
Filtre statut :  [ En cours ▼ ]

Quand l’utilisateur change un filtre :

une requête est envoyée automatiquement à l’API

le tableau est mis à jour instantanément

9. Fonctionnement avec HTMX

Le dashboard utilise HTMX, une bibliothèque JavaScript qui permet de charger dynamiquement du contenu HTML.

Cela signifie que :

certaines parties de la page sont chargées séparément

la page n’a pas besoin d’être rechargée entièrement

Exemple :

Page principale
     ↓
HTMX appelle /api/kpis
     ↓
HTMX appelle /api/equipment-table
     ↓
Les éléments apparaissent dans la page

Cela permet :

une interface plus fluide

des mises à jour automatiques

10. Exemple d’utilisation complète: 

Afficher le tableau complet:
        GET /maintenance/tdb/api/equipment-table
Filtrer par lettre:
        GET /maintenance/tdb/api/equipment-table?prefix=T
Filtrer par statut:
        GET /maintenance/tdb/api/equipment-table?status=Terminé
Filtrer par lettre et statut:
        GET /maintenance/tdb/api/equipment-table?prefix=T&status=En%20cours



        
11. Architecture simplifiée du dashboard

Le fonctionnement du dashboard peut être résumé ainsi :

Page dashboard
        │
        ▼
/maintenance/tdb/
        │
        ├── /api/kpis
        │      → indicateurs
        │
        ├── /api/id-prefix-filter
        │      → filtres
        │
        └── /api/equipment-table
               → tableau des maintenances

Chaque endpoint fournit une partie du dashboard.


ARCHITECTURE GLOBALE 

main.py
   │
   ▼
maintenance/router.py
   │
   ▼
maintenance/tdb/router.py
   │
   ▼
maintenance/tdb/services.py
   │
   ▼
Base de données (SQLite)

Dans le module maintenance, le code a été organisé en plusieurs fichiers afin de séparer les responsabilités et rendre l’application plus claire et plus facile à maintenir. Les fichiers router.py contiennent les routes de l’API, c’est-à-dire les URL accessibles par le client et les fonctions qui gèrent les requêtes HTTP (par exemple afficher le tableau de bord ou récupérer les données du tableau). Les fichiers services.py, eux, contiennent la logique métier, notamment les fonctions qui interrogent la base de données SQLite, appliquent les filtres et préparent les données avant de les envoyer au router. Cette séparation permet d’éviter de mélanger la gestion des requêtes web avec les opérations sur les données. De plus, un dossier tdb (tableau de bord) a été créé à l’intérieur du module maintenance afin d’isoler tout ce qui concerne le dashboard de maintenance. On y retrouve également un router.py et un services.py, mais uniquement dédiés aux fonctionnalités du tableau de bord (KPIs, filtres, tableau des maintenances). Cette organisation rend le projet plus modulaire, lisible et évolutif, car les fonctionnalités du dashboard sont regroupées dans un même espace sans alourdir les fichiers principaux du module maintenance.