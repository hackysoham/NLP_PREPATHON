import json
import csv
import os
from datetime import datetime
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report

def parse_iso(ts: str) -> datetime:
    ts = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(ts)

class Evaluator:
    def __init__(self, ground_truth_path: str, predictions_path: str, artifacts_dir: str = "artifacts"):
        self.ground_truth_path = ground_truth_path
        self.predictions_path = predictions_path
        self.artifacts_dir = artifacts_dir
        os.makedirs(self.artifacts_dir, exist_ok=True)

    def load_json(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def evaluate(self):
        try:
            gt_data = self.load_json(self.ground_truth_path)
            preds_data = self.load_json(self.predictions_path)
        except Exception as e:
            print(f"Error loading evaluation files: {e}")
            return
            
        gt_checkpoints = gt_data.get("checkpoints", [])
        
        # Sort predictions by time
        preds_data.sort(key=lambda x: parse_iso(x["as_of_time"]))
        
        # Write trajectory predictions
        with open(os.path.join(self.artifacts_dir, "trajectory_predictions.jsonl"), "w") as f:
            for p in preds_data:
                f.write(json.dumps(p) + "\n")
        
        matches = []
        unmatched_gt = []
        
        for gt in gt_checkpoints:
            gt_time = parse_iso(gt["as_of_time"])
            # Find the latest prediction <= gt_time
            valid_preds = [p for p in preds_data if parse_iso(p["as_of_time"]) <= gt_time]
            if valid_preds:
                best_pred = valid_preds[-1]
                matches.append({
                    "gt": gt,
                    "pred": best_pred
                })
            else:
                unmatched_gt.append(gt)

        # Unmatched predictions are those not picked as best_pred
        matched_pred_times = {m["pred"]["as_of_time"] for m in matches}
        unmatched_preds = [p for p in preds_data if p["as_of_time"] not in matched_pred_times]
        
        # 2. Print counts
        print(f"Number of ground truth rows: {len(gt_checkpoints)}")
        print(f"Number of prediction rows (internal trajectory): {len(preds_data)}")
        print(f"Number of exact customer/checkpoint matches: {len(matches)}")
        print(f"Unmatched ground-truth rows: {len(unmatched_gt)}")
        print(f"Unmatched prediction rows: {len(unmatched_preds)}")

        # 3. Build an explicit matching table
        print("\n--- MATCHED CHECKPOINT TABLE ---")
        print(f"{'GT Time':<22} | {'Pred Time':<22} | {'GT State':<22} | {'Pred State':<22} | {'GT Action':<20} | {'Pred Action'}")
        
        csv_rows = []
        csv_rows.append(["gt_as_of_time", "pred_as_of_time", "gt_inferred_state", "pred_inferred_state", "gt_action", "pred_action", "gt_hitl", "pred_hitl"])

        checkpoint_preds = []

        for m in matches:
            gt = m["gt"]
            pr = m["pred"]
            print(f"{gt['as_of_time']:<22} | {pr['as_of_time']:<22} | {gt['expected_inferred_state']:<22} | {pr['inferred_state']:<22} | {gt['expected_action']:<20} | {pr['action']}")
            
            csv_rows.append([
                gt['as_of_time'], pr['as_of_time'],
                gt['expected_inferred_state'], pr['inferred_state'],
                gt['expected_action'], pr['action'],
                gt.get('expected_hitl_status', ''), pr['hitl_status']
            ])
            checkpoint_preds.append(pr)

        with open(os.path.join(self.artifacts_dir, "evaluation_matches.csv"), "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)
            
        with open(os.path.join(self.artifacts_dir, "checkpoint_predictions.json"), "w") as f:
            json.dump(checkpoint_preds, f, indent=2)

        # 8. Before calculating F1
        print("\nGround truth checkpoint count:", len(gt_checkpoints))
        print("Matched checkpoint count:", len(matches))
        print("Missing checkpoint count:", len(unmatched_gt))
        print("Prediction-only count:", len(unmatched_preds))
        
        # 10. Assertions
        assert len(matches) + len(unmatched_gt) == len(gt_checkpoints), "Every scored row must have exactly one ground-truth match or be unmatched."
        for m in matches:
            assert parse_iso(m["pred"]["as_of_time"]) <= parse_iso(m["gt"]["as_of_time"]), "Prediction time must be <= GT time"

        # 11. Calculate metrics
        if len(matches) == 0:
            print("No matches found to evaluate.")
            return

        y_true_state = [m["gt"]["expected_inferred_state"] for m in matches]
        y_pred_state = [m["pred"]["inferred_state"] for m in matches]

        y_true_action = [m["gt"]["expected_action"] for m in matches]
        y_pred_action = [m["pred"]["action"] for m in matches]
        
        print("\n--- METRICS ---")
        print("State Accuracy:", accuracy_score(y_true_state, y_pred_state))
        print("State Macro F1:", f1_score(y_true_state, y_pred_state, average='macro', zero_division=0))
        print("\nState Classification Report:")
        print(classification_report(y_true_state, y_pred_state, zero_division=0))
        
        print("Action Accuracy:", accuracy_score(y_true_action, y_pred_action))
        print("Action Macro F1:", f1_score(y_true_action, y_pred_action, average='macro', zero_division=0))
        
        print("\nMetrics note: log loss, Brier score, and calibration require probabilistic outputs which are currently mocked.")
