import argparse
import sys
from app.replay.engine import ReplayEngine
from app.evaluation.scorer import Evaluator

def main():
    parser = argparse.ArgumentParser(description="Agentic Customer 360 CLI")
    parser.add_argument("--scenario", type=str, required=True, help="Path to scenario directory")
    parser.add_argument("--fast", action="store_true", help="Run in fast mode")
    parser.add_argument("--evaluate", action="store_true", help="Run evaluation after replay")
    
    args = parser.parse_args()
    
    history_path = f"{args.scenario}/history_seed.jsonl"
    live_path = f"{args.scenario}/live_stream.jsonl"
    gt_path = f"{args.scenario}/ground_truth.json"
    
    print(f"Loading scenario from {args.scenario}...")
    engine = ReplayEngine(history_path, live_path)
    
    print("Running replay engine...")
    engine.run()
    
    output_preds = "predictions.json"
    output_traces = "traces.json"
    
    engine.export_results(output_preds)
    engine.export_traces(output_traces)
    print(f"Results exported to {output_preds} and {output_traces}")
    
    if args.evaluate:
        print("Running evaluation...")
        evaluator = Evaluator(gt_path, output_preds)
        evaluator.evaluate()

if __name__ == "__main__":
    main()
