import json
import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import os
from groq import Groq

def risk_dashboard(request):
    """Renders the Risk Gate Threat Monitor workspace template."""
    return render(request, 'dashboard.html')

@csrf_exempt
def audit_user_account(request):
    """API endpoint to query credit card fraud data from MySQL and evaluate risk via Groq AI."""
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            user_id = int(payload.get("user_id", 0))
            
            # Direct MySQL extraction bypassing Django ORM
            query = f"SELECT * FROM bfsi_model.credit_card_fraud WHERE id = {user_id} LIMIT 1;"
            df = pd.read_sql(query, connection)
            
            if df.empty:
                return JsonResponse({"error": f"Record ID {user_id} not found in credit_card_fraud table."}, status=404)
            
            record = df.iloc[0].to_dict()
            amount = float(record.get('Amount', 0))
            fraud_class = int(record.get('Class', 0))
            
            # Groq AI Compliance Report Generator
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            prompt = f"""
            Analyze this transaction record for fraud detection and risk compliance:
            - Record / User ID: {user_id}
            - Transaction Amount: ${amount:,.2f}
            - Fraud Classification Label (Class): {fraud_class}
            - Time Metric: {record.get('Time', 'N/A')}
            
            Provide a quantitative threat breakdown and a formal Suspicious Activity Report (SAR) filing narrative.
            """
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "You are a senior banking risk compliance officer."}, {"role": "user", "content": prompt}],
                model="openai/gpt-oss-120b",
                temperature=0.3,
                max_tokens=60000
            )
            analysis_text = chat_completion.choices[0].message.content
            
            return JsonResponse({
                "user_id": user_id,
                "amount": amount,
                "fraud_class": fraud_class,
                "risk_analysis": analysis_text
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def get_tier_transactions(request, tier):
    """API endpoint to fetch transaction records filtered by risk tier for interactive review."""
    try:
        # Define SQL filters based on risk tier rules matching your credit_card_fraud dataset
        if tier == 'low':
            query = "SELECT id, Amount, Class FROM bfsi_model.credit_card_fraud WHERE Class = 0 AND Amount < 500 LIMIT 15;"
        elif tier == 'medium':
            query = "SELECT id, Amount, Class FROM bfsi_model.credit_card_fraud WHERE Class = 0 AND Amount >= 500 AND Amount < 5000 LIMIT 15;"
        elif tier == 'high':
            query = "SELECT id, Amount, Class FROM bfsi_model.credit_card_fraud WHERE Class = 1 OR Amount >= 5000 LIMIT 15;"
        else:
            return JsonResponse({"error": "Invalid risk tier specified."}, status=400)
            
        df = pd.read_sql(query, connection)
        records = df.to_dict(orient='records')
        
        return JsonResponse({
            "tier": tier,
            "count": len(records),
            "transactions": records
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)