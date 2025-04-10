import json
import streamlit as st

def normalize_nft_number(nft_number):
    """Normalise le format du numéro de NFT"""
    return f"nft_{nft_number}"

def find_trait_rarity(category, trait_name, data):
    """
    Trouve ou génère les informations de rareté pour un trait
    """
    # Ignorer les traits vides
    if not trait_name or trait_name.lower() == "empty":
        return None
    
    # Normaliser le nom de la catégorie
    category_upper = category.upper()
    
    # Liste des catégories possibles à vérifier
    possible_categories = [
        category_upper,
        category.upper().replace(" ", "_"),
        category.split(" ")[0].upper(),
        category_upper.replace("_", "")
    ]
    
    # Mappings de catégories courantes
    category_mappings = {
        "BACKGROUND": ["BG", "BACKDROP", "BACK"],
        "FUR": ["COLOR", "SKIN", "BASE"],
        "SHIRT": ["CLOTHES", "CLOTHING", "TOP", "OUTFIT"],
        "BODY": ["SKIN", "TORSO", "CHEST"],
        "EYES": ["EYE", "EYEWEAR", "VISION"],
        "CHEEK": ["FACE", "CHEEKS", "MARKING"],
        "HAT": ["HEAD", "HEADWEAR", "HELMET", "HAIR"],
        "POCKET": ["ITEM", "ACCESSORY_2", "SIDE_ITEM"],
        "ACCESSORY": ["ACC", "PROP", "ACCESSORY_1", "WEAR"]
    }
    
    # Tenter de trouver la bonne catégorie
    matched_category = None
    for possible_cat in possible_categories:
        if possible_cat in data:
            matched_category = possible_cat
            break
    
    if not matched_category:
        # Essayer les mappings
        for catalog_cat, aliases in category_mappings.items():
            if category_upper in aliases and catalog_cat in data:
                matched_category = catalog_cat
                break
    
    # Si une catégorie est trouvée, chercher le trait
    if matched_category:
        cat_traits = data[matched_category]
        
        # Essayer diverses méthodes de correspondance
        normalized_trait = trait_name.lower().replace(" ", "").replace("_", "").replace("-", "")
        
        for trait in cat_traits:
            # Correspondance exacte
            if trait["trait"].lower() == trait_name.lower():
                return trait
            
            # Correspondance normalisée
            normalized_catalog = trait["trait"].lower().replace(" ", "").replace("_", "").replace("-", "")
            if normalized_trait == normalized_catalog:
                return trait
            
            # Correspondance partielle
            if normalized_trait in normalized_catalog or normalized_catalog in normalized_trait:
                return trait
    
    # Si aucune correspondance n'est trouvée, générer une estimation de rareté
    # Baser la rareté sur la longueur du nom (juste comme heuristique simple)
    trait_length = len(trait_name)
    estimated_rarity = max(5.0, min(25.0, 30.0 - trait_length))
    
    # Déterminer le tier en fonction de la rareté estimée
    tier = "common"
    if estimated_rarity < 3.0:
        tier = "legendary"
    elif estimated_rarity < 5.0:
        tier = "epic"
    elif estimated_rarity < 10.0:
        tier = "rare"
    elif estimated_rarity < 15.0:
        tier = "uncommon"
    
    # Retourner un trait généré
    return {
        "trait": trait_name,
        "rarity": estimated_rarity,
        "tier": tier,
        "generated": True  # Indicateur que ce trait a été généré
    }

def calculate_nft_rarity_score(nft_traits, rarity_data):
    """
    Calcule le score de rareté pour un NFT en utilisant notre formule avancée
    """
    selected_traits = {}
    total_rarity = 0
    trait_count = 0
    legendary_count = 0
    unique_count = 0
    rarity_values = []
    
    # Pour chaque trait du NFT
    for category, trait_name in nft_traits.items():
        if trait_name.lower() == "empty":
            continue
        
        # Trouver les données de rareté pour ce trait
        trait_info = find_trait_rarity(category, trait_name, rarity_data)
        
        if trait_info:
            selected_traits[category.upper()] = trait_info
            total_rarity += trait_info["rarity"]
            trait_count += 1
            
            # Compter les traits légendaires et uniques
            if trait_info.get("count", 0) == 1:
                unique_count += 1
            if trait_info["tier"] == "legendary":
                legendary_count += 1
            
            # Inverser la rareté
            rarity_pct = trait_info["rarity"]
            inverse_rarity = 100.0 / max(0.1, rarity_pct)
            rarity_values.append(inverse_rarity)
    
    # Si aucun trait n'a été trouvé, retourner une valeur par défaut
    if not rarity_values:
        return 20.0, "common", selected_traits
    
    # Calculer le score
    avg_inverse_rarity = sum(rarity_values) / len(rarity_values)
    unique_bonus = unique_count * 20.0
    legendary_bonus = legendary_count * 10.0
    
    final_score = avg_inverse_rarity + unique_bonus + legendary_bonus
    final_rarity_pct = 100.0 / max(1.0, final_score / 5.0)
    final_rarity_pct = max(0.1, min(25.0, final_rarity_pct))
    
    # Déterminer le niveau
    if unique_count >= 3 or legendary_count >= 4:
        tier = "legendary"
    elif unique_count >= 2 or legendary_count >= 3 or final_rarity_pct < 3.0:
        tier = "epic"
    elif unique_count >= 1 or legendary_count >= 2 or final_rarity_pct < 7.0:
        tier = "rare"
    elif legendary_count >= 1 or final_rarity_pct < 12.0:
        tier = "uncommon"
    else:
        tier = "common"
    
    return final_rarity_pct, tier, selected_traits

def calculate_real_rarity():
    """
    Calcule la rareté réelle de chaque trait en fonction de sa fréquence d'apparition
    dans toute la collection de NFTs
    """
    # Charger tous les NFTs
    with open("nfts_metadata.json", "r") as f:
        all_nfts = json.load(f)
    
    # Nombre total de NFTs dans la collection
    total_nfts = len(all_nfts)
    
    # Dictionnaire pour compter les occurrences de chaque trait par catégorie
    trait_counts = {}
    
    # Parcourir tous les NFTs et compter les traits
    for nft_id, traits in all_nfts.items():
        for category, trait_value in traits.items():
            if trait_value.lower() == "empty":
                continue
                
            if category not in trait_counts:
                trait_counts[category] = {}
            
            if trait_value not in trait_counts[category]:
                trait_counts[category][trait_value] = 0
            
            trait_counts[category][trait_value] += 1
    
    # Convertir les comptages en pourcentages de rareté et assigner des niveaux
    rarity_catalog = {}
    
    for category, traits in trait_counts.items():
        rarity_catalog[category.upper()] = []
        
        for trait_name, count in traits.items():
            # Calculer le pourcentage d'apparition
            percentage = (count / total_nfts) * 100
            
            # Déterminer le niveau de rareté
            tier = "common"
            
            # Traitement spécial pour les traits qui n'apparaissent qu'une seule fois
            if count == 1:
                tier = "legendary"  # Garantir que les traits uniques sont toujours légendaires
            elif percentage < 1.0:
                tier = "legendary"
            elif percentage < 3.0:
                tier = "epic"
            elif percentage < 7.0:
                tier = "rare"
            elif percentage < 15.0:
                tier = "uncommon"
            
            # Ajouter à notre catalogue avec la rareté réelle
            rarity_catalog[category.upper()].append({
                "trait": trait_name,
                "rarity": percentage,
                "tier": tier,
                "count": count
            })
    
    return rarity_catalog

def find_legendary_nfts(limit=50, rarity_data=None):
    """
    Analyse tous les NFTs et trouve les plus rares
    """
    # Charger les NFTs et les données de rareté
    with open("nfts_metadata.json", "r") as f:
        all_nfts = json.load(f)
    
    # Utiliser les données de rareté passées en paramètre
    if rarity_data is None:
        # Utiliser calculate_real_rarity comme solution de secours
        rarity_data = calculate_real_rarity()
    
    # Calculer le score pour chaque NFT
    nft_scores = []
    
    # Limiter le nombre de NFTs analysés pour des raisons de performance
    nft_count = 0
    for nft_id, traits in all_nfts.items():
        # Extraire le numéro du NFT depuis l'ID
        nft_number = nft_id.replace("nft_", "").strip()
        
        # Calculer le score
        score, tier, selected_traits = calculate_nft_rarity_score(traits, rarity_data)
        
        # Compter les traits uniques/légendaires pour affichage
        unique_count = sum(1 for t in selected_traits.values() if t.get("count", 0) == 1)
        legendary_count = sum(1 for t in selected_traits.values() if t["tier"] == "legendary")
        rare_count = sum(1 for t in selected_traits.values() if t["tier"] == "rare")
        
        nft_scores.append({
            "id": nft_id,
            "number": nft_number,
            "score": score,
            "tier": tier,
            "traits": traits,
            "selected_traits": selected_traits,
            "unique_count": unique_count,
            "legendary_count": legendary_count,
            "rare_count": rare_count
        })
        
        nft_count += 1
        if nft_count >= 1000:  # Limiter pour la première version
            break
    
    # Trier par score (du plus rare au moins rare)
    nft_scores.sort(key=lambda x: x["score"])
    
    # Retourner les top NFTs (pas de tuple)
    return nft_scores[:limit]
