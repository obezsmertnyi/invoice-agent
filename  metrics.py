from collections import defaultdict
from datetime import datetime, timedelta

# Metrics storage (in production use Redis or database)
metrics = defaultdict(list)

@app.get("/metrics")
async def get_metrics():
    """Get processing metrics"""
    
    # Calculate stats for last 24 hours
    cutoff_time = datetime.now() - timedelta(hours=24)
    recent_metrics = [
        m for m in metrics['processing_times'] 
        if m['timestamp'] > cutoff_time
    ]
    
    if recent_metrics:
        avg_time = sum(m['time'] for m in recent_metrics) / len(recent_metrics)
        success_rate = sum(1 for m in recent_metrics if m['success']) / len(recent_metrics) * 100
    else:
        avg_time = 0
        success_rate = 0
    
    return {
        "last_24_hours": {
            "total_processed": len(recent_metrics),
            "average_processing_time": f"{avg_time:.2f}s",
            "success_rate": f"{success_rate:.1f}%",
            "models_used": dict(metrics['models_used'])
        },
        "all_time": {
            "total_processed": len(metrics['processing_times']),
            "document_types": dict(metrics['document_types'])
        }
    }

# Update your extraction endpoint to track metrics
# Add this after successful extraction:
metrics['processing_times'].append({
    'timestamp': datetime.now(),
    'time': processing_time,
    'success': True
})
metrics['models_used'][extraction_result["model_used"]] += 1
metrics['document_types'][document_type] += 1