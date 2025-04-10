import json
import streamlit as st
from config import TOTAL_MINTED_NFTS

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
    Calcule le score de rareté pour un NFT de façon simple et transparente
    """
    # Initialisation des compteurs
    selected_traits = {}
    total_rarity_score = 0
    trait_count = 0
    
    # Pour chaque trait du NFT
    for category, trait_name in nft_traits.items():
        # Ignorer les traits empty
        if trait_name.lower() == "empty":
            continue
        
        # Trouver les données de rareté pour ce trait
        category_upper = category.upper()
        if rarity_data and category_upper in rarity_data:
            for trait_info in rarity_data[category_upper]:
                if trait_info["trait"].lower() == trait_name.lower():
                    # Ajouter aux traits sélectionnés
                    selected_traits[category_upper] = trait_info
                    
                    # Ajouter à la rareté totale (plus petit = plus rare)
                    total_rarity_score += trait_info["rarity"]
                    trait_count += 1
                    break
    
    # Si aucun trait n'a été trouvé, retourner une valeur par défaut
    if trait_count == 0:
        return 100.0, "common", {}
    
    # Calculer la rareté moyenne (plus petit = plus rare)
    avg_rarity = total_rarity_score / trait_count
    
    # Déterminer le niveau avec des seuils optimisés pour une distribution naturelle
    if avg_rarity < 0.5:
        tier = "unique"
    elif avg_rarity < 1.5:
        tier = "legendary"
    elif avg_rarity < 5.0:
        tier = "epic"
    elif avg_rarity < 8.0:
        tier = "rare"
    elif avg_rarity < 18.0:
        tier = "uncommon"
    else:
        tier = "common"
    
    return avg_rarity, tier, selected_traits

def calculate_real_rarity():
    """
    Calcule la rareté réelle de chaque trait en fonction de sa fréquence d'apparition
    dans la collection de NFTs réellement mintés
    """
    # Charger tous les NFTs
    with open("nfts_metadata.json", "r") as f:
        all_nfts = json.load(f)
    
    # Filtrer pour ne garder que les NFTs mintés (les premiers selon TOTAL_MINTED_NFTS)
    minted_nfts = {}
    for nft_id, traits in all_nfts.items():
        # Extraire le numéro du NFT
        nft_number = int(nft_id.replace("nft_", ""))
        if nft_number <= TOTAL_MINTED_NFTS:
            minted_nfts[nft_id] = traits
    
    # Dictionnaire pour compter les occurrences de chaque trait par catégorie
    trait_counts = {}
    
    # Parcourir seulement les NFTs mintés et compter les traits
    for nft_id, traits in minted_nfts.items():
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
            percentage = (count / TOTAL_MINTED_NFTS) * 100
            
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

def find_legendary_nfts(limit=1575, rarity_data=None):
    """
    Trouve tous les NFTs mintés et assigne des niveaux de rareté par percentiles
    pour obtenir une distribution précise
    """
    # Charger les données NFT
    with open("nfts_metadata.json", "r") as f:
        all_nfts = json.load(f)
    
    # Résultats
    all_nfts_with_rarity = []
    
    # Calculer la rareté initiale pour tous les NFTs mintés
    for nft_id, traits in all_nfts.items():
        nft_number = int(nft_id.replace("nft_", ""))
        
        # Ne traiter que les NFTs mintés
        if nft_number <= TOTAL_MINTED_NFTS:
            avg_rarity, _, selected_traits = calculate_nft_rarity_score(traits, rarity_data)
            
            # Calculer les compteurs pour la compatibilité
            unique_count = sum(1 for t in selected_traits.values() if t.get("count", 0) == 1)
            legendary_count = sum(1 for t in selected_traits.values() if t.get("tier") == "legendary")
            
            all_nfts_with_rarity.append({
                "number": nft_number,
                "score": avg_rarity,
                "selected_traits": selected_traits,
                "unique_count": unique_count,
                "legendary_count": legendary_count
            })
    
    # Trier par rareté (score le plus bas = plus rare)
    all_nfts_with_rarity.sort(key=lambda x: x["score"])
    
    # Distribution exacte par percentiles
    total_nfts = len(all_nfts_with_rarity)
    unique_count = int(total_nfts * 0.005)  # 0.5%
    legendary_count = int(total_nfts * 0.015)  # 1.5%
    epic_count = int(total_nfts * 0.03)  # 3%
    rare_count = int(total_nfts * 0.10)  # 10%
    uncommon_count = int(total_nfts * 0.35)  # 35%
    
    # Assigner les tiers en fonction des comptages exacts
    for i, nft in enumerate(all_nfts_with_rarity):
        if i < unique_count:
            nft["tier"] = "unique"
        elif i < unique_count + legendary_count:
            nft["tier"] = "legendary"
        elif i < unique_count + legendary_count + epic_count:
            nft["tier"] = "epic"
        elif i < unique_count + legendary_count + epic_count + rare_count:
            nft["tier"] = "rare"
        elif i < unique_count + legendary_count + epic_count + rare_count + uncommon_count:
            nft["tier"] = "uncommon"
        else:
            nft["tier"] = "common"
    
    return all_nfts_with_rarity[:limit]
