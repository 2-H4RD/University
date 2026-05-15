from typing import List, Tuple
from preprocessing import LabeledAlignment


def compute_precision(reference: List[LabeledAlignment], predicted: List[List[Tuple[int, int]]]) -> Tuple[int, int]:
    intersection = 0
    total_predicted = 0
    for ref, pred in zip(reference, predicted):
        pred_set = set(pred)
        possible_set = set(ref.possible) | set(ref.sure)
        intersection += len(pred_set & possible_set)
        total_predicted += len(pred_set)
    return intersection, total_predicted


def compute_recall(reference: List[LabeledAlignment], predicted: List[List[Tuple[int, int]]]) -> Tuple[int, int]:
    intersection = 0
    total_sure = 0
    for ref, pred in zip(reference, predicted):
        pred_set = set(pred)
        sure_set = set(ref.sure)
        intersection += len(pred_set & sure_set)
        total_sure += len(sure_set)
    return intersection, total_sure


def compute_aer(reference: List[LabeledAlignment], predicted: List[List[Tuple[int, int]]]) -> float:
    prec_num, total_pred = compute_precision(reference, predicted)
    rec_num, total_sure = compute_recall(reference, predicted)
    denom = total_pred + total_sure
    if denom == 0:
        return 0.0
    return 1.0 - (prec_num + rec_num) / denom
