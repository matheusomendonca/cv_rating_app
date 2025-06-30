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
    if judge_ratings:
        rating_df = pd.DataFrame([r.model_dump() for r in judge_ratings])
        rating_df = rating_df.rename(columns={'score': 'final_score'})
        rating_df = rating_df.drop_duplicates(subset='candidate_id', keep='first')
        # Remove file column from rating_df to avoid duplication
        if 'file' in rating_df.columns:
            rating_df = rating_df.drop(columns=['file'])
        score_col = 'final_score'
    else:
        rating_df = pd.DataFrame([r.model_dump() for r in ratings])
        rating_df = rating_df.rename(columns={'score': 'initial_score'})
        rating_df = rating_df.drop_duplicates(subset='candidate_id', keep='first')
        # Remove file column from rating_df to avoid duplication
        if 'file' in rating_df.columns:
            rating_df = rating_df.drop(columns=['file'])
        score_col = 'initial_score'

    # Fix: If rating_df is empty, ensure it has a 'candidate_id' column for merging
    if rating_df.empty:
        rating_df = pd.DataFrame(columns=['candidate_id'])

    # OUTER JOIN to keep all candidates
    df = info_df.merge(rating_df, on="candidate_id", how="outer", suffixes=('', '_rating'))

    # Fill missing values for candidates with no rating
    for col in ['final_score', 'initial_score', 'strengths', 'weaknesses', 'rationale']:
        if col in df.columns:
            df[col] = df[col].fillna("MISSING")

    # Remove candidate_id from final output
    if 'candidate_id' in df.columns:
        df = df.drop(columns=['candidate_id'])

    # Reorder columns to put score first - with proper checks
    if score_col in df.columns:
        other_cols = [col for col in df.columns if col != score_col]
        df = df[[score_col] + other_cols]
    else:
        # If score column is missing, just use the DataFrame as is
        print(f"Warning: Expected score column '{score_col}' not found in DataFrame. Available columns: {df.columns.tolist()}")

    # Debug print
    print("combine(): Number of unique candidate_ids in info_df:", info_df['candidate_id'].nunique())
    print("combine(): Number of unique candidate_ids in rating_df:", rating_df['candidate_id'].nunique())
    print("combine(): Number of rows in final DataFrame:", len(df))
    print("combine(): Final DataFrame columns:", df.columns.tolist())

    # Sort by the appropriate score column - with proper checks
    if score_col in df.columns:
        # Ensure the score column contains numeric values for sorting
        try:
            df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
            return df.sort_values(by=score_col, ascending=False)
        except Exception as e:
            print(f"Warning: Could not sort by {score_col}: {e}")
            return df
    else:
        return df
