import pandas as pd
import re
from pathlib import Path


def parse_srt_file(file_path):
    """
    Parse an SRT subtitle file into a DataFrame.
    
    Args:
        file_path: Path to the SRT file
        
    Returns:
        pandas.DataFrame with columns: n_sub, start_t, end_t, text
    """
    # Read the file as text
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into subtitle blocks (separated by empty lines)
    blocks = re.split(r'\n\s*\n', content.strip())
    
    data = []
    
    for block in blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        
        if len(lines) < 3:
            continue
        
        # First line is subtitle number
        try:
            n_sub = int(lines[0].strip())
        except ValueError:
            continue
        
        # Second line is timestamp
        timestamp_line = lines[1].strip()
        timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2}),\d{3}\s*-->\s*(\d{2}:\d{2}:\d{2}),\d{3}', timestamp_line)
        
        if not timestamp_match:
            continue
        
        start_t = timestamp_match.group(1)
        end_t = timestamp_match.group(2)
        
        # Remaining lines are text (combine them with spaces)
        text_lines = lines[2:]
        text = ' '.join(line.strip() for line in text_lines if line.strip())
        
        data.append({
            'n_sub': n_sub,
            'start_t': start_t,
            'end_t': end_t,
            'text': text
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    return df


if __name__ == '__main__':
    # Example usage
    file_path = Path('/Users/CLocs/Downloads/Sample_Surgery1_cut1a.srt')
    df = parse_srt_file(file_path)
    print(df.head(10))
    print(f"\nTotal subtitles: {len(df)}")

