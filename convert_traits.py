import json
import re
import os

def convert_traits_to_json(input_file, output_file):
    """
    Convertit le fichier d'analyse de traits au format spécifique en JSON.
    """
    print(f"Lecture du fichier : {input_file}")
    
    # Vérifier si le fichier existe
    if not os.path.exists(input_file):
        print(f"ERREUR : Le fichier {input_file} n'existe pas.")
        return {}
    
    # Initialiser le dictionnaire pour stocker les données
    traits_data = {}
    current_category = None
    current_tier = None
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"Fichier lu avec succès. {len(lines)} lignes")
        
        # Parcourir les lignes avec un index
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Ignorer les lignes vides ou lignes de séparation
            if not line or line == "=============================":
                i += 1
                continue
            
            # Vérifier si c'est une ligne de titre (ANALYSE DES TRAITS...)
            if "ANALYSE DES TRAITS" in line:
                i += 1
                continue
            
            # Vérifier si c'est une catégorie principale (tout en majuscules)
            if line.isupper() and line not in ["LÉGENDAIRE", "ÉPIQUE", "RARE", "COMMUN"]:
                current_category = line
                traits_data[current_category] = []
                print(f"Catégorie trouvée : {current_category}")
                i += 1
                continue
            
            # Vérifier si c'est un niveau de rareté
            if line in ["LÉGENDAIRE", "ÉPIQUE", "RARE", "COMMUN"] or line.startswith('---') or line.startswith('==='):
                if line in ["LÉGENDAIRE", "ÉPIQUE", "RARE", "COMMUN"]:
                    current_tier = line.lower()
                    # Convertir en anglais pour compatibilité
                    if current_tier == "légendaire":
                        current_tier = "legendary"
                    elif current_tier == "épique":
                        current_tier = "epic"
                    elif current_tier == "rare":
                        current_tier = "rare"
                    elif current_tier == "commun":
                        current_tier = "common"
                i += 1
                continue
            
            # Vérifier s'il s'agit d'une ligne de trait (commençant par •)
            if line.startswith("•") and current_category and current_tier:
                # Extraire le nom du trait
                trait_match = re.match(r"• (.+)", line)
                if trait_match:
                    trait_name = trait_match.group(1).strip()
                    
                    # Passer à la ligne suivante pour la rareté
                    i += 1
                    if i < len(lines):
                        rarity_line = lines[i].strip()
                        rarity_match = re.search(r"Rareté: ([\d.,]+)%", rarity_line)
                        
                        if rarity_match:
                            rarity_str = rarity_match.group(1).replace(',', '.')
                            try:
                                rarity = float(rarity_str)
                                
                                traits_data[current_category].append({
                                    "trait": trait_name,
                                    "rarity": rarity,
                                    "tier": current_tier
                                })
                                
                                print(f"  Ajouté : {trait_name} ({rarity}%, {current_tier})")
                            except ValueError:
                                print(f"  ERREUR: Impossible de convertir '{rarity_str}' en nombre")
            
            # Passer à la ligne suivante
            i += 1
        
        # Vérifier si des données ont été extraites
        total_traits = sum(len(traits) for traits in traits_data.values())
        if total_traits == 0:
            print("AVERTISSEMENT : Aucun trait n'a été extrait du fichier.")
            return {}
        
        # Écrire les données dans le fichier JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(traits_data, f, indent=2, ensure_ascii=False)
        
        print(f"Données écrites avec succès dans {output_file}")
        print(f"Total : {len(traits_data)} catégories, {total_traits} traits")
        return traits_data
    
    except Exception as e:
        print(f"ERREUR lors de la conversion : {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    input_file = 'analyse_traits (1).txt'
    output_file = 'nft_traits_rarity.json'
    
    print(f"Démarrage de la conversion de {input_file} vers {output_file}")
    traits_data = convert_traits_to_json(input_file, output_file)
