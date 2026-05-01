from typing import List, Dict, Any, Optional

def analyze_solver_history(history: List[float], tolerance: float = 1e-6) -> Dict[str, Any]:
    """
    Analyze optimization history and return summary metrics.
    
    Args:
        history: list of objective scores per step (initial + each iteration)
        tolerance: threshold to detect convergence (change between steps)
    
    Returns:
        dict with keys: initial_score, final_score, best_score, best_step,
                        score_range, total_steps, converged, convergence_step, improvement
    """
    if not history:
        return {}
    
    if len(history) == 1:
        return {
            'initial_score': history[0],
            'final_score': history[0],
            'best_score': history[0],
            'best_step': 0,
            'score_range': 0.0,
            'total_steps': 0,
            'converged': False,
            'convergence_step': None,
            'improvement': 0.0
        }
    
    initial = history[0]
    final = history[-1]
    best = min(history)
    best_step = history.index(best)  # first occurrence
    score_range = max(history) - min(history)
    total_steps = len(history) - 1
    improvement = initial - final
    
    # Detect convergence: first step where change < tolerance
    converged = False
    convergence_step = None
    for i in range(1, len(history)):
        if abs(history[i] - history[i-1]) < tolerance:
            converged = True
            convergence_step = i  # step index (1-based step number)
            break
    
    return {
        'initial_score': initial,
        'final_score': final,
        'best_score': best,
        'best_step': best_step,
        'score_range': score_range,
        'total_steps': total_steps,
        'converged': converged,
        'convergence_step': convergence_step,
        'improvement': improvement
    }
