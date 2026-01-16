# Multi-turn conversation examples for Store Manager analytics
CONVERSATION_HISTORY_EXAMPLES = [
    {
        "title": "Multi-Turn Context Building - Year Analysis",
        "conversation": [
            {
                "turn": 1,
                "question": "What is total sales in 2013?",
                "response": "Total sales in 2013 amounted to **$2,665,070.95**, representing 37,961 units sold throughout the year."
            },
            {
                "turn": 2,
                "question": "Who was the top customer?",
                "response": "The top customer in 2013 generated **$16,020.82**, representing **0.6% of the $2.6M total** we just discussed. This high-value customer should be prioritized for retention programs."
            },
            {
                "turn": 3,
                "question": "What about top product?",
                "response": "Following up on 2013 performance, the **Nokia Smart Phone, Full Size** was the top product with **$20,334.71** in sales, contributing **0.8% of the total $2.6M revenue** for that year."
            }
        ]
    },
    {
        "title": "Regional Drill-Down Pattern",
        "conversation": [
            {
                "turn": 1,
                "question": "Show me sales by region",
                "response": "### Summary\nWest region leads with **$725,458** (32% of total), followed by East with **$678,781** (30%).\n\n### Key Metrics\n| Region | Sales | Share |\n|--------|-------|-------|\n| West | $725,458 | 32% |\n| East | $678,781 | 30% |\n| Central | $501,240 | 22% |\n| South | $391,722 | 16% |\n\n### Key Insights\n- **Market Leadership**: West outperforms by $47K, focus on replicating strategies in South\n- **Growth Opportunity**: South region represents 16% - targeted campaigns could boost revenue\n- **Regional Balance**: Top 2 regions account for 62% of sales, diversification needed"
            },
            {
                "turn": 2,
                "question": "Tell me more about West region",
                "response": "Drilling into the **West region** from our analysis, this top performer achieved **$725,458 (32% of total sales)**. Technology products drive 45% of West sales, with Phones leading at $180K. **Action**: Replicate West's Technology-focused strategy in underperforming South region."
            }
        ]
    },
    {
        "title": "Customer Value Follow-Up",
        "conversation": [
            {
                "turn": 1,
                "question": "Show me top 5 customers by sales",
                "response": "### Summary\nTop 5 customers generated **$71,293** combined (3.2% of total sales).\n\n### Key Metrics\n| Customer | Sales |\n|----------|-------|\n| S*** M*** | $18,423 |\n| T*** S*** | $17,890 |\n| R*** J*** | $14,567 |\n| K*** L*** | $11,231 |\n| A*** W*** | $9,182 |\n\n### Key Insights\n- **High-Value Concentration**: Top 5 represent 3.2% of revenue - implement VIP retention program\n- **Customer Lifetime Value**: $14,259 average - worth investing in loyalty initiatives\n- **Risk Management**: Top customer only 0.8% of total - healthy distribution, low dependency"
            },
            {
                "turn": 2,
                "question": "What products does the top customer buy?",
                "response": "The **top customer (S*** M***, $18,423)** from our previous analysis primarily purchases **Technology products (78% of their spending)**. Phones account for $8,900, Copiers $5,200. **Action**: Cross-sell Accessories to this high-value Technology buyer to increase wallet share."
            }
        ]
    },
]


def get_conversation_examples(num_examples: int = None) -> list:
    """
    Get conversation history examples for few-shot prompting
    
    Args:
        num_examples: Number of example conversations to return (None = all)
    
    Returns:
        List of conversation examples
    """
    if num_examples is None:
        return CONVERSATION_HISTORY_EXAMPLES
    return CONVERSATION_HISTORY_EXAMPLES[:num_examples]


def format_examples_for_prompt() -> str:
    """
    Format conversation examples for LLM prompt (few-shot learning)
    
    Returns:
        Formatted string showing multi-turn conversation patterns
    """
    formatted = "\n=== FEW-SHOT EXAMPLES (Learn from these patterns) ===\n\n"
    
    for example in CONVERSATION_HISTORY_EXAMPLES:
        formatted += f"**{example['title']}:**\n"
        for turn in example['conversation']:
            formatted += f"Turn {turn['turn']} Q: {turn['question']}\n"
            formatted += f"Turn {turn['turn']} A: {turn['response']}\n\n"
        formatted += "---\n\n"
    
    return formatted



