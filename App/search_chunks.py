import os
import re
from collections import Counter

def search_textbook(symptoms):
    """
    Search through medical textbook chunks for relevant information based on user symptoms.
    
    Args:
        symptoms (str): User's reported symptoms
        
    Returns:
        list: List of relevant text chunks
    """
    # Convert symptoms to lowercase and tokenize
    symptoms = symptoms.lower()
    symptom_words = re.findall(r'\b\w+\b', symptoms)
    
    # Check if textbook_chunks directory exists
    if not os.path.exists('textbook_chunks'):
        print("Warning: textbook_chunks directory not found")
        return ["No medical textbook data available."]
    
    # Dictionary to store matches with their relevance score
    matches = {}
    
    # List all files in the textbook_chunks directory
    try:
        files = os.listdir('textbook_chunks')
    except Exception as e:
        print(f"Error accessing textbook_chunks: {e}")
        return ["Error accessing medical database."]
    
    # Process each file
    for filename in files:
        filepath = os.path.join('textbook_chunks', filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Calculate relevance score
                score = 0
                content_lower = content.lower()
                
                # Count exact symptom matches
                for word in symptom_words:
                    if len(word) > 2:  # Ignore very short words
                        score += content_lower.count(word)
                
                # Check for phrase matches (higher weight)
                for phrase in re.findall(r'\b(\w+\s+\w+)\b', symptoms):
                    if phrase.lower() in content_lower:
                        score += 3  # Give higher weight to phrase matches
                
                # If there's any relevance, store the content with its score
                if score > 0:
                    matches[content] = score
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    
    # Sort chunks by relevance score (descending)
    sorted_matches = [content for content, _ in sorted(matches.items(), key=lambda x: x[1], reverse=True)]
    
    # Return top 3 most relevant chunks (or fewer if not enough matches)
    return sorted_matches[:3]