from typing import List, Optional
import pandas as pd
from models import CandidateInfo, CandidateRating, JudgeRating

def combine(
    infos: List[CandidateInfo],
    ratings: List[CandidateRating],
    judge_ratings: Optional[List[JudgeRating]] = None
) -> pd.DataFrame:
    """Join info and rating lists into a single DataFrame, keeping all candidates."""
    info_df = pd.DataFrame([c.model_dump() for c in infos])
    info_df = info_df.drop_duplicates(subset='candidate_id', keep='first')
    
    # Rename columns to Portuguese
    column_mapping = {
        'name': 'Nome',
        'email': 'Email',
        'phone': 'Telefone',
        'uf': 'UF',
        'city': 'Cidade',
        'languages': 'Idiomas',
        'programming_languages': 'Linguagens de Programação',
        'frameworks': 'Frameworks',
        'years_experience': 'Anos de Experiência',
        'education': 'Educação',
        'summary': 'Resumo'
    }
    info_df = info_df.rename(columns=column_mapping)
    
    if judge_ratings:
        # Create rating_df from judge_ratings
        rating_df = pd.DataFrame([r.model_dump() for r in judge_ratings])
        
        # Rename judge rating columns
        rating_df = rating_df.rename(columns={
            'score': 'Pontuação Final',
            'strengths': 'Pontos Fortes',
            'weaknesses': 'Pontos Fracos',
            'rationale': 'Justificativa',
            'initial_score': 'Pontuação Inicial',
            'score_adjustment': 'Ajuste de Pontuação'
        })
        
        # Also create initial_rating_df from original ratings for comparison
        initial_rating_df = pd.DataFrame([r.model_dump() for r in ratings])
        initial_rating_df = initial_rating_df.rename(columns={
            'score': 'Pontuação Inicial Original',
            'strengths': 'Pontos Fortes Original',
            'weaknesses': 'Pontos Fracos Original',
            'rationale': 'Justificativa Original'
        })
        
        # Merge judge ratings with initial ratings to ensure we have both
        rating_df = rating_df.merge(initial_rating_df, on='candidate_id', how='left', suffixes=('', '_original'))
        
        rating_df = rating_df.drop_duplicates(subset='candidate_id', keep='first')
        # Remove file column from rating_df to avoid duplication
        if 'file' in rating_df.columns:
            rating_df = rating_df.drop(columns=['file'])
        if 'file_original' in rating_df.columns:
            rating_df = rating_df.drop(columns=['file_original'])
            
        score_col = 'Pontuação Final'
    else:
        rating_df = pd.DataFrame([r.model_dump() for r in ratings])
        
        rating_df = rating_df.rename(columns={
            'score': 'Pontuação Inicial',
            'strengths': 'Pontos Fortes',
            'weaknesses': 'Pontos Fracos',
            'rationale': 'Justificativa'
        })
        rating_df = rating_df.drop_duplicates(subset='candidate_id', keep='first')
        # Remove file column from rating_df to avoid duplication
        if 'file' in rating_df.columns:
            rating_df = rating_df.drop(columns=['file'])
        score_col = 'Pontuação Inicial'

    # Fix: If rating_df is empty, ensure it has a 'candidate_id' column for merging
    if rating_df.empty:
        rating_df = pd.DataFrame(columns=['candidate_id'])

    # OUTER JOIN to keep all candidates
    df = info_df.merge(rating_df, on="candidate_id", how="outer", suffixes=('', '_rating'))

    # Fill missing values for candidates with no rating
    for col in ['Pontuação Final', 'Pontuação Inicial', 'Pontos Fortes', 'Pontos Fracos', 'Justificativa', 'Ajuste de Pontuação']:
        if col in df.columns:
            df[col] = df[col].fillna("AUSENTE")

    # Remove candidate_id from final output
    if 'candidate_id' in df.columns:
        df = df.drop(columns=['candidate_id'])

    # Reorder columns to put score first, then candidate info, then analysis
    if score_col in df.columns:
        try:
            # Convert score to numeric for sorting
            df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
            # Sort by score in descending order
            df = df.sort_values(by=score_col, ascending=False, na_position='last')
            # Keep as numeric for now - we'll format at the end
        except Exception as e:
            print(f"Warning: Could not sort by {score_col}: {e}")
    
    # Ensure file column is first, then score, then other columns
    column_order = ['file']
    if score_col in df.columns:
        column_order.append(score_col)
    if 'Pontuação Inicial' in df.columns and 'Pontuação Inicial' != score_col:
        column_order.append('Pontuação Inicial')
    
    # Add remaining columns
    remaining_cols = [col for col in df.columns if col not in column_order]
    column_order.extend(remaining_cols)
    
    # Reorder columns
    df = df[column_order]
    
    # Apply Brazilian formatting to score columns at the very end
    for col in ['Pontuação Final', 'Pontuação Inicial']:
        if col in df.columns:
            # Convert to numeric first to ensure proper formatting
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # Format with comma as decimal separator for Brazilian format
            df[col] = df[col].apply(lambda x: f"{x:.1f}".replace('.', ',') if pd.notna(x) else "AUSENTE")
    
    return df
