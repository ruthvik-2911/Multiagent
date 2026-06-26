def compose(results):
    context = ""
    sources = []
    
    for result in results:
        if result["status"] == "success":
            context += (
                f"\n[{result['agent'].upper()}]\n"
                f"{result['context']}\n"
            )
            sources.extend(
                result.get("sources", [])
            )
            
    return {
        "context": context,
        "sources": sources
    }
