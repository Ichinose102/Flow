## 💡 Le Concept : Pourquoi c'est spécial ?

Normalement, un **Arduino Uno** ne peut pas contrôler un ordinateur directement (il n'est pas reconnu comme un clavier ou une souris HID). Pour faire du contrôle multimédia, la plupart des gens achètent un Arduino Leonardo.

**Ma solution :**
J'ai contourné cette limitation technique en créant un script "Bridge" en Python. 
- **L'Arduino** s'occupe de la partie "Hardware" avec les composants qui vont avec (lecture des capteurs, RFID, IR).
- **Python** s'occupe de la partie "Intelligence" (interprétation des codes et exécution des commandes système sur Windows).

Cela permet de transformer n'importe quel Arduino basique en un centre de contrôle ultra-puissant.