import re
from src.utils.llm_helper import call_gemini_text, setup_gemini
from src.utils.logger import setup_logger
from src.prompts import PHASE_3_SYSTEM_INSTRUCTION, PHASE_3_USER_PROMPT_TEMPLATE

logger = setup_logger(__name__)

REQUIRED_KEYS = [
    "focus_zone_1", "focus_zone_2", "focus_zone_3",
    "action_plan_1", "action_plan_2", "action_plan_3"
]

def parse_llm_response(text: str) -> dict:
    """
    Parses the LLM text output into a dictionary with strict enforcement:
    - 3 Focus Zones
    - 3 Action Plans
    - No student-level framing
    """
    
    # 1. Sanitize Prohibited Phrases (Student Leakage)
    prohibited_phrases = [
        "some students", "many students", "high performers", "low scorers", 
        "individual students", "few students", "most students"
    ]
    
    sanitized_text = text
    masked = False
    for phrase in prohibited_phrases:
        if re.search(r"\b" + re.escape(phrase) + r"\b", sanitized_text, re.IGNORECASE):
            # Replace with class-level equivalent
            sanitized_text = re.sub(r"\b" + re.escape(phrase) + r"\b", "the class", sanitized_text, flags=re.IGNORECASE)
            masked = True
            
    if masked:
        logger.warning("Sanitized student-level phrasing from LLM output.")

    # 2. Extraction Strategy
    # We expect the prompt to give us lists. If the regex based strict parsing fails,
    # we might need to be robust. 
    # Current prompt asks for specific headers. Let's assume headers exist.
    # But instead of searching for single lines, let's look for the blocks.
    # Actually, the user requirement is "Enforce exact output cardinality (3 + 3)".
    # Let's try to extract all lines starting with "- " or numbered lists under headers?
    # Or keep the simple regex if prompt is strict? 
    # The Prompt Template (in prompts.py) likely forces "Focus Zone 1: ...".
    # Let's stick to the mapped extraction but make it robust to find *all* occurences 
    # and then slice/fill.
    
    # Let's extract by sections.
    # Assumption: "Focus Zones" section and "Action Plans" section.
    
    # Alternative: The prompt asks for "Focus Zone 1:", "Focus Zone 2:", etc.
    # Let's define a helper to extract N items.
    
    def extract_items(prefix_base, count, content):
        items = []
        for i in range(1, 10): # Check up to 10 just in case
            # Pattern: "Focus Zone 1: value" or "1. value" if header is "Focus Zones"
            # Based on previous code, it looked for "Focus Zone 1: ..."
            pattern = f"{prefix_base} {i}:\s*(.*)"
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if val: items.append(val)
        return items

    focus_zones = extract_items("Focus Zone", 3, sanitized_text)
    action_plans = extract_items("Action Plan", 3, sanitized_text)
    
    # --- Quality Enhancement (Step 1, 2, 3, 4) ----
    
    def enhance_focus_zone(text):
        # Rule: Avoid statistics, percentages, scores
        # Regex for numbers like 50%, 0.5, 5/10
        if re.search(r"\d+%|\d+\.\d+|\d+/\d+", text):
            logger.warning(f"Focus Zone contains statistics: '{text}'. Rewriting...")
            # Simple heuristic: Split by punctuation and keep non-numeric parts or just strip numbers
            # Better: generic rewrite.
            text = re.sub(r"\(.*?\)", "", text) # Remove parentheticals often containing stats
            text = re.sub(r"\d+%|\d+\.\d+", "", text) # Remove raw numbers
            text = text.replace("Accuracy", "").replace("Score", "").strip()
            
        # Rule: Behavior based. If empty after strip, use generic.
        if not text:
            text = "Difficulty applying core concepts to scenarios"
            
        return text.strip()

    def enhance_action_plan(text):
        # Rule: Start with action verb
        allowed_verbs = ["Reinforce", "Introduce", "Spend", "Use"]
        
        # Check first word
        first_word = text.split(" ")[0] if text else ""
        if first_word not in allowed_verbs:
             logger.warning(f"Action Plan starts with invalid verb: '{first_word}'. Rewriting...")
             # Heuristic: If it contains "should", remove preceding.
             if "should" in text:
                 text = text.split("should")[-1].strip()
             
             # Force prefix if still not valid
             # We can't easily adhere to "Reinforce/Introduce" without semantics. 
             # But prompt says "Required framing".
             # Let's try to map typical issues.
             # Or just prefix "Reinforce the ability to..."
             # But "Use worked examples to" is allowed.
             # Strictness: "Rewrite where necessary".
             # Let's prefix "Reinforce" if in doubt.
             text = f"Reinforce {text}"
             
        # Disallowed patterns check
        disallowed = ["Students should", "It is recommended", "There is a need to"]
        for d in disallowed:
            if d.lower() in text.lower():
                text = re.sub(d, "", text, flags=re.IGNORECASE).strip()
                
        return text

    def clean_text(text):
        # Step 4: Final quality pass (conciseness, hedging)
        hedging = ["may", "might", "could be", "possibly"]
        for h in hedging:
            text = re.sub(r"\b" + h + r"\b", "", text, flags=re.IGNORECASE)
            
        # Remove extra spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # Apply enhancements
    focus_zones = [clean_text(enhance_focus_zone(f)) for f in focus_zones]
    action_plans = [clean_text(enhance_action_plan(a)) for a in action_plans]
    
    # 3. Enforce Cardinality (3 items)
    
    # Truncate
    focus_zones = focus_zones[:3]
    action_plans = action_plans[:3]
    
    # Fill
    filler = "Insufficient class-level signal to derive additional pattern"
    while len(focus_zones) < 3:
        logger.warning("Fewer than 3 Focus Zones derived per class. Filling placeholder.")
        focus_zones.append(filler)
        
    while len(action_plans) < 3:
        logger.warning("Fewer than 3 Action Plans derived per class. Filling placeholder.")
        action_plans.append(filler)
        
    data = {
        "focus_zone_1": focus_zones[0],
        "focus_zone_2": focus_zones[1],
        "focus_zone_3": focus_zones[2],
        "action_plan_1": action_plans[0],
        "action_plan_2": action_plans[1],
        "action_plan_3": action_plans[2]
    }
    
    return data

def synthesize_class(class_id: str, csv_content: str) -> dict:
    """
    Calls Gemini to synthesize class insights.
    """
    setup_gemini()
    
    full_prompt = f"{PHASE_3_SYSTEM_INSTRUCTION}\n\n{PHASE_3_USER_PROMPT_TEMPLATE}"
    
    logger.info(f"Calling Gemini for Class {class_id}...")
    response_text = call_gemini_text(full_prompt, csv_content)
    
    logger.info(f"Received response for {class_id}. Parsing...")
    parsed_data = parse_llm_response(response_text)
    
    parsed_data["class_id"] = class_id
    return parsed_data
