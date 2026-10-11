import json
from pathlib import Path
from typing import Any


class PipelineEvaluator:
    """
    Evaluation harness to compare pipeline JSON outputs against 
    Golden Dataset Ground Truth.
    """

    def __init__(self, gt_dir: str | Path, pred_dir: str | Path, tolerance: float = 0.05):
        self.gt_dir = Path(gt_dir)
        self.pred_dir = Path(pred_dir)
        self.tolerance = tolerance

    def load_json(self, path: Path) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate_document(self, gt: dict, pred: dict) -> dict[str, Any]:
        metrics = {
            "document_number_match": gt.get("document_number") == pred.get("document_number"),
            
            # Entity Resolution Eval (Customer Matching)
            "customer_id_match": gt.get("customer_id") == pred.get("customer_id"),
            
            # Extraction Evals (Totals & Financials)
            "total_amount_match": abs(
                (gt.get("total_amount") or 0.0) - (pred.get("total_amount") or 0.0)
            ) <= self.tolerance,
            
            # HITL Routing Eval (needs_review flag accuracy)
            "needs_review_match": gt.get("needs_review") == pred.get("needs_review"),
            "false_positive_review": False,
            "false_negative_review": False,
        }

        # Check HITL False Positives / Negatives specifically
        gt_review = gt.get("needs_review", True)
        pred_review = pred.get("needs_review", True)
        
        if not gt_review and pred_review:
            metrics["false_positive_review"] = True  # Good doc sent to manual review unnecessarily
        elif gt_review and not pred_review:
            metrics["false_negative_review"] = True  # Flawed doc passed into automation (critical bug!)

        # Item-level matching evaluation (Entity Resolution & Extraction)
        gt_items = gt.get("items", [])
        pred_items = pred.get("items", [])
        
        metrics["item_count_match"] = len(gt_items) == len(pred_items)
        
        matched_items_correct = 0
        for g_item, p_item in zip(gt_items, pred_items):
            id_match = g_item.get("item_number") == p_item.get("item_number")
            qty_match = g_item.get("quantity") == p_item.get("quantity")
            if id_match and qty_match:
                matched_items_correct += 1

        metrics["item_accuracy"] = (
            matched_items_correct / len(gt_items) if gt_items else (1.0 if not pred_items else 0.0)
        )

        return metrics

    def run_evaluation(self) -> None:
        gt_files = list(self.gt_dir.glob("*.json"))
        if not gt_files:
            print(f"❌ No ground truth files found in {self.gt_dir}")
            return

        total_docs = len(gt_files)
        aggregated_metrics = {
            "doc_number_accuracy": 0,
            "customer_id_accuracy": 0,
            "total_amount_accuracy": 0,
            "needs_review_accuracy": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "item_accuracy_sum": 0.0,
        }

        print(f"🚀 Starting evaluation on {total_docs} documents...\n")

        for gt_path in gt_files:
            pred_path = self.pred_dir / gt_path.name
            if not pred_path.exists():
                print(f"⚠️ Prediction file missing for {gt_path.name}, skipping.")
                total_docs -= 1
                continue

            gt_data = self.load_json(gt_path)
            pred_data = self.load_json(pred_path)

            m = self.evaluate_document(gt_data, pred_data)

            if m["document_number_match"]: aggregated_metrics["doc_number_accuracy"] += 1
            if m["customer_id_match"]: aggregated_metrics["customer_id_accuracy"] += 1
            if m["total_amount_match"]: aggregated_metrics["total_amount_accuracy"] += 1
            if m["needs_review_match"]: aggregated_metrics["needs_review_accuracy"] += 1
            if m["false_positive_review"]: aggregated_metrics["false_positives"] += 1
            if m["false_negative_review"]: aggregated_metrics["false_negatives"] += 1
            aggregated_metrics["item_accuracy_sum"] += m["item_accuracy"]

        # Print Summary Report
        print("📊 === EVALUATION REPORT ===")
        print(f"Evaluated Documents: {total_docs}")
        print(f" - Document Number Precision: {aggregated_metrics['doc_number_accuracy'] / total_docs * 100:.1f}%")
        print(f" - Customer ID Matching (ER): {aggregated_metrics['customer_id_accuracy'] / total_docs * 100:.1f}%")
        print(f" - Total Amount Accuracy: {aggregated_metrics['total_amount_accuracy'] / total_docs * 100:.1f}%")
        print(f" - Line Items Average Accuracy: {aggregated_metrics['item_accuracy_sum'] / total_docs * 100:.1f}%")
        print(f" - HITL Routing Accuracy (needs_review): {aggregated_metrics['needs_review_accuracy'] / total_docs * 100:.1f}%")
        print(f"   🚨 False Positives (Over-review): {aggregated_metrics['false_positives']}")
        print(f"   🔥 False Negatives (Missed bugs - CRITICAL): {aggregated_metrics['false_negatives']}")


if __name__ == "__main__":
    evaluator = PipelineEvaluator(
        gt_dir="evals/ground_truth",
        pred_dir="data/output"
    )
    evaluator.run_evaluation()