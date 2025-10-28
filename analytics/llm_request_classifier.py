"""
LLM-based request classifier for RBSA report routing.
Uses OpenAI to interpret user intent and map to specific report sections.
"""

import json
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def classify_rbsa_request(user_message: str) -> Dict[str, Any]:
    """
    Use LLM to classify a user's request for RBSA analysis results.
    
    Args:
        user_message: The user's natural language request
        
    Returns:
        Dict containing:
        - report_type: str ('final', 'approach_a', 'approach_b', 'approach_c', 'approach_d', 'desmoothing', 'substitution', 'unknown')
        - summary_type: str ('executive', 'detailed', 'either')
        - confidence: float (0.0 to 1.0)
        - reasoning: str (explanation of classification)
    """
    
    system_prompt = """You are an expert classifier for RBSA (Return-Based Style Analysis) report requests.

Your job is to analyze user requests and determine:
1. Which report section they want
2. What level of detail they want
3. Your confidence in the classification

Available report types:
- final: Overall/final RBSA results, summary, conclusion, main findings
- approach_a: Stepwise NNLS approach, Approach A specific results  
- approach_b: Elastic Net + NNLS approach, Approach B specific results
- approach_c: PCA + NNLS approach, Approach C specific results  
- approach_d: Clustering + Approach A, Approach D specific results
- desmoothing: Desmoothing analysis, autocorrelation, smoothing correction
- substitution: Index substitution, replacement analysis
- unknown: Cannot determine or general question

Summary types:
- executive: Brief, high-level summary with key takeaways
- detailed: Comprehensive, in-depth analysis with methodology  
- either: User didn't specify, could be either

Return ONLY valid JSON in this exact format:
{
  "report_type": "final",
  "summary_type": "detailed", 
  "confidence": 0.95,
  "reasoning": "User asks for 'detailed summary' which indicates final results with comprehensive detail"
}"""

    user_prompt = f"""Classify this RBSA report request:

"{user_message}"

Analyze the request and return the classification as JSON."""

    try:
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cost-effective for classification
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=200,   # Keep response concise
            response_format={"type": "json_object"}  # Ensure JSON response
        )
        
        result_text = response.choices[0].message.content
        if not result_text:
            raise ValueError("Empty response from LLM")
            
        result = json.loads(result_text)
        
        # Validate the response structure
        required_keys = {'report_type', 'summary_type', 'confidence', 'reasoning'}
        if not all(key in result for key in required_keys):
            raise ValueError(f"Missing required keys. Got: {list(result.keys())}")
            
        # Validate report_type
        valid_reports = {'final', 'approach_a', 'approach_b', 'approach_c', 'approach_d', 
                        'desmoothing', 'substitution', 'unknown'}
        if result['report_type'] not in valid_reports:
            result['report_type'] = 'unknown'
            
        # Validate summary_type  
        valid_summaries = {'executive', 'detailed', 'either'}
        if result['summary_type'] not in valid_summaries:
            result['summary_type'] = 'either'
            
        # Ensure confidence is between 0 and 1
        confidence = float(result['confidence'])
        result['confidence'] = max(0.0, min(1.0, confidence))
        
        return result
        
    except Exception as e:
        # Fallback classification on error
        return {
            "report_type": "unknown",
            "summary_type": "either", 
            "confidence": 0.0,
            "reasoning": f"Classification failed: {str(e)}"
        }


def test_classifier():
    """Test the classifier with various request examples"""
    
    test_cases = [
        "Show me the detailed summary",
        "Give me more details about the final results", 
        "What were the results for Approach A?",
        "Tell me about the stepwise NNLS approach",
        "Show me the desmoothing analysis",
        "I want the executive summary of approach B",
        "What about substitution results?",
        "Can you explain the clustering approach in detail?",
        "Give me the overall conclusion",
        "What's the headline finding?",
        "How did the elastic net perform?",
        "Show me everything about approach C",
        "What are the key takeaways?",
        "I need comprehensive analysis of the final approach",
        "Just give me the highlights"
    ]
    
    print("🧪 Testing RBSA Request Classifier\n")
    
    for i, test_request in enumerate(test_cases, 1):
        print(f"Test {i}: '{test_request}'")
        result = classify_rbsa_request(test_request)
        
        print(f"  → Report: {result['report_type']}")
        print(f"  → Summary: {result['summary_type']}")  
        print(f"  → Confidence: {result['confidence']:.2f}")
        print(f"  → Reasoning: {result['reasoning']}")
        print()


if __name__ == "__main__":
    test_classifier()