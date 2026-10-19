# Serveur MCP RULA sur Clever Cloud

Ce runbook prépare une application Clever Cloud indépendante pour le transport HTTP du serveur MCP. Il s’applique après la fusion humaine des PR1 à PR4. Aucun provisionnement ni déploiement n’est effectué par ce document.

Le serveur MCP lit les transcripts produit et BizDev déjà confirmés et anonymisés dans RULA, puis enregistre les rapports Markdown dans la table `rapports_claude`. Il n’appelle pas Albert et ne lance aucune migration. La migration RULA `002_rapports_claude.sql` doit donc avoir été appliquée par le déploiement backend RULA avant le premier démarrage du serveur MCP.

## Ressources et séparation

Dans l’organisation Clever Cloud choisie pour RULA, créer une application Docker dédiée nommée par exemple `lab-anssi-rula-mcp`. Lier cette application à l’addon PostgreSQL RULA déjà utilisé par le backend. Ne pas créer d’addon ni de base supplémentaire. Vérifier que l’addon lié est bien la base de l’environnement RULA visé.

Dans l’application MCP, définir `CC_DOCKERFILE=MCP.Dockerfile` et `CC_DOCKER_EXPOSED_HTTP_PORT=8080`. Le conteneur écoute sur `0.0.0.0:8080`, et le proxy Clever Cloud publie son HTTPS. Le processus ASGI est `serveur_mcp:app` avec le transport HTTP stateless sur `/mcp`; la route `/healthz` ne renvoie que l’état minimal du processus.

Configurer dans l’application MCP :

```text
RULA_MCP_HOTE=0.0.0.0
RULA_MCP_PORT=8080
RULA_MCP_BEARER_TOKEN=<secret unique généré localement>
```

La connexion à la base suit `charge_configuration()`. Les variables `DB_HOTE`, `DB_PORT`, `DB_NOM`, `DB_UTILISATEUR` et `DB_MOT_DE_PASSE` ont priorité lorsqu’elles sont renseignées; sinon la configuration lit les variables `POSTGRESQL_ADDON_*` de l’addon lié. Vérifier la correspondance exacte des noms injectés par Clever Cloud avant le démarrage. Conserver les identifiants de base exclusivement dans Clever Cloud.

Générer un bearer aléatoire dédié à cette application dans PowerShell. La commande crée le fichier d’en-têtes sans afficher le secret, puis restreint son ACL au compte Windows courant :

```powershell
$repertoire = Join-Path $env:LOCALAPPDATA 'RULA-MCP'
New-Item -ItemType Directory -Force $repertoire | Out-Null
$chemin = Join-Path $repertoire 'rula-mcp-headers.txt'
if (Test-Path $chemin) { throw 'Le fichier existe déjà. Choisissez un autre nom ou effectuez une rotation explicite du bearer.' }
$octets = New-Object byte[] 48
$generateur = [Security.Cryptography.RandomNumberGenerator]::Create()
$generateur.GetBytes($octets)
$generateur.Dispose()
$jeton = [Convert]::ToBase64String($octets).TrimEnd('=').Replace('+', '-').Replace('/', '_')
[IO.File]::WriteAllText($chemin, "Authorization: Bearer $jeton`n", [Text.UTF8Encoding]::new($false))
icacls.exe $chemin /inheritance:r /grant:r "${env:USERDOMAIN}\${env:USERNAME}:(F)"
notepad.exe $chemin
```

Copier la valeur après `Bearer` dans `RULA_MCP_BEARER_TOKEN` dans le panneau de l’application Clever Cloud. Enregistrer le même fichier local pour Claude Desktop. Ne pas le mettre dans le dépôt, les arguments du processus, une URL, GitHub Actions ou des journaux. L’authentification MCP utilise ce bearer; elle est distincte de la protection HTTP Basic de l’application RULA. Les identifiants de l’application et le token MCP ne doivent jamais réutiliser ceux de l’environnement `DEMO`.

## Workflow GitHub manuel

Après fusion des fichiers sur `main`, créer l’environnement GitHub Actions `MCP`, avec les secrets suivants, propres à l’application MCP :

```text
CLEVER_MCP_TOKEN
CLEVER_MCP_SECRET
CLEVER_MCP_ID_APP
CLEVER_MCP_ID_ORGANISATION
```

Créer ou lier l’application Clever Cloud et l’addon avant de lancer le workflow. Depuis Actions, lancer **Déploiement MCP** avec la branche `main`. Le workflow refuse toute autre référence, n’a pas de déclencheur automatique, et ne lit que les quatre secrets de l’environnement `MCP`. Il ne modifie pas le workflow DÉMO.

## Configuration de Claude Desktop sous Windows

Créer le fichier d’en-têtes avec la commande ci-dessus. Elle refuse d’écraser un fichier existant; pour faire tourner un bearer, révoquer l’ancien côté Clever Cloud puis choisir explicitement un nouveau chemin de fichier. Le fichier doit rester hors du dépôt.

Sauvegarder `claude_desktop_config.json`, puis fusionner uniquement l’entrée `mcpServers.rula-mcp-distant` suivante. Préserver les propriétés racine existantes, notamment `preferences` et `coworkUserFilesPath`, ainsi que tous les autres serveurs `mcpServers` :

```json
{
  "mcpServers": {
    "rula-mcp-distant": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote@0.15.1",
        "https://<hote-clever>/mcp",
        "--header-file",
        "C:\\Users\\<utilisateur>\\AppData\\Roaming\\Claude\\rula-mcp-headers.txt"
      ]
    }
  }
}
```

`mcp-remote` transmet le bearer depuis le fichier d’en-têtes plutôt que depuis les arguments visibles du processus. Redémarrer Claude Desktop puis vérifier que les trois outils `lister_transcripts`, `lire_transcript` et `enregistrer_analyse` sont disponibles. Le transport stdio local validé pendant le POC reste disponible séparément; ne pas modifier sa configuration ni celle du serveur `rula-sonde`.

## Contrôles après fusion et déploiement autorisé

Avant le premier déploiement, vérifier la fusion des PR1–PR4, l’état de la migration `002_rapports_claude.sql` sur la base RULA ciblée, la liaison à cette même base, les trois variables `RULA_MCP_*` du serveur et l’environnement GitHub `MCP` avec ses quatre secrets. Le workflow ne doit être lancé qu’après ces vérifications et la décision humaine de déployer.

Après déploiement, vérifier `GET https://<hote-clever>/healthz`, puis confirmer qu’un appel MCP sans bearer et un bearer incorrect sont refusés. Avec la configuration Claude Desktop, effectuer la recette sur un transcript de test déjà pseudonymisé et confirmé : le retrouver par `lister_transcripts`, lire ses blocs via `lire_transcript`, enregistrer un rapport Markdown avec `enregistrer_analyse`, puis relire le rapport dans RULA. Ne pas utiliser un transcript de production comme donnée de recette sans autorisation dédiée. Confirmer dans les journaux qu’aucun bearer ou contenu de transcript n’a été écrit.

Références : [déploiement Docker Clever Cloud](https://www.clever-cloud.com/developers/doc/applications/docker/) pour `CC_DOCKERFILE`, le port HTTP Docker et le conteneur; [référence des variables Clever Cloud](https://www.clever-cloud.com/developers/doc/reference/reference-environment-variables/) pour `CC_DOCKER_EXPOSED_HTTP_PORT`; [README de mcp-remote](https://github.com/punkpeye/mcp-remote/blob/main/README.md) pour `--header-file` et la configuration Claude Desktop.
