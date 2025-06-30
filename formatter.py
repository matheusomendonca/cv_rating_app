import pandas as pd
import unicodedata

def clean_text_for_excel(text):
    """Clean text to be Excel-safe by normalizing unicode characters."""
    # Handle lists/arrays by joining as comma-separated string
    if isinstance(text, (list, tuple)):
        text = ", ".join(str(item) for item in text)
    # Handle numpy arrays
    elif hasattr(text, "tolist") and callable(text.tolist):
        text = ", ".join(str(item) for item in text.tolist())

    if pd.isna(text) or text is None:
        return ""
    
    # Convert to string if it's not already
    text = str(text)
    
    # Normalize unicode characters (NFD decomposition then NFC composition)
    text = unicodedata.normalize('NFD', text)
    text = unicodedata.normalize('NFC', text)
    
    # Replace problematic characters with ASCII equivalents
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ñ': 'n', 'ç': 'c',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Á': 'A', 'À': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'Ó': 'O', 'Ò': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ñ': 'N', 'Ç': 'C'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def to_excel(df: pd.DataFrame, path: str):
    """Save the DataFrame to an Excel file with proper encoding handling."""
    # Create a copy to avoid modifying the original DataFrame
    df_clean = df.copy()
    
    # Clean all string columns for Excel compatibility
    for column in df_clean.columns:
        if df_clean[column].dtype == 'object':
            df_clean[column] = df_clean[column].apply(clean_text_for_excel)
    
    try:
        # Try to save with default settings first
        df_clean.to_excel(path, index=False, engine='openpyxl')
    except Exception as e:
        # If that fails, try with additional encoding options
        try:
            df_clean.to_excel(path, index=False, engine='openpyxl', encoding='utf-8')
        except Exception as e2:
            # If still failing, try with xlsxwriter engine
            try:
                df_clean.to_excel(path, index=False, engine='xlsxwriter')
            except Exception as e3:
                # Last resort: save as CSV with UTF-8 encoding
                csv_path = path.replace('.xlsx', '.csv')
                df_clean.to_csv(csv_path, index=False, encoding='utf-8-sig')
                raise Exception(f"Could not save as Excel. Saved as CSV instead: {csv_path}. Original error: {e}")
