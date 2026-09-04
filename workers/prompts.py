QUALITY_EVALUATION_PROMPT = (
    "You are an expert technical interviewer. "
    "Evaluate this candidate answer. "
    "Return a JSON object with keys: overall_quality_score (0-100), "
    "relevance (0-1), completeness (0-1), clarity (0-1), feedback (string)."
)

TECHNICAL_ACCURACY_PROMPT = (
    "You are a technical interviewer evaluating a candidate's answer. "
    "Return a JSON object with keys: accuracy_score (0-100), "
    "correct_concepts_count (int), incorrect_concepts_count (int), "
    "knowledge_gaps (list of strings)."
)

COMMUNICATION_EVALUATION_PROMPT = (
    "Evaluate the candidate's communication quality. "
    "Return a JSON object with keys: clarity_score (0-100), "
    "professionalism (0-100), confidence_level (0-1), "
    "pace_appropriateness (0-1)."
)

POST_INTERVIEW_FEEDBACK_PROMPT = (
    "You are collecting short feedback from a candidate immediately after an interview. "
    "Keep the survey brief, friendly, and easy to answer. "
    "Ask the candidate these questions: "
    "1. On a scale of 0 to 10, how likely are you to recommend this interview experience "
    "to a friend or colleague? "
    "2. What is one thing we could improve about your interview experience? "
    "The first question must accept a numerical rating from 0 to 10. "
    "The second question should allow open-text feedback."
)


PRODUCT_MANAGEMENT_PROMPTS = [
    {
        "domain": "product",
        "prompt_template": (
            "A food-delivery app can build only two of these four features this quarter: "
            "faster checkout, restaurant loyalty rewards, scheduled delivery, and a "
            "personalized home feed. Prioritize the features and explain your decision. "
            "Consider user impact, business value, strategic alignment, engineering effort, "
            "and trade-offs."
        ),
        "rubric_hint": (
            "Evaluate whether the candidate clearly defines the product goal and target "
            "users, establishes prioritization criteria, compares impact against effort, "
            "makes an explicit ranking, explains trade-offs, and states key assumptions."
        ),
    },
    {
        "domain": "product",
        "prompt_template": (
            "A ride-sharing app has budget to improve only one of three areas: reducing "
            "driver cancellation, improving rider pickup accuracy, or adding a loyalty "
            "program. As the product manager, prioritize one initiative and explain how "
            "you would decide between the options."
        ),
        "rubric_hint": (
            "Evaluate problem framing, identification of affected users, prioritization "
            "criteria, expected customer and business impact, effort or feasibility "
            "considerations, trade-off reasoning, and clarity of the final recommendation."
        ),
    },
    {
        "domain": "product",
        "prompt_template": (
            "You are the product manager for a music streaming app. Monthly active users "
            "are stable, but 30-day retention has fallen from 40% to 30%. Identify the "
            "metrics you would examine to diagnose the decline and explain how each metric "
            "would help you find the underlying problem."
        ),
        "rubric_hint": (
            "Evaluate whether the candidate distinguishes the north-star metric from "
            "diagnostic metrics, considers retention cohorts and segments, identifies "
            "activation and engagement metrics, proposes meaningful breakdowns, and "
            "connects metric changes to actionable hypotheses."
        ),
    },
    {
        "domain": "product",
        "prompt_template": (
            "A mobile payments product has increased new-user sign-ups by 25%, but the "
            "percentage of users completing their first payment has decreased. As the "
            "product manager, define the key metrics and funnel stages you would analyze "
            "to understand what is happening and decide what to improve first."
        ),
        "rubric_hint": (
            "Evaluate funnel understanding, metric selection, conversion analysis, "
            "segmentation, identification of possible drop-off points, prioritization "
            "of investigation areas, and the ability to turn metrics into product actions."
        ),
    },
    {
        "domain": "product",
        "prompt_template": (
            "Estimate the number of food-delivery orders placed in a large Indian city "
            "on an average day. State your assumptions, build a simple estimation model, "
            "calculate the estimate step by step, and explain which assumptions have the "
            "largest effect on the result."
        ),
        "rubric_hint": (
            "Evaluate whether the candidate defines the scope, uses reasonable and "
            "explicit assumptions, breaks the estimate into logical components, performs "
            "consistent calculations, checks the result for plausibility, and identifies "
            "the assumptions most sensitive to the final estimate."
        ),
    },
]

SDE_PROMPT_TEMPLATES = [
    {
        "domain": "sde",
        "difficulty": "easy",
        "prompt_template": (
            "Role: Act as an experienced Software Engineering interviewer. "
            "Context: Generate one technical SDE interview question for a candidate "
            "at an easy difficulty level. Focus on fundamental programming, "
            "object-oriented programming, basic data structures, databases, "
            "debugging, or core software engineering concepts. "
            "Constraints: The question must be clear, practical, and suitable for "
            "an entry-level SDE interview. Vary the topic and question style across "
            "generations. Do not repeat or closely rephrase previously generated "
            "questions. Do not provide the answer or explanation. Return only the "
            "interview question."
        ),
    },
    {
        "domain": "sde",
        "difficulty": "medium",
        "prompt_template": (
            "Role: Act as an experienced Software Engineering interviewer. "
            "Context: Generate one technical SDE interview question for a candidate "
            "at a medium difficulty level. Focus on algorithms, data structures, "
            "database design, SQL, REST APIs, concurrency, testing, debugging, "
            "or practical software engineering problem-solving. "
            "Constraints: The question should require reasoning or application of "
            "technical concepts rather than simple recall. Vary the topic, scenario, "
            "and problem style across generations. Do not repeat or closely rephrase "
            "previously generated questions. Do not provide the answer or explanation. "
            "Return only the interview question."
        ),
    },
    {
        "domain": "sde",
        "difficulty": "hard",
        "prompt_template": (
            "Role: Act as a senior Software Engineering interviewer conducting an "
            "advanced SDE interview. Context: Generate one challenging technical "
            "question involving system design, distributed systems, scalability, "
            "performance optimization, fault tolerance, concurrency, data-intensive "
            "systems, or advanced software architecture. "
            "Constraints: The question must require multi-step technical reasoning "
            "and should reflect real-world engineering challenges. Vary the system, "
            "constraints, and problem scenario across generations. Do not repeat or "
            "closely rephrase previously generated questions. Avoid questions that "
            "can be answered with simple definitions. Do not provide the answer or "
            "explanation. Return only the interview question."
        ),
    },
]
