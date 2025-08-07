#!/usr/bin/env python3

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from models import CandidateInfo, CandidateRating, JudgeRating
from parser import CVParser
from agent_extraction import ExtractionAgent
from agent_rating import RatingAgent
from agent_judge import JudgeAgent
from combiner import combine

# Load environment variables
load_dotenv()

def diagnose_streamlit_issue():
    """Diagnose what might be causing the judge agent to fail in Streamlit."""
    print("🔍 DIAGNOSING STREAMLIT JUDGE AGENT ISSUE")
    print("=" * 80)
    
    print("Based on the tests, the judge agent is working correctly in isolation.")
    print("The issue is likely happening in the Streamlit app environment.")
    print("\nPossible causes:")
    print("1. Different job description")
    print("2. API rate limiting")
    print("3. Network connectivity issues")
    print("4. Memory constraints")
    print("5. Different environment variables")
    print("6. Concurrent processing issues")
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC CHECKS")
    print("=" * 60)
    
    # Check 1: Environment variables
    print("\n1. Checking environment variables...")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"✅ OpenAI API key is set (length: {len(openai_key)})")
        print(f"   Key starts with: {openai_key[:10]}...")
    else:
        print("❌ OpenAI API key is not set!")
        print("   Make sure you have OPENAI_API_KEY in your environment")
    
    # Check 2: Test API connectivity
    print("\n2. Testing OpenAI API connectivity...")
    try:
        import openai
        openai.api_key = openai_key
        
        # Test with a simple completion
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Hello'"}],
            max_tokens=5
        )
        print("✅ OpenAI API is accessible")
        print(f"   Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        print("   This might be causing the judge agent to fail")
    
    # Check 3: Test with a simple judge call
    print("\n3. Testing simple judge agent call...")
    try:
        # Create a simple test case
        candidate = CandidateInfo(
            candidate_id="test",
            file="test.pdf",
            name="Test Candidate",
            email="test@test.com",
            phone="123-456-7890",
            uf="SP",
            city="São Paulo",
            languages=["Português"],
            programming_languages=[],
            frameworks=[],
            years_experience=2,
            education="Test Education",
            summary="Test summary"
        )
        
        rating = CandidateRating(
            candidate_id="test",
            file="test.pdf",
            score=7.0,
            strengths="Good communication",
            weaknesses="Limited technical skills",
            rationale="Reasonable candidate"
        )
        
        job_desc = "Analista de Suporte I - Requisitos: atendimento ao cliente, resolução de problemas"
        
        judge = JudgeAgent(job_desc, batch_size=1)
        judge_ratings = judge._judge_batch([candidate], [rating])
        
        if judge_ratings:
            judge_rating = judge_ratings[0]
            print("✅ Simple judge test successful!")
            print(f"   Final Score: {judge_rating.score}")
            print(f"   Score Adjustment: {judge_rating.score_adjustment}")
            
            if "erro de processamento" in judge_rating.score_adjustment.lower():
                print("   ⚠️  But still got error message!")
            else:
                print("   ✅ No error message - judge working correctly")
        else:
            print("❌ Simple judge test failed - no results returned")
            
    except Exception as e:
        print(f"❌ Simple judge test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Check 4: Memory usage
    print("\n4. Checking system resources...")
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"✅ Memory usage: {memory.percent}%")
        print(f"   Available: {memory.available / (1024**3):.1f} GB")
        print(f"   Total: {memory.total / (1024**3):.1f} GB")
        
        if memory.percent > 90:
            print("   ⚠️  High memory usage might cause issues")
        else:
            print("   ✅ Memory usage is normal")
    except ImportError:
        print("⚠️  psutil not available - cannot check memory usage")
    except Exception as e:
        print(f"❌ Memory check failed: {e}")
    
    # Check 5: Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    print("\nTo fix the judge agent issue in Streamlit:")
    print("\n1. Check your job description:")
    print("   - Make sure it's not too long or complex")
    print("   - Try with a simpler job description first")
    print("   - Ensure it's in Portuguese")
    
    print("\n2. Check API rate limits:")
    print("   - Monitor your OpenAI API usage")
    print("   - Consider reducing batch_size or max_workers")
    print("   - Add delays between API calls if needed")
    
    print("\n3. Test with fewer CVs:")
    print("   - Try processing just 1-2 CVs first")
    print("   - Gradually increase the number")
    print("   - Monitor for when the issue starts occurring")
    
    print("\n4. Add error logging:")
    print("   - The judge agent already has debug prints")
    print("   - Check the Streamlit console for error messages")
    print("   - Look for 'Warning:' or 'Error:' messages")
    
    print("\n5. Environment differences:")
    print("   - Make sure you're using the same Python environment")
    print("   - Check that all dependencies are installed")
    print("   - Verify the OpenAI API key is correct")
    
    print("\n6. Try different configurations:")
    print("   - Reduce batch_size from 5 to 2")
    print("   - Reduce max_workers from 4 to 2")
    print("   - Test with different LLM models")

def main():
    """Run the diagnostic."""
    diagnose_streamlit_issue()

if __name__ == "__main__":
    main() 