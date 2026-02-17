import subprocess
import json
import os
import time

def run_command(command, stop_on_error=True):
    if isinstance(command, str):
        print(f"Exécution : {command}")
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
    else:
        print(f"Exécution : {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"ERREUR lors de l'exécution : {result.stderr or result.stdout}")
        if stop_on_error:
            print("Arrêt du script en raison d'une erreur critique.")
            exit(1)
    return result.stdout

def check_cluster_connection():
    print("Vérification de la connexion au cluster Kubernetes...")
    result = subprocess.run(["kubectl", "cluster-info"], capture_output=True, text=True)
    if result.returncode != 0:
        print("\n" + "!"*60)
        print("ERREUR : Impossible de contacter le cluster Kubernetes.")
        print("Assurez-vous que votre cluster KIND est démarré (kind export kubeconfig).")
        print("Vérifiez également que kubectl est correctement configuré.")
        print("!"*60 + "\n")
        return False
    return True

def main():
    # S'assurer que le script s'exécute dans son propre répertoire
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 1. Charger la configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Erreur : config.json non trouvé.")
        return

    formateur_ip = config.get('formateur_ip')
    formateur_port = config.get('formateur_port')
    stagiaire_nom = config.get('stagiaire_nom')
    namespace = "mon-application"

    print(f"Démarrage du Lab pour {stagiaire_nom}...")

    # 2. Vérifier la connexion au cluster
    if not check_cluster_connection():
        return

    # 3. Créer le namespace si nécessaire
    run_command(f"kubectl create namespace {namespace} --dry-run=client -o yaml | kubectl apply -f -")

    # 4. Premier déploiement Helm pour initialiser
    print("Déploiement initial de l'application via HELM...")
    run_command(["helm", "upgrade", "--install", "mon-app", "./app-chart", "-n", namespace, "--set", f"namespace={namespace}"])

    # Attendre un peu que les ressources soient créées
    print("Attente de la création des ressources...")
    time.sleep(5)

    # 5. Récupérer les infos kubectl
    print("Récupération des informations du cluster...")
    pods_info = run_command(["kubectl", "get", "pods", "-n", namespace], stop_on_error=False)
    svc_info = run_command(["kubectl", "get", "svc", "-n", namespace], stop_on_error=False)

    logs_kubectl = f"--- PODS ---\n{pods_info}\n--- SERVICES ---\n{svc_info}"

    # 5. Générer le HTML final
    # On échappe les données pour le JS
    logs_js = json.dumps(logs_kubectl)
    stagiaire_js = json.dumps(stagiaire_nom)

    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Validation Lab Kubernetes</title>
    <style>
        body {{ font-family: sans-serif; text-align: center; padding: 50px; background-color: #f4f4f9; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: inline-block; }}
        pre {{ text-align: left; background: #272822; color: white; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        button {{ background-color: #4CAF50; color: white; padding: 15px 32px; font-size: 16px; border: none; border-radius: 4px; cursor: pointer; }}
        button:hover {{ background-color: #45a049; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Lab 01 - Déploiement NGINX Terminé</h1>
        <p>Stagiaire : <strong>{stagiaire_nom}</strong></p>
        <h3>Récapitulatif de votre déploiement :</h3>
        <pre>{logs_kubectl}</pre>
        <br>
        <button onclick="valider()">VALIDER ET ENVOYER AU FORMATEUR</button>
    </div>

    <script>
        function valider() {{
            const data = {{
                stagiaire: {stagiaire_js},
                logs: {logs_js}
            }};
            fetch("http://{formateur_ip}:{formateur_port}", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify(data)
            }})
            .then(response => {{
                if (response.ok) {{
                    alert("Succès ! Vos résultats ont été envoyés au formateur.");
                }} else {{
                    alert("Erreur lors de l'envoi. Vérifiez la connexion au serveur du formateur.");
                }}
            }})
            .catch(error => {{
                console.error("Erreur:", error);
                alert("Erreur réseau : " + error);
            }});
        }}
    </script>
</body>
</html>
"""

    # 7. Mettre à jour Helm avec le nouveau contenu HTML
    print("Mise à jour de la page web avec les données du cluster...")
    # On utilise --set-file ou on passe la string via --set.
    # Pour éviter les problèmes de caractères spéciaux dans le HTML via CLI, on va créer un fichier temporaire
    with open('index.html.tmp', 'w') as f:
        f.write(html_content)

    run_command(["helm", "upgrade", "--install", "mon-app", "./app-chart", "-n", namespace,
                 "--set", f"namespace={namespace}",
                 "--set-file", "indexHtml=index.html.tmp"])

    os.remove('index.html.tmp')

    print("\n" + "="*60)
    print("DÉPLOIEMENT RÉUSSI !")
    print("Pour accéder à votre application, exécutez la commande suivante :")
    print(f"kubectl port-forward svc/nginx-service 8081:80 -n {namespace}")
    print("\nEnsuite, ouvrez votre navigateur sur : http://localhost:8081")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
