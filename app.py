import streamlit as st
import json
import pandas as pd
import random

# Page configuration
st.set_page_config(
    page_title="NFT Traits Rarity Checker",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply custom CSS
try:
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except:
    # Fallback inline CSS
    st.markdown("""
    <style>
        body {
            background-color: #121212;
            color: white;
        }
        .section-container {
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            border: 2px solid #4CAF50;
        }
        .trait-card {
            background-color: #2a2a2a;
            border-left: 5px solid;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

# Load data function
@st.cache_data
def load_data():
    try:
        with open("nft_traits_rarity.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return {}

# Load data
data = load_data()

# Function to normalize category names
def normalize_category_name(name):
    if name.isupper():
        return name.title()
    return name

# Fonction pour fusionner les catégories de fourrure
def merge_fur_categories(data):
    merged_data = {}
    fur_traits = []
    
    # Parcourir toutes les catégories
    for category, traits in data.items():
        # Vérifier directement si le nom de catégorie contient "fur" ou "Fur" (indépendamment de la casse)
        if "fur" in category.lower():
            print(f"Fusionnant la catégorie: {category}")  # Debug
            # Ajouter la catégorie d'origine comme tag pour chaque trait
            for trait in traits:
                trait_copy = trait.copy()
                trait_copy["original_category"] = category
                fur_traits.append(trait_copy)
        else:
            # Conserver les autres catégories telles quelles
            merged_data[category] = traits
    
    # Ajouter la catégorie fusionnée "Fur" avec tous les traits
    if fur_traits:
        merged_data["Fur"] = fur_traits
        print(f"Nombre total de traits de fourrure fusionnés: {len(fur_traits)}")  # Debug
    
    return merged_data

# Normalize category names
normalized_data = {}
for category, traits in data.items():
    normalized_category = normalize_category_name(category)
    normalized_data[normalized_category] = traits

# Fusionner les catégories de fourrure
data = merge_fur_categories(normalized_data)

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
tabs = st.tabs(["Check Rarity", "Explore Traits", "About"])

with tabs[0]:
    # Rarity checker
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.header("Check your traits combination rarity")
    
    # Create two columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Select your NFT traits")
        
        # Initialize variables for rarity calculation
        selected_traits = {}
        total_rarity = 0
        trait_count = 0
        
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
            for category, trait in selected_traits.items():
                # Pour les traits de fourrure, afficher la catégorie d'origine
                display_category = category
                if category == "Fur" and "original_category" in trait:
                    display_category = f"Fur ({normalize_category_name(trait['original_category'])})"
                
                tier_color = {
                    "common": "#8bc34a",     # Light green
                    "uncommon": "#4CAF50",   # Medium green
                    "rare": "#2196F3",       # Blue
                    "epic": "#9C27B0",       # Purple
                    "legendary": "#FFD700"   # Gold
                }
                
                color = tier_color.get(trait["tier"], "#8bc34a")
                
                st.markdown(
                    f"""
                    <div class="trait-card" style="border-left-color: {color};">
                        <strong>{display_category}:</strong> {trait["trait"]} 
                        <span class="rarity-badge" style="background-color: {color};">
                            {trait["rarity"]}% - {trait["tier"].capitalize()}
                        </span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        else:
            st.info("Select traits to see their details here")
        
        # Calculate global rarity score
        st.subheader("Overall Rarity Score")
        
        if trait_count > 0:
            avg_rarity = total_rarity / trait_count
            
            # Determine rank
            if avg_rarity < 1:
                rank = "Legendary"
                stars = "⭐⭐⭐⭐⭐"
                color = "#FFD700"
            elif avg_rarity < 3:
                rank = "Epic"
                stars = "⭐⭐⭐⭐"
                color = "#9C27B0"
            elif avg_rarity < 6:
                rank = "Rare"
                stars = "⭐⭐⭐"
                color = "#2196F3"
            elif avg_rarity < 10:
                rank = "Uncommon"
                stars = "⭐⭐"
                color = "#4CAF50"
            else:
                rank = "Common"
                stars = "⭐"
                color = "#8bc34a"
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.metric("Average Rarity", f"{avg_rarity:.2f}%")
            
            with col2:
                st.markdown(f'<div style="text-align: center;"><span style="font-size: 24px;">{stars}</span><br><span style="font-size: 28px; color: {color}; font-weight: bold;">{rank}</span></div>', unsafe_allow_html=True)
            
            if st.button("Save my combination", type="primary"):
                st.success("Combination saved successfully!")
                
        else:
            st.info("Select at least one trait to calculate rarity score")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    # Explore traits tab content
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.header("Explore all traits")
    
    # Category selection
    categories = list(data.keys())
    selected_category = st.selectbox("Select a category", categories)
    
    if selected_category:
        # Filter options
        col1, col2 = st.columns([3, 1])
        with col1:
            rarity_filter = st.multiselect("Filter by rarity tier", 
                                           ["legendary", "epic", "rare", "common"], 
                                           default=["legendary", "epic", "rare", "common"])
        
        with col2:
            sort_by = st.radio("Sort by:", ["Rarity (asc)", "Rarity (desc)", "Name"])
        
        # Get filtered traits
        filtered_traits = [t for t in data[selected_category] if t["tier"] in rarity_filter]
        
        if filtered_traits:
            # Create and format dataframe
            df = pd.DataFrame(filtered_traits)
            
            # Sort data
            if sort_by == "Rarity (asc)":
                df = df.sort_values("rarity")
            elif sort_by == "Rarity (desc)":
                df = df.sort_values("rarity", ascending=False)
            else:
                df = df.sort_values("trait")
            
            # Rename columns for display
            df = df.rename(columns={"trait": "Trait", "rarity": "Rarity (%)", "tier": "Tier"})
            
            # Add background color based on tier
            def highlight_tier(val):
                if val == "legendary":
                    return 'background-color: rgba(255, 215, 0, 0.2)'
                elif val == "epic":
                    return 'background-color: rgba(156, 39, 176, 0.2)'
                elif val == "rare":
                    return 'background-color: rgba(33, 150, 243, 0.2)'
                elif val == "uncommon":
                    return 'background-color: rgba(76, 175, 80, 0.2)'
                return 'background-color: rgba(76, 175, 80, 0.1)'
            
            styled_df = df.style.applymap(highlight_tier, subset=['Tier'])
            
            # Display table and chart
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            st.subheader("Rarity Distribution")
            chart_data = df[["Trait", "Rarity (%)"]].set_index("Trait").sort_values("Rarity (%)")
            
            # Limit to 20 traits for better readability
            if len(chart_data) > 20:
                st.bar_chart(chart_data.iloc[:20])
                st.info(f"Showing only the first 20 traits out of {len(chart_data)}")
            else:
                st.bar_chart(chart_data)
        else:
            st.warning("No traits found with the selected filters")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    # About tab content
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.header("About this application")
    
    st.markdown("""
    This application helps you check the rarity of your NFT traits and calculate an overall rarity score for your combination.
    
    ### How it works
    
    1. Select your traits in the "Check Rarity" tab
    2. View the details of each trait's rarity
    3. Get an overall score and rank for your combination
    
    ### Rarity levels
    
    - **Legendary** (⭐⭐⭐⭐⭐): Less than 1% rarity
    - **Epic** (⭐⭐⭐⭐): Between 1% and 3% rarity
    - **Rare** (⭐⭐⭐): Between 3% and 6% rarity
    - **Uncommon** (⭐⭐): Between 6% and 10% rarity
    - **Common** (⭐): More than 10% rarity
    
    ### Data
    
    The rarity data comes from analysis of the complete collection.
    """)
    
    # Random example generator
    st.subheader("Try a random example")
    
    if st.button("Generate random example", type="primary"):
        example = {}
        for category, traits in data.items():
            if traits:
                example[category] = random.choice(traits)
        
        if example:
            st.subheader("Random combination")
            
            total_rarity = sum(trait["rarity"] for trait in example.values())
            avg_rarity = total_rarity / len(example)
            
            for category, trait in example.items():
                tier_color = {
                    "common": "#8bc34a",
                    "uncommon": "#4CAF50",
                    "rare": "#2196F3",
                    "epic": "#9C27B0",
                    "legendary": "#FFD700"
                }
                color = tier_color.get(trait["tier"], "#8bc34a")
                
                st.markdown(
                    f"""
                    <div style="border-left: 5px solid {color}; padding: 10px; margin-bottom: 10px; background-color: #2a2a2a; border-radius: 5px;">
                        <strong>{category}</strong>: {trait["trait"]} 
                        <span style="color: {color}; font-weight: bold;">({trait["rarity"]}%, {trait["tier"].capitalize()})</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            
            # Determine rank
            if avg_rarity < 1:
                rank = "Legendary"
                stars = "⭐⭐⭐⭐⭐"
                color = "#FFD700"
            elif avg_rarity < 3:
                rank = "Epic"
                stars = "⭐⭐⭐⭐"
                color = "#9C27B0"
            elif avg_rarity < 6:
                rank = "Rare"
                stars = "⭐⭐⭐"
                color = "#2196F3"
            elif avg_rarity < 10:
                rank = "Uncommon"
                stars = "⭐⭐"
                color = "#4CAF50"
            else:
                rank = "Common"
                stars = "⭐"
                color = "#8bc34a"
                
            st.markdown(f'<div style="text-align: center; margin-top: 20px;"><span style="font-size: 24px; font-weight: bold;">Average Rarity: </span><span style="font-size: 28px; color: {color}; font-weight: bold;">{avg_rarity:.2f}%</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align: center; margin-top: 10px;"><span style="font-size: 28px; color: {color};">{stars}</span><br><span style="font-size: 32px; color: {color}; font-weight: bold;">{rank}</span></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <p>© 2025 CelestialMammoth on Eclipse | <a href="https://github.com">GitHub</a> | <a href="https://x.com/CelestMammoth">@CelestMammoth</a></p>
</div>
""", unsafe_allow_html=True)
