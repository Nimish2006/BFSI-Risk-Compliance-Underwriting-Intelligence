import os
import pandas as pd
from groq import Groq

class GermanCreditScoreCard:
    def __init__(self):
        self.base_score = 500 
        
    def calculate_score(self, borrower_profile):
        score = self.base_score
        checking = str(borrower_profile.get('checking_account', '')).lower().strip()
        if 'rich' in checking: score += 100
        elif 'moderate' in checking: score += 50
        else: score += 20
        
        amount = float(borrower_profile.get('credit_amount', 0))
        duration = float(borrower_profile.get('duration', 1))
        monthly_burden = amount / duration if duration > 0 else amount
        
        if monthly_burden > 300: score -= 80  
        elif monthly_burden > 150: score -= 40
        else: score += 30                      
        
        return max(300, min(850, score))

    def evaluate_underwriting_decision(self, credit_score, amount):
        if credit_score >= 680:
            decision = "AUTOMATED_APPROVE"
            remarks = "Prime Borrower profile. Immediate capital disbursement authorized."
        elif credit_score >= 550:
            if amount > 5000:
                decision = "MANUAL_UNDERWRITING"
                remarks = "Near-prime applicant. Elevated loan size requires oversight."
            else:
                decision = "AUTOMATED_APPROVE"
                remarks = "Approved within acceptable baseline tier parameters."
        else:
            decision = "AUTOMATED_REJECT"
            remarks = "Subprime risk matrix match. Reserves below threshold."
        return {"credit_score": credit_score, "underwriting_decision": decision, "compliance_remarks": remarks}


class IntelligentUnderwritingAgent:
    def __init__(self, scorecard):
        self.scorecard = scorecard
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def process_application(self, borrower_profile):
        base_score = self.scorecard.calculate_score(borrower_profile)
        initial_action = self.scorecard.evaluate_underwriting_decision(base_score, float(borrower_profile.get('credit_amount', 0)))
        
        decision = initial_action['underwriting_decision']
        amount = float(borrower_profile.get('credit_amount', 0))
        duration = int(borrower_profile.get('duration', 12))
        
        agent_action = "DISPATCH_FUNDS_ROUTE"
        counter_offer = None

        if decision == "AUTOMATED_REJECT" or (decision == "MANUAL_UNDERWRITING" and amount > 5000):
            agent_action = "CALCULATE_COUNTER_OFFER"
            safe_amount_target = 150.0 * duration
            if safe_amount_target < amount and safe_amount_target >= 500:
                counter_offer = {
                    "original_request": amount,
                    "autonomous_counter_amount": round(safe_amount_target, 2),
                    "reasoning": "Agent intervention: Scaled loan down to protect risk boundaries."
                }
                agent_action = "FORWARD_COUNTER_OFFER_TO_BORROWER"
            else:
                agent_action = "FINAL_COMPLIANCE_REJECTION_ROUTE"

        ai_memo = self._generate_live_groq_memo(borrower_profile, base_score, initial_action, counter_offer)
        return {
            "scorecard": initial_action,
            "agent_directives": {"routing_action": agent_action, "counter_offer_details": counter_offer},
            "generative_outputs": ai_memo
        }

    def _generate_live_groq_memo(self, profile, score, action, counter):
        prompt = f"""
        Analyze this consumer lending application:
        - Internal Risk Score: {score}/850
        - System Decision: {action['underwriting_decision']}
        - Requested Amount: ${profile.get('credit_amount')} over {profile.get('duration')} months
        - Checking/Savings Status: {profile.get('checking_account')}
        Generate two sections separated by '---':
        ### 1. Executive Credit Memorandum
    Provide a professional risk assessment memo covering:
    - Summary of the decision and risk score evaluation.
    - Key risk factors and their impact (use clean bullet points, NOT markdown tables).

    ### 2. Customer Notification Letter
    Provide a formal, polite, clear letter addressed to the applicant explaining the decision, next steps, and recourse options.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "system", "content": "Expert AI risk underwriter."}, {"role": "user", "content": prompt}],
                model="openai/gpt-oss-120b",
                temperature=0.3,
                max_tokens=65000
            )
            raw = chat_completion.choices[0].message.content
            parts = raw.split("---") if "---" in raw else [raw, "Review complete."]
            return {"executive_credit_summary": parts[0].strip(), "customer_facing_letter": parts[1].strip()}
        except Exception as e:
            return {"executive_credit_summary": str(e), "customer_facing_letter": "System busy."}