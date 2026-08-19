from langgraph.graph import StateGraph, START, END
from backend.state import DebateState
from backend.agents import support_agent_node, oppose_agent_node, cross_examination_node, judge_agent_node

def build_debate_graph():
    # 1. Initialize StateGraph
    workflow = StateGraph(DebateState)
    
    # 2. Add Nodes
    workflow.add_node("support_agent", support_agent_node)
    workflow.add_node("oppose_agent", oppose_agent_node)
    workflow.add_node("cross_examination", cross_examination_node)
    workflow.add_node("judge_agent", judge_agent_node)
    
    # 3. Add Edges (Parallel Execution for Debaters)
    workflow.add_edge(START, "support_agent")
    workflow.add_edge(START, "oppose_agent")
    workflow.add_edge("support_agent", "cross_examination")
    workflow.add_edge("oppose_agent", "cross_examination")
    
    def should_continue(state: DebateState) -> str:
        # Loop for exactly 1 round of cross_examination (which generates 1 rebuttal total)
        # We incremented turn_count in cross_examination, so after round 1, turn_count is 2.
        if state.get("turn_count", 1) <= 1:
            return "cross_examination"
        return "judge_agent"

    workflow.add_conditional_edges(
        "cross_examination",
        should_continue,
        {
            "cross_examination": "cross_examination",
            "judge_agent": "judge_agent"
        }
    )
    
    workflow.add_edge("judge_agent", END)
    
    # 4. Compile the graph
    app = workflow.compile()
    
    return app

debate_graph = build_debate_graph()
