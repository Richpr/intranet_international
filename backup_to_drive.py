# intranet_international/backup_to_drive.py

import os
import zipfile
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# --- CONFIGURATION DU SCRIPT ---
# Le dossier Google Drive dans lequel les sauvegardes seront stockées.
# Si ce dossier n'existe pas, il sera créé lors du premier lancement.
DRIVE_FOLDER_NAME = "Intranet_International_Backups"

# Fichiers et dossiers à inclure dans l'archive
FILES_TO_BACKUP = [
    'db.sqlite3',
    'media',
]

def authenticate_drive():
    """Authentification PyDrive (utilise settings.yaml et génère token.json)"""
    
    # 1. Initialise l'authentification en lisant settings.yaml
    gauth = GoogleAuth(settings_file="settings.yaml")

    # 2. Tente de charger le jeton existant (pour les exécutions futures)
    gauth.LoadCredentialsFile("token.json")

    # 3. Si les identifiants ne sont pas chargés, lance l'authentification OOB (manuelle)
    if gauth.credentials is None:
        print("--- AUTHENTIFICATION REQUISE (Une seule fois) ---")
        
        # Le mode OOB (Out-of-Band) est nécessaire pour un serveur sans interface graphique
        # Il va imprimer un lien pour le navigateur et attendre un code
        gauth.LocalWebserverAuth() 
        
    # 4. Si l'authentification a réussi (nouvelle ou ancienne)
    if gauth.access_token_expired:
        gauth.Refresh() # Rafraîchit le jeton si nécessaire

    # 5. Sauvegarde les identifiants (token.json) pour la prochaine fois
    gauth.SaveCredentialsFile("token.json")
    
    return GoogleDrive(gauth)

def find_or_create_folder(drive, folder_name):
    """Trouve un dossier existant ou le crée s'il n'existe pas"""
    file_list = drive.ListFile({
        'q': f"title='{folder_name}' and trashed=false",
        'maxResults': 10
    }).GetList()

    if file_list:
        print(f"Dossier trouvé : '{folder_name}' ({file_list[0]['id']})")
        return file_list[0]['id']
    else:
        # Création du dossier
        folder_metadata = {
            'title': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        print(f"Dossier créé : '{folder_name}' ({folder['id']})")
        return folder['id']

def run_backup():
    # 1. Préparation du nom et de l'archive
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"intranet_backup_{timestamp}.zip"

    print(f"Création de l'archive locale : {archive_name}...")
    try:
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Ajout des fichiers/dossiers configurés
            for path in FILES_TO_BACKUP:
                if os.path.isdir(path):
                    # Ajout récursif du dossier media/
                    for root, _, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # archive le chemin relatif pour la structure du zip
                            zipf.write(file_path, os.path.relpath(file_path))
                elif os.path.exists(path):
                    # Ajout du fichier db.sqlite3
                    zipf.write(path)
                else:
                    print(f"Attention : Chemin non trouvé : {path}")
        print("Archive locale créée avec succès.")

        # 2. Authentification et upload
        drive = authenticate_drive()
        drive_folder_id = find_or_create_folder(drive, DRIVE_FOLDER_NAME)

        print(f"Téléversement de {archive_name} vers Google Drive...")
        
        # Création et téléversement du fichier
        file_drive = drive.CreateFile({
            'title': archive_name,
            'parents': [{'id': drive_folder_id}]
        })
        file_drive.SetContentFile(archive_name)
        file_drive.Upload()
        print("Téléversement terminé avec succès !")

    except Exception as e:
        print(f"ERREUR LORS DE LA SAUVEGARDE : {e}")

    finally:
        # 3. Nettoyage
        if os.path.exists(archive_name):
            os.remove(archive_name)
            print(f"Nettoyage : Archive locale '{archive_name}' supprimée.")

if __name__ == "__main__":
    # Change le répertoire de travail pour s'assurer que db.sqlite3 et media/ sont trouvés
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Django utilise les mêmes settings, mais le script est à la racine, donc on monte d'un niveau
    # si le script est dans un sous-dossier, sinon on reste là.
    # Puisque le projet est à la racine de intranet_international, on reste là.
    
    run_backup()