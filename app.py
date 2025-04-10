import streamlit as st
import json
import pandas as pd
import random
import re
import zipfile
import tempfile
import os
import shutil
import plotly.graph_objects as go

# Celle-ci doit être la première commande Streamlit
st.set_page_config(
    page_title="NFT Rarity Checker",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ajoutez ce code après st.set_page_config
st.markdown("""
<style>
body {
    background-color: #121212 !important;
    color: white !important;
}
.stApp {
    background-color: #121212 !important;
}
.main {
    background-color: #121212 !important;
}
header {
    background-color: #121212 !important;
}
.block-container {
    background-color: #121212 !important;
}
footer {
    background-color: #121212 !important;
}

/* Style pour masquer le bandeau Streamlit en haut */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}

/* Pour les widgets */
div.stSelectbox > div[data-baseweb="select"] > div {
    background-color: #2a2a2a !important;
    color: white !important;
}

/* Amélioration pour la section Traits Summary */
h3, h4 {
    color: #4CAF50 !important;
    font-size: 1.5rem !important;
    font-weight: bold !important;
    margin-top: 20px !important;
    margin-bottom: 15px !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.5) !important;
}

/* Style pour la zone de texte du résumé */
.stMarkdown p {
    color: white !important;
    font-size: 1.1rem !important;
    background-color: rgba(42, 42, 42, 0.7) !important;
    padding: 10px 15px !important;
    border-radius: 8px !important;
    border-left: 3px solid #4CAF50 !important;
    margin: 10px 0 !important;
}

/* Mettre en évidence les informations importantes */
.stMarkdown strong {
    color: #8bc34a !important;
    font-weight: bold !important;
}

/* Style pour les informations numériques */
.stMarkdown p:contains("Average rarity") {
    font-size: 1.2rem !important;
    background-color: rgba(76, 175, 80, 0.2) !important;
    border: 1px solid rgba(76, 175, 80, 0.5) !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
}
</style>
""", unsafe_allow_html=True)

# Ensuite seulement, importez utils
from utils import (
    normalize_nft_number,
    find_trait_rarity,
    calculate_nft_rarity_score,
    calculate_real_rarity,
    find_legendary_nfts
)

# Page configuration
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Mappings directs pour les traits et catégories
CATEGORY_MAP = {
    "background": "BACKGROUND",
    "fur": "FUR",
    "shirt": "SHIRT",
    "body": "BODY",
    "eyes": "EYES",
    "cheek": "CHEEK",
    "hat": "HAT",
    "pocket": "POCKET",
    "accessory": "ACCESSORY"
}

# Mappings pour les valeurs de traits
TRAIT_MAP = {
    # Mappings pour BACKGROUND
    "space": "space",
    "codex": "codex",
    "pastel_green": "pastel_green",
    "pastel_blue": "pastel_blue",
    "blue_sky": "blue_sky",
    "midnight_blue": "midnight_blue",
    "america": "america",
    "lavender": "lavender",
    "code_rain": "code_rain",
    "money": "money",
    "vortex": "vortex",
    "eggplant": "eggplant",
    "iceberg": "iceberg",
    "grey_background": "grey_background",
    
    # Mappings pour FUR
    "shiny_dark_brown": "dark_brown",
    "dark_brown": "dark_brown",
    "dark_brown_fur": "dark_brown",
    "sky_blue_fur": "sky_blue",
    "shiny_sky_blue": "sky_blue",
    "white_fur": "White_FUR",
    "White_FUR": "White_FUR",
    "pink": "Pink_Fur",
    "Pink_Fur": "Pink_Fur",
    "light_grey": "light_grey",
    "dark_grey_fur": "dark_grey",
    "shiny_dark_grey": "dark_grey",
    "rainbow_fur": "rainbow",
    "light_brown": "light_brown",
    "orange": "orange",
    "shiny_orange": "orange",
    "dark_yellow_fur": "yellow",
    "shiny_apple_green": "APPLE_GREEN_FUR",
    "APPLE_GREEN_FUR": "APPLE_GREEN_FUR",
    "apple_green_fur": "APPLE_GREEN_FUR",
    "lavender": "lavender",
    
    # Mappings pour SHIRT
    "yellow_zip_jacket": "yellow_zip_jacket",
    "black-tunique": "black-tunique",
    "orange_zip_jacket": "orange_zip_jacket",
    "purple_sweat": "purple_sweat",
    "red_jacket": "red_jacket",
    "ninja_jacket": "ninja_jacket",
    "chef_jacket": "chef_jacket",
    "peasan": "peasan",
    "white_kimono": "white_kimono",
    "purple_tracksuit": "purple_tracksuit",
    "pink_hoodie": "pink_hoodie",
    "white_sweat": "white_sweat",
    "jail": "jail",
    "simple_black_jacket": "simple_black_jacket",
    "mysteri_shirt": "mysteri_shirt",
    "knight_shirt": "knight_shirt",
    "red_tunique": "red_tunique",
    "superhero_tunic": "superhero_tunic",
    "artic_camo": "artic_camo",
    "Black_shirt": "Black_shirt",
    "casual_blue_shirt": "casual_blue_shirt",
    
    # Mappings pour ACCESSORY
    "beer": "beer",
    "microphone": "microphone",
    "baseball_bat": "baseball_bat",
    "balloon": "balloon",
    "fly": "fly",
    "soda": "soda",
    "gold_nose": "gold_nose",
    "ruler": "ruler",
    "rain": "rain",
    "smiling_sloth": "smiling_sloth",
    "photo": "photo",
    
    # Mappings pour les autres catégories...
    # (Ajouter les autres mappings selon vos besoins)
    
    # Valeur par défaut pour les traits "empty"
    "empty": "empty"
}

# Fonction pour normaliser le nom de catégorie
def normalize_category_name(category):
    # Convertir en minuscules et supprimer les espaces
    category = category.lower().strip()
    # Utiliser le mappage des catégories
    return CATEGORY_MAP.get(category, category.upper())

# Fonction pour normaliser le nom de trait
def normalize_trait_name(trait, category):
    # Convertir en minuscules
    trait = trait.lower().strip()
    # Utiliser le mappage des traits
    return TRAIT_MAP.get(trait, trait)

# Remplacer la fonction load_data() par celle-ci
@st.cache_data
def load_data():
    # D'abord, essayer de charger les données de rareté calculées au préalable
    try:
        with open("calculated_rarity.json", "r") as f:
            return json.load(f)
    except:
        # Si le fichier n'existe pas, calculer la rareté et l'enregistrer
        rarity_catalog = calculate_real_rarity()
        
        try:
            with open("calculated_rarity.json", "w") as f:
                json.dump(rarity_catalog, f, indent=2)
        except:
            pass  # Ignorer les erreurs d'écriture
        
        return rarity_catalog

# Fonction pour charger les données des NFTs
@st.cache_data
def load_nft_data():
    try:
        with open("nfts_metadata.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        # Si le fichier n'existe pas, retourner un dictionnaire vide
        return {}

# Charger les données
data = load_data()
nft_data = load_nft_data()

# En-tête avec logo amélioré
st.markdown('<div class="app-header">', unsafe_allow_html=True)
col_logo, col_title = st.columns([1, 4])

# Affichage du logo avec une taille plus appropriée
with col_logo:
    try:
        st.image("static/logo.png", width=120)
    except:
        try:
            st.image("logo.png", width=120)
        except:
            st.write("🧬")  # Emoji de remplacement si le logo n'est pas trouvé

# Titre principal après le logo
with col_title:
    st.markdown('<h1 class="app-title">NFT Traits Rarity Checker</h1>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Créez les onglets (supprimez le titre qui existe déjà)
tabs = st.tabs(["Check Rarity", "Explore Traits", "Legendary NFTs", "About"])

with tabs[0]:
    # Rarity checker
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.header("Check your traits combination rarity")
    
    # Initialiser les variables de rareté
    selected_traits = {}
    total_rarity = 0
    trait_count = 0
    
    # Options de saisie en anglais
    input_method = st.radio("Choose input method:", ["Enter NFT Number", "Select Traits Manually"], horizontal=True)
    
    # Créer deux colonnes pour la mise en page
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if input_method == "Enter NFT Number":
            st.subheader("Enter your NFT number")
            input_nft = st.text_input("Enter your NFT number")
            
            # Bouton de recherche et traitement
            if input_nft:
                # Normaliser le numéro de NFT
                normalized_nft_number = normalize_nft_number(input_nft)
                
                # Vérifier l'existence du NFT
                if normalized_nft_number in nft_data or input_nft in nft_data:
                    nft_key = normalized_nft_number if normalized_nft_number in nft_data else input_nft
                    st.success(f"NFT #{input_nft} found!")
                    
                    # Récupérer les traits
                    nft_traits = nft_data[nft_key]
                    
                    # Afficher les traits bruts
                    st.write("Traits found in this NFT:", nft_traits)
                    
                    # Traiter chaque trait
                    traits_with_rarity = 0
                    for category, trait_name in nft_traits.items():
                        if trait_name.lower() == "empty":
                            continue
                        
                        # Trouver ou générer la rareté du trait
                        trait_info = find_trait_rarity(category, trait_name, data)
                        
                        if trait_info:
                            # Ajouter aux traits sélectionnés
                            selected_traits[category.upper()] = trait_info
                            total_rarity += trait_info["rarity"]
                            trait_count += 1
                            traits_with_rarity += 1
                            
                            # Marquer si le trait a été généré
                            if trait_info.get("generated"):
                                st.info(f"Rarity for '{trait_name}' in '{category}' was estimated (no exact match found)")
                    
                    # Si aucun trait n'a été trouvé, afficher un message
                    if traits_with_rarity == 0:
                        st.warning("No traits with rarity data found for this NFT")
                        st.info("Using default rarity values for visualization purposes")
                        
                        # Générer des valeurs de rareté pour tous les traits
                        for category, trait_name in nft_traits.items():
                            if trait_name.lower() == "empty":
                                continue
                            
                            # Générer une rareté aléatoire mais réaliste
                            import random
                            rarity = random.uniform(5.0, 20.0)
                            tier = "common"
                            if rarity < 3.0:
                                tier = "legendary"
                            elif rarity < 5.0:
                                tier = "epic"
                            elif rarity < 10.0:
                                tier = "rare"
                            elif rarity < 15.0:
                                tier = "uncommon"
                            
                            trait_info = {
                                "trait": trait_name,
                                "rarity": rarity,
                                "tier": tier,
                                "generated": True
                            }
                            
                            selected_traits[category.upper()] = trait_info
                            total_rarity += trait_info["rarity"]
                            trait_count += 1
        else:
            # Code de sélection manuelle existant
            st.subheader("Select your traits")
            
            # Create an expandable container for each category
            for category, traits in data.items():
                with st.expander(f"{category} - {len(traits)} traits available"):
                    trait_names = [trait["trait"] for trait in traits]
                    selected = st.selectbox(category, [""] + trait_names, key=category)
                    
                    if selected:
                        selected_trait = next((t for t in traits if t["trait"] == selected), None)
                        if selected_trait:
                            selected_traits[category] = selected_trait
                            total_rarity += selected_trait["rarity"]
                            trait_count += 1
    
    with col2:
        st.subheader("Trait Details")
        
        if selected_traits:
            # Fonction pour déterminer le nombre d'étoiles selon la rareté
            def get_stars(rarity, tier):
                # Nombre d'étoiles basé sur la rareté
                if tier == "legendary":
                    stars = 5
                elif tier == "epic":
                    stars = 4
                elif tier == "rare":
                    stars = 3
                elif tier == "uncommon":
                    stars = 2
                else:  # common
                    stars = 1
                    
                # Ajuster en fonction de la rareté numérique si nécessaire
                if rarity < 1.0 and stars < 5:
                    stars += 1
                elif rarity > 20.0 and stars > 1:
                    stars -= 1
                    
                return stars
            
            # Afficher chaque trait avec ses étoiles
            for category, trait in selected_traits.items():
                tier_color = {
                    "common": "#8bc34a",     # Light green
                    "uncommon": "#4CAF50",   # Medium green
                    "rare": "#2196F3",       # Blue
                    "epic": "#9C27B0",       # Purple
                    "legendary": "#FFD700"   # Gold
                }
                
                color = tier_color.get(trait["tier"], "#8bc34a")
                stars_count = get_stars(trait["rarity"], trait["tier"])
                
                # Créer la chaîne d'étoiles (étoiles pleines suivies d'étoiles vides)
                stars_html = "★" * stars_count + "☆" * (5 - stars_count)
                
                # Informations de fréquence et badge d'unicité
                count_info = f"{trait.get('count', '?')} NFTs" if "count" in trait else ""
                unique_badge = ""
                if trait.get("count", 0) == 1:
                    unique_badge = '<span style="background-color: gold; color: black; padding: 2px 5px; border-radius: 10px; font-size: 10px; margin-left: 5px;">UNIQUE</span>'
                
                # Affichage amélioré
                st.markdown(
                    f"""
                    <div class="trait-card" style="border-left-color: {color}; margin-bottom: 15px; padding: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); background-color: #1e1e1e; border-left: 5px solid {color};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="font-size: 16px; color: white;">{category.upper()}:</strong> 
                                <span style="font-size: 15px; color: #cccccc;">{trait["trait"]} {unique_badge}</span>
                            </div>
                            <span class="rarity-badge" style="background-color: {color}; border-radius: 20px; padding: 3px 8px; font-size: 12px; font-weight: bold; color: black;">
                                {trait["rarity"]:.2f}% - {trait["tier"].capitalize()}
                            </span>
                        </div>
                        <div style="margin-top: 8px; font-size: 20px; color: {color}; letter-spacing: 3px;">
                            {stars_html}
                        </div>
                        <div style="margin-top: 5px; font-size: 12px; color: #999999;">
                            {count_info}
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

            # Ajouter une section résumé
            average_rarity = total_rarity / trait_count if trait_count > 0 else 0
            st.markdown(f"""
            <div style="background-color: #2a2a2a; padding: 15px; border-radius: 10px; border-left: 4px solid #4CAF50; margin: 20px 0;">
                <h3 style="color: #4CAF50; margin-top: 0;">Traits Summary</h3>
                <p style="font-size: 16px; color: white;">Found <strong style="color: #8bc34a;">{trait_count}</strong> traits with rarity data</p>
                <p style="font-size: 18px; color: white; background-color: rgba(76, 175, 80, 0.2); padding: 10px; border-radius: 5px;">
                    Average rarity: <strong style="color: #8bc34a;">{average_rarity:.2f}%</strong> if all traits are considered equal
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            if input_method == "Enter NFT Number" and input_nft:
                st.error("NFT found but no matching rarity data for its traits")
                st.info("This could be due to differences in trait names between your NFT data and rarity data files")
            else:
                st.info("Select traits to see their details here")
        
        # Calcul et affichage du score de rareté global avec un design amélioré
        st.subheader("Overall Rarity Score")
        
        if trait_count > 0:
            # Au lieu d'une simple moyenne, utilisons une formule qui valorise les traits rares
            
            # 1. Calculer la rareté inverse (plus le % est petit, plus la valeur sera grande)
            rarity_values = []
            legendary_count = 0
            unique_count = 0
            
            for category, trait in selected_traits.items():
                rarity_pct = trait["rarity"]
                
                # Compter les traits légendaires et uniques
                if trait.get("count", 0) == 1:
                    unique_count += 1
                if trait["tier"] == "legendary":
                    legendary_count += 1
                
                # Inverser la rareté: plus le % est petit, plus la valeur est grande
                # Formule: 100 / rareté (%)
                inverse_rarity = 100.0 / max(0.1, rarity_pct)  # Éviter division par zéro
                rarity_values.append(inverse_rarity)
            
            # 2. Calculer le score global (moyenne pondérée des raretés inverses)
            if rarity_values:
                avg_inverse_rarity = sum(rarity_values) / len(rarity_values)
                
                # 3. Bonus pour les traits uniques et légendaires
                unique_bonus = unique_count * 20.0  # +20 points par trait unique
                legendary_bonus = legendary_count * 10.0  # +10 points par trait légendaire
                
                # 4. Score final
                final_score = avg_inverse_rarity + unique_bonus + legendary_bonus
                
                # 5. Convertir en pourcentage de rareté (inversé)
                # Plus le score est élevé, plus le % final doit être petit
                final_rarity_pct = 100.0 / max(1.0, final_score / 5.0)
                
                # Limiter le pourcentage entre 0.1% et 25%
                final_rarity_pct = max(0.1, min(25.0, final_rarity_pct))
                
                # 6. Déterminer le niveau global selon le nouveau score
                if unique_count >= 3 or legendary_count >= 4:
                    rarity_tier = "Legendary"
                    rarity_color = "#FFD700"
                    global_stars = 5
                elif unique_count >= 2 or legendary_count >= 3 or final_rarity_pct < 3.0:
                    rarity_tier = "Epic"
                    rarity_color = "#9C27B0"
                    global_stars = 4
                elif unique_count >= 1 or legendary_count >= 2 or final_rarity_pct < 7.0:
                    rarity_tier = "Rare"
                    rarity_color = "#2196F3"
                    global_stars = 3
                elif legendary_count >= 1 or final_rarity_pct < 12.0:
                    rarity_tier = "Uncommon"
                    rarity_color = "#4CAF50"
                    global_stars = 2
                else:
                    rarity_tier = "Common"
                    rarity_color = "#8bc34a"
                    global_stars = 1
            
            # Nombre d'étoiles global
            global_stars_html = "★" * global_stars + "☆" * (5 - global_stars)
            
            # Affichage amélioré du score global
            st.markdown(f'''
            <div style="font-size: 28px; color: {rarity_color}; letter-spacing: 5px; margin: 15px 0; text-align: center;">
                ★★★★★
            </div>
            <div style="font-size: 22px; font-weight: bold; margin: 10px 0; text-align: center;">
                {final_rarity_pct:.2f}%
            </div>
            <div style="background-color: #2a2a2a; height: 20px; border-radius: 10px; margin: 15px 0;">
            <div style="background: linear-gradient(90deg, {rarity_color}, #8bc34a); width: {min(final_rarity_pct * 5, 100)}%; height: 100%; border-radius: 10px;"></div>
            </div>
            <p style="margin-bottom: 0; font-size: 14px; opacity: 0.8; text-align: center;">Based on {trait_count} traits</p>
            ''', unsafe_allow_html=True)

            # Après l'affichage des étoiles, ajoutons une échelle visuelle de rareté
            st.markdown(
                f"""
                <div style="margin-top: 20px; text-align: center;">
                    <p style="margin-bottom: 5px; font-size: 12px;">Échelle de rareté</p>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="font-size: 11px;">Commun<br>15%+</span>
                        <span style="font-size: 11px;">Peu commun<br>8-12%</span>
                        <span style="font-size: 11px;">Rare<br>5-8%</span>
                        <span style="font-size: 11px;">Épique<br>3-5%</span>
                        <span style="font-size: 11px;">Légendaire<br>&lt;3%</span>
                    </div>
                    <div style="height: 15px; background: linear-gradient(90deg, #8bc34a, #4CAF50, #2196F3, #9C27B0, #FFD700); border-radius: 8px; position: relative;">
                        <div style="position: absolute; left: calc({min(max(0, (15 - final_rarity_pct) / 15 * 100), 100)}% - 5px); top: -5px; width: 10px; height: 25px; background-color: white; border-radius: 3px;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("Select at least one trait to calculate rarity score")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    # Explore traits tab content
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.header("Explore all traits by category")
    
    # Sélectionner une catégorie
    categories = list(data.keys())
    selected_category = st.selectbox("Select a category", categories)
    
    if selected_category:
        # Options de filtrage
        st.subheader("Filter options")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Filtrer par niveau de rareté
            rarities = ["legendary", "epic", "rare", "uncommon", "common"]
            rarity_filter = st.multiselect("Filter by rarity tier", rarities, default=rarities)
        
        with col2:
            # Trier par
            sort_by = st.radio("Sort by", ["Rarity (low to high)", "Rarity (high to low)", "Name (A-Z)"], horizontal=True)
        
        # Filtrer et trier les traits
        traits = data[selected_category]
        
        # Filtrer par niveau de rareté (s'adapter aux différents formats de données)
        filtered_traits = []
        for t in traits:
            # S'assurer que t est un objet et qu'il a une clé 'tier'
            if isinstance(t, dict) and "tier" in t:
                if t["tier"] in rarity_filter:
                    filtered_traits.append(t)
            else:
                # Si t n'a pas de tier, considérer qu'il est 'common'
                if "common" in rarity_filter:
                    # Si t est une chaîne, le convertir en objet
                    if isinstance(t, str):
                        filtered_traits.append({"trait": t, "rarity": 5.0, "tier": "common"})
                    else:
                        filtered_traits.append(t)
        
        # Trier les traits
        if sort_by == "Rarity (low to high)":
            filtered_traits.sort(key=lambda x: x.get("rarity", 5.0) if isinstance(x, dict) else 5.0)
        elif sort_by == "Rarity (high to low)":
            filtered_traits.sort(key=lambda x: x.get("rarity", 5.0) if isinstance(x, dict) else 5.0, reverse=True)
        else:  # Nom A-Z
            filtered_traits.sort(key=lambda x: x.get("trait", str(x)).lower() if isinstance(x, dict) else str(x).lower())
        
        # Afficher les traits
        st.subheader(f"{selected_category} traits ({len(filtered_traits)})")
        
        # Conteneur pour les cartes de traits
        st.markdown('<div class="traits-container">', unsafe_allow_html=True)
        
        # Afficher les cartes de traits en colonnes
        cols = st.columns(4)
        
        for i, trait in enumerate(filtered_traits):
            # Adapter à différents formats de données
            if isinstance(trait, dict):
                trait_name = trait.get("trait", str(trait))
                rarity = trait.get("rarity", 5.0)
                tier = trait.get("tier", "common")
            else:
                trait_name = str(trait)
                rarity = 5.0
                tier = "common"
            
            # Déterminer la couleur en fonction du niveau de rareté
            tier_color = {
                "common": "#8bc34a",     # Light green
                "uncommon": "#4CAF50",   # Medium green
                "rare": "#2196F3",       # Blue
                "epic": "#9C27B0",       # Purple
                "legendary": "#FFD700"   # Gold
            }
            
            color = tier_color.get(tier, "#8bc34a")
            
            # Afficher la carte de trait dans la colonne appropriée
            with cols[i % 4]:
                st.markdown(
                    f"""
                    <div class="trait-card" style="border-left-color: {color};">
                        <div class="trait-header">
                            <span>{trait_name}</span>
                            <span class="rarity-badge" style="background-color: {color};">{rarity}%</span>
                        </div>
                        <p class="trait-tier">{tier.capitalize()}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.header("Legendary & Rare NFTs Gallery")
    st.markdown("Discover the rarest NFTs in the collection, based on our advanced rarity calculation system.")
    
    # Trouver les NFTs légendaires
    try:
        top_nfts = find_legendary_nfts(limit=50, rarity_data=data)
    except Exception as e:
        st.error(f"Erreur lors de la recherche des NFTs légendaires: {e}")
        top_nfts = []
    
    # Filtrer par niveau de rareté
    rarity_filter = st.multiselect(
        "Filtrer par niveau de rareté", 
        ["legendary", "epic", "rare", "uncommon", "common"],
        default=["legendary", "epic"]
    )
    
    filtered_nfts = [nft for nft in top_nfts if nft["tier"] in rarity_filter]
    
    # Afficher le nombre de NFTs trouvés
    st.write(f"**{len(filtered_nfts)} NFTs** matching the selected criteria")
    
    # Afficher les NFTs en grille simple
    if filtered_nfts:
        # Créer une grille de 3 colonnes
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]
        
        # Afficher chaque NFT
        for i, nft in enumerate(filtered_nfts):
            nft_number = nft["number"]
            tier = nft["tier"]
            score = nft["score"]
            unique_count = nft["unique_count"]
            legendary_count = nft["legendary_count"]
            
            # Couleurs par tier
            tier_colors = {
                "legendary": "#FFD700",  # Gold
                "epic": "#9C27B0",       # Purple
                "rare": "#2196F3",       # Blue
                "uncommon": "#4CAF50",   # Green
                "common": "#8bc34a"      # Light green
            }
            color = tier_colors.get(tier, "#8bc34a")
            
            # Déterminer la colonne à utiliser
            col = columns[i % 3]
            
            with col:
                # Carte NFT
                st.markdown(f"""
                <div style="border: 2px solid {color}; border-radius: 10px; padding: 10px; margin-bottom: 15px; background-color: #1e1e1e;">
                    <h3 style="color: {color}; margin-top: 0;">NFT #{nft_number}</h3>
                    <p style="margin: 5px 0;">
                        <span style="background-color: {color}; color: black; padding: 3px 8px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                            {tier.capitalize()} - {score:.2f}%
                        </span>
                    </p>
                    <p>Unique traits: {unique_count} | Legendary: {legendary_count}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Traits principaux dans un expander
                with st.expander("Voir les traits"):
                    for category, trait in nft["selected_traits"].items():
                        trait_tier = trait["tier"]
                        trait_color = tier_colors.get(trait_tier, "#8bc34a")
                        
                        # Badge UNIQUE si applicable
                        unique_badge = ""
                        if trait.get("count", 0) == 1:
                            unique_badge = "🏆 UNIQUE"
                        
                        # Afficher le trait
                        st.markdown(f"""
                        <div style="margin-bottom: 8px; padding: 5px; border-left: 3px solid {trait_color}; background-color: #2a2a2a;">
                            <strong>{category}:</strong> {trait["trait"]} {unique_badge}<br>
                            <small>Rareté: {trait.get('rarity', 0):.2f}% ({trait_tier.capitalize()})</small>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("No NFT matches your criteria. Try modifying the filters.")

with tabs[3]:
    # About tab
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.header("About this application")
    
    st.markdown("""
    This app allows you to check the rarity of different NFT traits and calculate the overall rarity score of your NFT.
    
    ## How to use
    
    1. Enter your NFT number directly
    2. Or select traits manually to see how rare your combination is
    
    ## Troubleshooting
    
    If the app can't find the rarity for your NFT traits, it may be due to differences in naming between your NFT metadata and the rarity data.
    """)
    
    # Section de débogage
    with st.expander("Debug Tools"):
        st.subheader("Data Analysis")
        
        if st.button("Compare Trait Names"):
            # Analyser les différences entre les noms de traits
            trait_differences = {}
            
            for nft_key, nft_traits in list(nft_data.items())[:10]:  # Limiter à 10 NFTs pour l'analyse
                for category, trait_name in nft_traits.items():
                    matched_category = normalize_category_name(category)
                    
                    if matched_category:
                        if matched_category not in trait_differences:
                            trait_differences[matched_category] = set()
                        
                        # Ajouter le nom du trait
                        trait_differences[matched_category].add(trait_name)
            
            # Afficher les différences
            for category, traits in trait_differences.items():
                st.write(f"**{category}**:")
                
                # Traits dans les métadonnées NFT
                st.write("NFT metadata traits:", ", ".join(list(traits)[:20]))
                
                # Traits dans les données de rareté
                if category in data:
                    rarity_traits = [t["trait"] for t in data[category]]
                    st.write("Rarity data traits:", ", ".join(rarity_traits[:20]))
                    
                    # Calculer les différences
                    nft_set = set([t.lower() for t in traits])
                    rarity_set = set([t.lower() for t in rarity_traits])
                    
                    not_in_rarity = nft_set - rarity_set
                    if not_in_rarity:
                        st.warning(f"Traits in NFT data but not in rarity data: {', '.join(list(not_in_rarity)[:10])}")
                
                st.write("---")
        
        # Option pour enregistrer un mapping personnalisé
        st.subheader("Custom Trait Mapping")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            category = st.selectbox("Category", list(data.keys()))
        with col2:
            nft_trait = st.text_input("NFT Trait Name")
        with col3:
            rarity_trait = st.selectbox("Rarity Trait Name", [t["trait"] for t in data.get(category, [])] if category else [])
        
        if st.button("Add Custom Mapping"):
            st.session_state.custom_mappings = getattr(st.session_state, "custom_mappings", {})
            
            if category not in st.session_state.custom_mappings:
                st.session_state.custom_mappings[category] = {}
            
            st.session_state.custom_mappings[category][nft_trait.lower()] = rarity_trait
            st.success(f"Added mapping: {nft_trait} → {rarity_trait} in {category}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <p>© 2025 CelestialMammoth on Eclipse | <a href="https://github.com/">GitHub</a> | <a href="https://x.com/CelestMammoth">@CelestMammoth</a></p>
</div>
""", unsafe_allow_html=True)
