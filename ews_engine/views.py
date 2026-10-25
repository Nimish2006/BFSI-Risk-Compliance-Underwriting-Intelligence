# Create your views here.
import json
import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import os
from groq import Groq

def ews_dashboard(request):
    """Renders the Early Warning System workspace template."""
    return render(request, 'ews_dashboard.html')

@csrf_exempt
def analyze_ews_loan(request):
    """API endpoint to pull loan default records and formulate proactive hardship outreach strategies."""
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            loan_id = int(payload.get("loan_id", 0))
            
            # Direct MySQL query on Lending Club schema
            query = f"SELECT * FROM bfsi_model.ews_loan_data WHERE id = {loan_id} LIMIT 1;"
            df = pd.read_sql(query, connection)
            
            if df.empty:
                return JsonResponse({"error": f"Loan ID {loan_id} not found in ews_loan_data table."}, status=404)
            
            loan_record = df.iloc[0].to_dict()
            fico = int(loan_record.get('fico', 700))
            not_fully_paid = int(loan_record.get('not_fully_paid', 0))
            
            risk_status = "CRITICAL DEFAULT WARNING" if not_fully_paid == 1 or fico < 640 else "PERFORMING PORTFOLIO ASSET"
            
            # Groq AI Hardship & Restructuring Advisor
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            prompt = f"""
            Analyze this credit account for Early Warning System (EWS) default prediction:
            - Loan ID: {loan_id}
            - FICO Score: {fico}
            - Installment Amount: ${loan_record.get('installment', 0)}
            - Debt-to-Income (DTI): {loan_record.get('dti', 0)}
            - Historical Default Flag (not_fully_paid): {not_fully_paid}
            - Revolving Balance: ${loan_record.get('revol_bal', 0)}
            
            Generate an internal risk mitigation restructuring brief and an empathetic borrower hardship outreach message.
            """
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "You are a proactive loan portfolio risk manager."}, {"role": "user", "content": prompt}],
                model="openai/gpt-oss-120b",
                temperature=0.3,
                max_tokens=8000
            )
            outreach_text = chat_completion.choices[0].message.content
            
            return JsonResponse({
                "loan_id": loan_id,
                "fico": fico,
                "risk_status": risk_status,
                "ews_insights": outreach_text
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)