# 🌀 FLOW — Dashboard & Control Center

**FLOW** est un système de contrôle intelligent combinant un prototype **Arduino Uno** et une interface **Python custom**. 

Ce projet permet de transformer un simple Arduino Uno (qui ne possède pas de puce native USB HID) en un puissant contrôleur multimédia et de sécurité pour PC via une communication série optimisée.

---

## 🚀 Pourquoi FLOW ?
De base, l'Arduino Uno ne peut pas simuler nativement un clavier ou une souris (HID). Au lieu de flasher le firmware (Atmega16U2) ou de changer de carte, j'ai développé une **passerelle Python** qui :

* **Écoute** les signaux de l'Arduino en temps réel via le port série.
* **Interprète** les codes Infrarouge (IR) et les tags RFID.
* **Exécute** des actions système complexes (Verrouillage, Arrêt, Raccourcis).
* **Affiche** un Dashboard moderne avec monitoring CPU/RAM et données capteurs.

---

## 🛠️ Fonctionnalités

### 🖥️ Dashboard (Interface Python)
* **Monitoring Temps Réel :** Affichage de la charge CPU et de l'utilisation RAM.
* **Capteurs :** Température et Humidité récupérées en direct du capteur DHT11.
* **Analytics :** Graphique d'historique des températures (via le bouton dédié).
* **Design Apple-Style :** Interface sombre, épurée avec des bordures arrondies.

### 🎮 Contrôle Télécommande (IR)
* **Arrêt PC :** Extinction propre du système via le bouton dédié.
* **Multimédia :** Gestion du Volume (+/-), Play/Pause, Suivant/Précédent.
* **Raccourcis Apps :** Lancement rapide de **Spotify** et **Notion**.
* **Analytics :** Ouverture instantanée du pop-up graphique.

### 🔐 Sécurité (RFID)
* **Lock Mode :** Verrouillage instantané de la session Windows au passage de ton badge ou de ta carte RFID.

---

## 📦 Installation

### 1. Matériel requis
* Arduino Uno + Shield de prototypage
* Module RFID RC522
* Récepteur Infrarouge (connecté sur la **Broche 4**)
* Capteur de température/humidité DHT11
* Buzzer (pour les retours sonores)

### 2. Logiciel (Python)
Installe les dépendances nécessaires avec la commande suivante :
```bash
pip install pyserial pyautogui psutil matplotlib 